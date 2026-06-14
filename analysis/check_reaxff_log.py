#!/usr/bin/env python3
"""
check_reaxff_log.py  --  Phase 3 ReaxFF smoke-test log inspector.

Reads a LAMMPS log from the ReaxFF smoke test and checks the things that matter
for force-field VALIDATION (not science):
  - did the run complete? (look for 'Total wall time')
  - any NaN / inf values? (charges or energies blowing up)
  - QEq warnings (charge equilibration not converging)
  - 'dangerous' / other LAMMPS warnings
  - final temperature
  - energy behavior (first vs last total energy), if available

Prints a PASS/FAIL summary and exits non-zero on failure so it can gate a
workflow. It does NOT compute any physical property.

Usage:
    python analysis/check_reaxff_log.py
    python analysis/check_reaxff_log.py logs/reaxff_smoke_test.log
"""

import argparse
import math
import os
import re
import sys


def parse_thermo(lines):
    """
    Extract the LAST thermo table in the log (a run may have several, e.g. one
    for minimization and one for the NVT dynamics). Returns (header, rows) for
    the final table so 'final temperature' reflects the dynamics run, not the
    zero-velocity minimization. Empty if none found.
    """
    header = None
    rows = []
    cur_header = None
    cur_rows = []
    in_table = False
    for line in lines:
        s = line.strip()
        if s.startswith("Step"):
            # starting a new table; remember the previous completed one
            if cur_header and cur_rows:
                header, rows = cur_header, cur_rows
            cur_header = s.split()
            cur_rows = []
            in_table = True
            continue
        if in_table:
            parts = s.split()
            if len(parts) == len(cur_header):
                try:
                    cur_rows.append([float(p) for p in parts])
                    continue
                except ValueError:
                    in_table = False
            else:
                in_table = False
    # the last table seen wins if it has data
    if cur_header and cur_rows:
        header, rows = cur_header, cur_rows
    return header, rows


def col(header, rows, name):
    """Return the list of values for column `name` (case-insensitive), or None."""
    if not header:
        return None
    lower = {h.lower(): i for i, h in enumerate(header)}
    if name.lower() not in lower:
        return None
    idx = lower[name.lower()]
    return [r[idx] for r in rows]


def main():
    parser = argparse.ArgumentParser(description="Inspect a ReaxFF smoke-test LAMMPS log.")
    parser.add_argument("log", nargs="?", default="logs/reaxff_smoke_test.log",
                        help="path to the log (default: logs/reaxff_smoke_test.log)")
    args = parser.parse_args()

    if not os.path.isfile(args.log):
        print(f"[MISSING] log file not found: {args.log}")
        print("Run the smoke test first:  lmp -in lammps_inputs/in.reaxff_smoke_test")
        sys.exit(2)

    with open(args.log, "r", errors="replace") as fh:
        text = fh.read()
    lines = text.splitlines()
    low = text.lower()

    checks = []  # (ok, label, detail)

    # 1. Completion.
    completed = "total wall time" in low
    checks.append((completed, "run completed",
                   "found 'Total wall time'" if completed
                   else "no 'Total wall time' -> run did not finish / crashed"))

    # 2. NaN / inf.
    has_nan = bool(re.search(r"\b(nan|-?inf)\b", low))
    checks.append((not has_nan, "no NaN/Inf",
                   "no NaN/Inf tokens" if not has_nan
                   else "found NaN/Inf -> charges or energies diverged"))

    # 3. QEq convergence warnings.
    qeq_warn = "qeq" in low and ("not converge" in low or "maxiter" in low
                                 or "failed to converge" in low)
    checks.append((not qeq_warn, "QEq converged",
                   "no QEq convergence warnings" if not qeq_warn
                   else "QEq convergence warning present"))

    # 4. Other LAMMPS warnings (report, not necessarily fatal).
    warnings = [ln.strip() for ln in lines if ln.lower().startswith("warning")]
    dangerous = "dangerous builds" in low and not re.search(
        r"dangerous builds\s*=\s*0", low)
    checks.append((not dangerous, "neighbor list ok",
                   "no dangerous neighbor builds" if not dangerous
                   else "dangerous neighbor builds > 0"))

    # 5. Thermo-derived info (temperature, energy behavior).
    header, rows = parse_thermo(lines)
    temp = col(header, rows, "Temp")
    etot = col(header, rows, "TotEng") or col(header, rows, "Etotal")

    final_temp = temp[-1] if temp else None
    energy_ok = True
    energy_detail = "no energy column found"
    if etot:
        e0, e1 = etot[0], etot[-1]
        energy_finite = all(math.isfinite(e) for e in etot)
        energy_ok = energy_finite
        energy_detail = (f"TotEng {e0:.3f} -> {e1:.3f} "
                         f"({'finite' if energy_finite else 'NON-FINITE'})")
    checks.append((energy_ok, "energy finite", energy_detail))

    # --- Report -------------------------------------------------------
    print(f"ReaxFF smoke-test log : {args.log}\n")
    all_ok = True
    for ok, label, detail in checks:
        tag = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{tag}] {label:18s}: {detail}")

    print()
    if final_temp is not None:
        print(f"  final temperature : {final_temp:.2f} K")
    if warnings:
        print(f"  LAMMPS warnings   : {len(warnings)} (review below)")
        for w in warnings[:10]:
            print(f"    - {w}")

    print()
    if all_ok:
        print("RESULT: PASS -- ReaxFF/QEq smoke test looks healthy.")
        sys.exit(0)
    else:
        print("RESULT: FAIL -- see failed checks above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
