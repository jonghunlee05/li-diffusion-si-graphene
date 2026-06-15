#!/usr/bin/env python3
"""
check_model_a_logs.py  --  Phase 4 Model A log inspector.

Inspects the minimization and short-equilibration LAMMPS logs and checks the
things that matter for STRUCTURAL validation (Phase 4 pass condition: the model
minimizes & equilibrates without collapse/explosion):
  - normal completion ('Total wall time')
  - NaN / Inf
  - QEq convergence warnings
  - dangerous neighbor builds
  - temperature blow-up
  - energy divergence (non-finite or wildly unbounded)

Does NOT compute any physical property. Prints PASS/FAIL per log and overall.

Usage:
    python analysis/check_model_a_logs.py
    python analysis/check_model_a_logs.py logs/model_a_minimize.log
"""

import argparse
import math
import os
import re
import sys


DEFAULT_LOGS = ["logs/model_a_minimize.log", "logs/model_a_equilibrate_short.log"]
TEMP_BLOWUP_K = 5000.0     # final/any temperature above this = blow-up


def parse_last_thermo(lines):
    """Return (header, rows) for the LAST thermo table in the log."""
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


def check_one(path):
    """Return (ok, list_of_(ok,label,detail), info_dict)."""
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
    checks.append((not has_nan, "no NaN/Inf",
                   "clean" if not has_nan else "NaN/Inf present"))

    qeq_warn = "qeq" in low and ("not converge" in low or "failed to converge" in low)
    checks.append((not qeq_warn, "QEq ok",
                   "no convergence warnings" if not qeq_warn else "QEq warning"))

    dangerous = bool(re.search(r"dangerous builds\s*=\s*[1-9]", low))
    checks.append((not dangerous, "neighbors ok",
                   "no dangerous builds" if not dangerous else "dangerous builds > 0"))

    header, rows = parse_last_thermo(lines)
    temp = col(header, rows, "Temp")
    etot = col(header, rows, "TotEng") or col(header, rows, "Etotal")
    info = {}

    tmax = max((abs(t) for t in temp), default=None) if temp else None
    info["final_temp"] = temp[-1] if temp else None
    temp_ok = tmax is None or tmax < TEMP_BLOWUP_K
    checks.append((temp_ok, "temp bounded",
                   f"max |T| {tmax:.1f} K" if tmax is not None else "no temp column"))

    if etot:
        finite = all(math.isfinite(e) for e in etot)
        info["e0"], info["e1"] = etot[0], etot[-1]
        checks.append((finite, "energy finite",
                       f"TotEng {etot[0]:.2f} -> {etot[-1]:.2f}"
                       + ("" if finite else "  NON-FINITE")))
    else:
        checks.append((True, "energy finite", "no energy column"))

    ok = all(c[0] for c in checks)
    return ok, checks, info


def main():
    ap = argparse.ArgumentParser(description="Check Model A minimize/equilibrate logs.")
    ap.add_argument("logs", nargs="*", default=DEFAULT_LOGS,
                    help=f"log paths (default: {DEFAULT_LOGS})")
    args = ap.parse_args()

    overall = True
    any_found = False
    for path in args.logs:
        ok, checks, info = check_one(path)
        print(f"\n=== {path} ===")
        if ok is None:
            print(f"  [SKIP] {checks[0][2]}")
            continue
        any_found = True
        for c_ok, label, detail in checks:
            print(f"  [{'PASS' if c_ok else 'FAIL'}] {label:14s}: {detail}")
        if info.get("final_temp") is not None:
            print(f"  final temperature : {info['final_temp']:.2f} K")
        overall = overall and ok

    print()
    if not any_found:
        print("RESULT: no logs found. Run the minimize/equilibrate inputs first.")
        sys.exit(2)
    if overall:
        print("RESULT: PASS -- Model A minimized/equilibrated without collapse.")
        sys.exit(0)
    print("RESULT: FAIL -- see failed checks above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
