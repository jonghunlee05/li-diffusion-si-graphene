#!/usr/bin/env python3
"""
check_outputs.py  —  Phase 1 toolchain validation helper.

Checks whether the expected LAMMPS outputs exist after running the
Lennard-Jones test:
  1. a log file       (default name: log.lammps)
  2. a dump trajectory (any file matching *.lammpstrj, *.dump, or dump.*)

It prints a clear PASS/MISSING report and exits with status 0 only if both
are found, so it can be used in scripts or CI checks.

Usage:
    python analysis/check_outputs.py [--dir DIR] [--log LOGNAME]

Examples:
    python analysis/check_outputs.py --dir lammps_inputs
    python analysis/check_outputs.py --dir . --log log.lammps
"""

import argparse
import glob
import os
import sys


# Glob patterns that commonly identify a LAMMPS dump/trajectory file.
TRAJECTORY_PATTERNS = ["*.lammpstrj", "*.dump", "dump.*", "*.xyz"]


def find_log(directory, log_name):
    """Return the path to the log file if it exists, else None."""
    candidate = os.path.join(directory, log_name)
    return candidate if os.path.isfile(candidate) else None


def find_trajectories(directory):
    """Return a sorted list of files in `directory` that look like trajectories."""
    found = []
    for pattern in TRAJECTORY_PATTERNS:
        found.extend(glob.glob(os.path.join(directory, pattern)))
    # Deduplicate (a file could match more than one pattern) and sort.
    return sorted(set(found))


def is_nonempty(path):
    """True if the file exists and has size > 0 bytes."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


def main():
    parser = argparse.ArgumentParser(
        description="Check that LAMMPS produced a log and a trajectory."
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory to search for outputs (default: current directory).",
    )
    parser.add_argument(
        "--log",
        default="log.lammps",
        help="Expected log file name (default: log.lammps).",
    )
    args = parser.parse_args()

    directory = args.dir
    print(f"Checking for LAMMPS outputs in: {os.path.abspath(directory)}\n")

    all_ok = True

    # ---- 1. Log file -------------------------------------------------
    log_path = find_log(directory, args.log)
    if log_path and is_nonempty(log_path):
        print(f"[PASS]    log file        : {log_path}")
    elif log_path:
        print(f"[EMPTY]   log file        : {log_path} (exists but is empty)")
        all_ok = False
    else:
        print(f"[MISSING] log file        : {os.path.join(directory, args.log)}")
        all_ok = False

    # ---- 2. Trajectory file -----------------------------------------
    trajectories = [t for t in find_trajectories(directory) if is_nonempty(t)]
    if trajectories:
        print(f"[PASS]    trajectory file : {trajectories[0]}")
        for extra in trajectories[1:]:
            print(f"          (also found)    : {extra}")
    else:
        print(
            "[MISSING] trajectory file : none found matching "
            + ", ".join(TRAJECTORY_PATTERNS)
        )
        all_ok = False

    # ---- Summary -----------------------------------------------------
    print()
    if all_ok:
        print("RESULT: PASS — both log and trajectory found. Phase 1 outputs look good.")
        sys.exit(0)
    else:
        print("RESULT: FAIL — one or more expected outputs are missing.")
        print("Hint: run the test first, e.g.  (cd lammps_inputs && lmp -in in.lj_test)")
        sys.exit(1)


if __name__ == "__main__":
    main()
