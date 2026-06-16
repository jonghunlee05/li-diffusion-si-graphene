#!/usr/bin/env python3
"""
check_production_logs.py  --  Phase 6 production-log inspector.

Inspects the Model A and Model B production logs and checks (stability only --
NOT diffusion):
  - normal completion ('Total wall time')
  - NaN / Inf
  - QEq convergence warnings
  - dangerous neighbor builds
  - temperature blow-up (mobile temperature)
  - energy divergence (non-finite)
  - whether BOTH runs used the same timestep and target temperature (if detectable)

Usage:
    python analysis/check_production_logs.py
    python analysis/check_production_logs.py logs/model_a_production.log
"""

import argparse
import math
import os
import re
import sys

DEFAULT_LOGS = ["logs/model_a_production.log", "logs/model_b_production.log"]
TEMP_BLOWUP_K = 5000.0


def parse_last_thermo(lines):
    header, rows, cur_h, cur_r, intab = None, [], None, [], False
    for line in lines:
        s = line.strip()
        if s.startswith("Step"):
            if cur_h and cur_r:
                header, rows = cur_h, cur_r
            cur_h, cur_r, intab = s.split(), [], True
            continue
        if intab:
            p = s.split()
            if len(p) == len(cur_h):
                try:
                    cur_r.append([float(x) for x in p]); continue
                except ValueError:
                    intab = False
            else:
                intab = False
    if cur_h and cur_r:
        header, rows = cur_h, cur_r
    return header, rows


def col(header, rows, name):
    if not header or name.lower() not in [h.lower() for h in header]:
        return None
    i = [h.lower() for h in header].index(name.lower())
    return [r[i] for r in rows]


def detect_timestep(text, log_path):
    """fs/step. LAMMPS prints it to screen (not the log) -> fall back to input."""
    m = re.search(r"Time step\s*:\s*([0-9.eE+-]+)", text)
    if m:
        return float(m.group(1))
    inp = log_path.replace("logs/", "lammps_inputs/in.").replace("_production.log",
                                                                 "_production")
    if os.path.isfile(inp):
        t = open(inp).read()
        m2 = (re.search(r"variable\s+DT\s+equal\s+([0-9.eE+-]+)", t)
              or re.search(r"^\s*timestep\s+([0-9.eE+-]+)", t, re.M))
        if m2:
            return float(m2.group(1))
    return None


def check_one(path):
    if not os.path.isfile(path):
        return None, [(False, "log present", f"missing: {path}")], {}
    text = open(path, errors="replace").read()
    low = text.lower()
    lines = text.splitlines()
    checks = []

    completed = "total wall time" in low
    checks.append((completed, "completed",
                   "found 'Total wall time'" if completed else "no completion marker"))
    has_nan = bool(re.search(r"\b(nan|-?inf)\b", low))
    checks.append((not has_nan, "no NaN/Inf", "clean" if not has_nan else "NaN/Inf present"))
    qeq_warn = "qeq" in low and ("not converge" in low or "failed to converge" in low)
    checks.append((not qeq_warn, "QEq ok",
                   "no convergence warnings" if not qeq_warn else "QEq warning"))
    dangerous = bool(re.search(r"dangerous builds\s*=\s*[1-9]", low))
    checks.append((not dangerous, "neighbors ok",
                   "no dangerous builds" if not dangerous else "dangerous builds > 0"))

    header, rows = parse_last_thermo(lines)
    temp = col(header, rows, "c_ctemp") or col(header, rows, "Temp")
    etot = col(header, rows, "TotEng") or col(header, rows, "Etotal")
    info = {"timestep": detect_timestep(text, path)}

    tmax = max((abs(t) for t in temp), default=None) if temp else None
    if temp:
        half = temp[len(temp) // 2:]
        info["temp_mean_2ndhalf"] = sum(half) / len(half)
        info["final_temp"] = temp[-1]
    temp_ok = tmax is None or tmax < TEMP_BLOWUP_K
    checks.append((temp_ok, "temp bounded",
                   f"max mobile |T| {tmax:.0f} K" if tmax is not None else "no temp column"))

    if etot:
        finite = all(math.isfinite(e) for e in etot)
        info["e0"], info["e1"] = etot[0], etot[-1]
        checks.append((finite, "energy finite",
                       f"TotEng {etot[0]:.1f} -> {etot[-1]:.1f}"
                       + ("" if finite else "  NON-FINITE")))
    else:
        checks.append((True, "energy finite", "no energy column"))

    return all(c[0] for c in checks), checks, info


def main():
    ap = argparse.ArgumentParser(description="Check Phase 6 production logs.")
    ap.add_argument("logs", nargs="*", default=DEFAULT_LOGS)
    args = ap.parse_args()

    results = {}
    overall, any_found = True, False
    for path in args.logs:
        ok, checks, info = check_one(path)
        print(f"\n=== {path} ===")
        if ok is None:
            print(f"  [SKIP] {checks[0][2]}")
            continue
        any_found = True
        for c_ok, label, detail in checks:
            print(f"  [{'PASS' if c_ok else 'FAIL'}] {label:14s}: {detail}")
        if info.get("timestep") is not None:
            print(f"  timestep          : {info['timestep']} fs")
        if info.get("temp_mean_2ndhalf") is not None:
            print(f"  mobile T (2nd half): {info['temp_mean_2ndhalf']:.1f} K")
        results[path] = info
        overall = overall and ok

    if len(results) == 2:
        a, b = results.values()
        ts_same = a.get("timestep") == b.get("timestep")
        t_close = (a.get("temp_mean_2ndhalf") is not None
                   and b.get("temp_mean_2ndhalf") is not None
                   and abs(a["temp_mean_2ndhalf"] - b["temp_mean_2ndhalf"]) < 75)
        print("\n=== A vs B protocol cross-check ===")
        print(f"  [{'PASS' if ts_same else 'FAIL'}] same timestep   : "
              f"{a.get('timestep')} vs {b.get('timestep')} fs")
        print(f"  [{'PASS' if t_close else 'WARN'}] same target temp : "
              f"{a.get('temp_mean_2ndhalf', float('nan')):.0f} vs "
              f"{b.get('temp_mean_2ndhalf', float('nan')):.0f} K (mobile, 2nd half)")
        overall = overall and ts_same

    print()
    if not any_found:
        print("RESULT: no logs found. Run the production inputs first.")
        sys.exit(2)
    if overall:
        print("RESULT: PASS -- both production runs healthy and consistent.")
        sys.exit(0)
    print("RESULT: FAIL -- see failed checks above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
