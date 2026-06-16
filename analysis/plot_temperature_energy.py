#!/usr/bin/env python3
"""
plot_temperature_energy.py  --  Phase 6 production temperature/energy plots.

Reads the production logs and plots mobile temperature and total energy vs time
for each model:
    figures/phase6_temperature_energy_model_a.png
    figures/phase6_temperature_energy_model_b.png

Visualizes thermostat/energy behavior only. Computes NO diffusion and NO MSD.
If a log cannot be parsed, it FAILS CLEARLY (non-zero exit) -- never fabricates.

Usage:
    python analysis/plot_temperature_energy.py
"""

import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

JOBS = [
    ("logs/model_a_production.log", "Model A (pristine)",
     "figures/phase6_temperature_energy_model_a.png"),
    ("logs/model_b_production.log", "Model B (single-vacancy)",
     "figures/phase6_temperature_energy_model_b.png"),
]


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
    low = [h.lower() for h in header]
    if name.lower() not in low:
        return None
    i = low.index(name.lower())
    return [r[i] for r in rows]


def detect_dt_fs(text, log_path):
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


def make_plot(log_path, title, out_path):
    if not os.path.isfile(log_path):
        sys.exit(f"ERROR: log not found: {log_path} (run the production first)")
    text = open(log_path, errors="replace").read()
    header, rows = parse_last_thermo(text.splitlines())
    if not header or not rows:
        sys.exit(f"ERROR: could not parse a thermo table in {log_path} "
                 f"(refusing to fabricate data)")

    step = col(header, rows, "Step")
    temp = col(header, rows, "c_ctemp") or col(header, rows, "Temp")
    etot = col(header, rows, "TotEng") or col(header, rows, "Etotal")
    if step is None or temp is None or etot is None:
        sys.exit(f"ERROR: {log_path} missing Step/temperature/energy columns "
                 f"(found {header}); refusing to fabricate.")

    dt = detect_dt_fs(text, log_path)
    x = [s * dt / 1000.0 for s in step] if dt else step
    xlabel = "time (ps)" if dt else "step"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(x, temp, lw=1)
    ax1.set_ylabel("mobile T (K)")
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f"{title} — production temperature")
    ax2.plot(x, etot, lw=1, color="tab:red")
    ax2.set_ylabel("total energy (kcal/mol)")
    ax2.set_xlabel(xlabel)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("total energy")
    fig.tight_layout()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved {out_path}  ({len(rows)} thermo points, "
          f"{'ps' if dt else 'step'} axis)")


def main():
    for log_path, title, out_path in JOBS:
        make_plot(log_path, title, out_path)
    print("Done. (Temperature/energy only — no MSD, no diffusion.)")


if __name__ == "__main__":
    main()
