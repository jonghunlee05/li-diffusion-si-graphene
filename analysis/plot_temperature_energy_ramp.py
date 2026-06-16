#!/usr/bin/env python3
"""
plot_temperature_energy_ramp.py  --  Phase 6 staged-ramp temperature/energy plots.

Companion to plot_temperature_energy.py. That script plots a single production
log; this one plots the STAGED RAMP (in.production_ramp): the four per-stage logs
    logs/model_{a,b}_ramp_{300,600,900,1200}K.log
concatenated in temperature order into one continuous time axis per model:
    figures/phase6_temperature_energy_model_a_ramp.png
    figures/phase6_temperature_energy_model_b_ramp.png

Mobile temperature should step 300 -> 600 -> 900 -> 1200 K across the four stages;
total energy should rise but stay finite/bounded. Visualization only -- NO MSD, NO
diffusion. Reuses the parser from plot_temperature_energy.py. If a stage log cannot
be parsed it FAILS CLEARLY (non-zero exit) -- never fabricates.

Usage:
    python analysis/plot_temperature_energy_ramp.py
"""

import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

# reuse the validated parsing helpers from the sibling script
from plot_temperature_energy import parse_last_thermo, col, detect_dt_fs  # noqa: E402

RAMP_INPUT = "lammps_inputs/in.production_ramp"   # all stages share this timestep
STAGES = [300, 600, 900, 1200]   # K, in heat-up order


def ramp_dt_fs():
    """Read the validated DT (fs) from the shared ramp input; exit if absent."""
    if not os.path.isfile(RAMP_INPUT):
        sys.exit(f"ERROR: ramp input not found: {RAMP_INPUT}")
    m = re.search(r"variable\s+DT\s+equal\s+([0-9.eE+-]+)", open(RAMP_INPUT).read())
    if not m:
        sys.exit(f"ERROR: could not find 'variable DT equal' in {RAMP_INPUT}.")
    return float(m.group(1))
MODELS = [
    ("model_a", "Model A (pristine)",
     "figures/phase6_temperature_energy_model_a_ramp.png"),
    ("model_b", "Model B (single-vacancy)",
     "figures/phase6_temperature_energy_model_b_ramp.png"),
]


def load_stage(model, tstage):
    """Return (time_ps, temp, etot) for one ramp stage log, or exit on failure."""
    log_path = f"logs/{model}_ramp_{tstage}K.log"
    if not os.path.isfile(log_path):
        sys.exit(f"ERROR: ramp log not found: {log_path} (run that stage first)")
    text = open(log_path, errors="replace").read()
    header, rows = parse_last_thermo(text.splitlines())
    if not header or not rows:
        sys.exit(f"ERROR: could not parse a thermo table in {log_path} "
                 f"(refusing to fabricate data)")
    step = col(header, rows, "Step")
    temp = col(header, rows, "c_ctemp") or col(header, rows, "Temp")
    etot = col(header, rows, "TotEng") or col(header, rows, "Etotal")
    if step is None or temp is None or etot is None:
        sys.exit(f"ERROR: {log_path} missing Step/temp/energy columns "
                 f"(found {header}); refusing to fabricate.")
    dt = detect_dt_fs(text, log_path) or ramp_dt_fs()
    # per-stage time in ps, relative to the stage start
    t = [s * dt / 1000.0 for s in step]
    return t, temp, etot


def make_plot(model, title, out_path):
    xs, temps, etots, bounds = [], [], [], []
    offset = 0.0
    for tstage in STAGES:
        t, temp, etot = load_stage(model, tstage)
        xs += [offset + ti for ti in t]
        temps += temp
        etots += etot
        offset += t[-1]          # continuous time across stages
        bounds.append(offset)    # stage boundary (end of this stage)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax1.plot(xs, temps, lw=0.8)
    ax1.set_ylabel("mobile T (K)")
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f"{title} — staged-ramp temperature (300→600→900→1200 K)")
    for T, b in zip(STAGES, [0.0] + bounds[:-1]):
        ax1.axhline(T, color="gray", ls=":", lw=0.7, alpha=0.6)
    ax2.plot(xs, etots, lw=0.8, color="tab:red")
    ax2.set_ylabel("total energy (kcal/mol)")
    ax2.set_xlabel("time (ps)")
    ax2.grid(True, alpha=0.3)
    ax2.set_title("total energy")
    # mark stage boundaries on both panels
    for b in bounds[:-1]:
        for ax in (ax1, ax2):
            ax.axvline(b, color="black", ls="--", lw=0.6, alpha=0.4)
    fig.tight_layout()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved {out_path}  ({len(xs)} thermo points across "
          f"{len(STAGES)} stages, ps axis)")


def main():
    for model, title, out_path in MODELS:
        make_plot(model, title, out_path)
    print("Done. (Staged-ramp temperature/energy only — no MSD, no diffusion.)")


if __name__ == "__main__":
    main()
