#!/usr/bin/env python3
"""
plot_lammps_log.py  —  Phase 1 toolchain validation helper.

Reads a LAMMPS log file (default: 'log.lammps'), extracts the thermodynamic
table, and plots temperature and energy vs. timestep *if those columns are
present*. The figure is saved as a PNG in the figures/ directory.

This is intentionally simple and heavily commented. It only needs to work for
the trivial Lennard-Jones test run by lammps_inputs/in.lj_test.

Usage:
    python analysis/plot_lammps_log.py [path/to/log.lammps] [-o figures/log_plot.png]

Examples:
    python analysis/plot_lammps_log.py
    python analysis/plot_lammps_log.py lammps_inputs/log.lammps
    python analysis/plot_lammps_log.py lammps_inputs/log.lammps -o figures/lj_test.png
"""

import argparse
import os
import sys

import pandas as pd
import matplotlib

# Use a non-interactive backend so the script works over SSH / headless too.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (import after backend selection)


def parse_lammps_log(log_path):
    """
    Parse the thermo table(s) out of a LAMMPS log file.

    LAMMPS prints thermo output as a header line of column names followed by
    rows of numbers, bracketed by lines like:
        Per MPI rank memory allocation ...
        Step  Temp  ...
        0     1.44  ...
        ...
        Loop time of ...

    Strategy (deliberately simple):
      - Find a line that starts with 'Step' (the thermo header).
      - Read the numeric rows that follow until a non-numeric line appears.
      - Return a pandas DataFrame. If multiple thermo blocks exist, the first
        complete one is used (enough for the Phase 1 test).
    """
    with open(log_path, "r") as fh:
        lines = fh.readlines()

    header = None
    rows = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        # Detect the start of a thermo table: a header beginning with 'Step'.
        if stripped.startswith("Step"):
            header = stripped.split()
            rows = []
            in_table = True
            continue

        if in_table:
            parts = stripped.split()
            # A data row has the same number of columns as the header and every
            # field parses as a float. Anything else ends the table.
            if len(parts) == len(header):
                try:
                    rows.append([float(p) for p in parts])
                    continue
                except ValueError:
                    in_table = False
            else:
                in_table = False

            # If we just finished a non-empty table, stop — first block is enough.
            if rows:
                break

    if not header or not rows:
        return None

    return pd.DataFrame(rows, columns=header)


def find_column(df, candidates):
    """
    Return the first column name in `df` that matches one of `candidates`
    (case-insensitive). Returns None if none are present.

    LAMMPS column names depend on thermo_style; we accept common aliases.
    """
    lower_map = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def main():
    parser = argparse.ArgumentParser(description="Plot temperature/energy from a LAMMPS log.")
    parser.add_argument(
        "log",
        nargs="?",
        default="log.lammps",
        help="Path to the LAMMPS log file (default: log.lammps).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PNG path (default: figures/<logname>_plot.png).",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.log):
        sys.exit(f"ERROR: log file not found: {args.log}")

    df = parse_lammps_log(args.log)
    if df is None or df.empty:
        sys.exit(f"ERROR: could not find a thermo table in {args.log}")

    # Locate the x-axis (Step) and the columns we want to plot.
    step_col = find_column(df, ["Step"])
    temp_col = find_column(df, ["Temp", "Temperature"])
    # Accept several energy column names; total energy is preferred.
    energy_col = find_column(df, ["TotEng", "Etotal", "PotEng", "E_pair", "TotEnergy"])

    if step_col is None:
        # Fall back to a simple integer index if there is no Step column.
        x = range(len(df))
        x_label = "row index"
    else:
        x = df[step_col]
        x_label = step_col

    if temp_col is None and energy_col is None:
        sys.exit(
            "ERROR: log has no temperature or energy columns to plot "
            f"(columns found: {list(df.columns)})"
        )

    # Decide how many subplots we need (one per available quantity).
    panels = [c for c in (temp_col, energy_col) if c is not None]
    fig, axes = plt.subplots(len(panels), 1, figsize=(8, 3 * len(panels)), sharex=True)
    if len(panels) == 1:
        axes = [axes]  # make iterable when there is a single subplot

    for ax, col in zip(axes, panels):
        ax.plot(x, df[col], marker="o", markersize=3, linewidth=1)
        ax.set_ylabel(col)
        ax.grid(True, alpha=0.3)
        ax.set_title(f"{col} vs. {x_label}")
    axes[-1].set_xlabel(x_label)
    fig.suptitle(f"LAMMPS log: {os.path.basename(args.log)}")
    fig.tight_layout()

    # Resolve the output path (default into the figures/ directory).
    if args.output:
        out_path = args.output
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        figures_dir = os.path.join(repo_root, "figures")
        os.makedirs(figures_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.log))[0]
        out_path = os.path.join(figures_dir, f"{base}_plot.png")

    fig.savefig(out_path, dpi=150)
    print(f"Saved plot to: {out_path}")
    print(f"Columns plotted: {', '.join(panels)}")


if __name__ == "__main__":
    main()
