#!/usr/bin/env python3
"""
msd_temperature_sweep.py  --  Phase 7 extension: Li MSD/diffusion vs temperature.

Runs the SAME Li-MSD + diffusion analysis as the single-temperature Phase 7 tools,
but across all four ramp stages (300/600/900/1200 K) for both models, so apparent
Li mobility can be compared **vs temperature** (and Model B vs Model A at each T).

It reuses the validated core (read_dump, compute_msd from compute_li_msd.py;
fit/units from msd_utils.py) so the method is byte-identical to the 1200 K run.

Two stages:
  --stage diagnose : compute per-(model,T) MSD CSVs and print local-slope / z-plateau
                     diagnostics so fit windows can be chosen FROM THE DATA (rule #4).
  --stage fit      : using analysis/fit_windows_by_temperature.json, fit each
                     (model,T,component), write the combined table + figures.

Outputs (stage fit):
  analysis/results/by_temperature/model_{a,b}_{T}K_li_msd.csv
  analysis/results/diffusion_vs_temperature.csv / .json
  figures/phase7_msd_xy_by_temperature_model_{a,b}.png
  figures/phase7_apparent_D_xy_vs_temperature.png

Phase 7 = analysis only. The apparent D's remain comparative-only (not physical);
each fit still reports R², linearity ratio, and a regime label. See
notes/phase7_msd_diffusion_analysis.md.

Usage:
    python analysis/msd_temperature_sweep.py --stage diagnose
    python analysis/msd_temperature_sweep.py --stage fit
"""

import argparse
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

from compute_li_msd import process as compute_process
from msd_utils import (load_msd_csv, linear_fit, diffusion_from_slope,
                       MSD_COLUMN, DIM_DIVISOR)

TEMPS = [300, 600, 900, 1200]
MODELS = ["model_a", "model_b"]
COMPONENTS = ["3d", "xy", "z"]
DT_FS = 0.25
BYTEMP = "analysis/results/by_temperature"
WINDOWS = "analysis/fit_windows_by_temperature.json"
FIGS = "figures"


def traj_path(model, T):
    return f"trajectories/{model}_ramp_{T}K.lammpstrj"


def csv_path(model, T):
    return os.path.join(BYTEMP, f"{model}_{T}K_li_msd.csv")


def compute_all():
    os.makedirs(BYTEMP, exist_ok=True)
    for T in TEMPS:
        for model in MODELS:
            compute_process(model, traj_path(model, T), DT_FS, BYTEMP, label=f"{T}K")


def diagnose():
    compute_all()
    print("\n================ REGIME DIAGNOSTICS (choose fit windows from this) ===========")
    for model in MODELS:
        for T in TEMPS:
            d = load_msd_csv(csv_path(model, T))
            t, xy, z = d["time_ps"], d["msd_xy_A2"], d["msd_z_A2"]
            slopes = []
            for lo in range(0, 10, 2):                 # 2-ps windows
                sel = (t >= lo) & (t < lo + 2)
                if sel.sum() >= 3:
                    slopes.append((lo, float(np.polyfit(t[sel], xy[sel], 1)[0])))
            zp = z[t >= 0.5]
            sl = "  ".join(f"{lo}-{lo+2}:{s:7.1f}" for lo, s in slopes)
            print(f"  {model} {T:4d}K | xy slope/2ps (A^2/ps): {sl} | "
                  f"z plateau mean={zp.mean():.2f} (max {zp.max():.2f}) A^2")
    print("\nGuide: rising slopes -> super-diffusive; flat slopes -> linear; "
          "small flat z -> confined. Put chosen windows in", WINDOWS)


def fit_and_plot():
    if not os.path.isfile(WINDOWS):
        raise SystemExit(f"ERROR: {WINDOWS} not found. Run --stage diagnose, then "
                         f"create it with per-(model,T) windows.")
    cfg = json.load(open(WINDOWS))
    compute_all()

    rows = []
    summary = {"unit_conversion": "D[cm^2/s] = D[A^2/ps]*1e-4",
               "dimension_divisors": DIM_DIVISOR, "window_source": WINDOWS, "data": {}}
    for model in MODELS:
        summary["data"][model] = {}
        for T in TEMPS:
            d = load_msd_csv(csv_path(model, T))
            t = d["time_ps"]
            w = cfg[model][str(T)]
            start, end = float(w["fit_start_ps"]), float(w["fit_end_ps"])
            mask = (t >= start) & (t <= end)
            npts = int(mask.sum())
            summary["data"][model][str(T)] = {"fit_start_ps": start, "fit_end_ps": end,
                                               "n_points": npts, "components": {}}
            for comp in COMPONENTS:
                y = d[MSD_COLUMN[comp]]
                tw, yw = t[mask], y[mask]
                slope, intercept, r2 = linear_fit(tw, yw)
                d_a2ps, d_cm2s = diffusion_from_slope(slope, comp)
                mid = len(tw) // 2
                ratio = (float(np.polyfit(tw[mid:], yw[mid:], 1)[0] /
                               np.polyfit(tw[:mid], yw[:mid], 1)[0])
                         if mid >= 2 else float("nan"))
                regime = ("confined plateau" if comp == "z" and abs(d_cm2s) < 5e-6
                          else "super-diffusive" if ratio > 1.5
                          else "sub-diffusive" if ratio < 0.5 else "~linear")
                rows.append([model, T, comp, start, end, npts, f"{slope:.4f}",
                             f"{d_cm2s:.6e}", f"{r2:.4f}", f"{ratio:.3f}", regime])
                summary["data"][model][str(T)]["components"][comp] = {
                    "slope_A2_per_ps": slope, "D_cm2_per_s": d_cm2s, "r2": r2,
                    "linearity_ratio": ratio, "regime": regime}

    os.makedirs("analysis/results", exist_ok=True)
    csv_out = "analysis/results/diffusion_vs_temperature.csv"
    with open(csv_out, "w") as fh:
        fh.write("# Phase 7 sweep: apparent Li D vs temperature (comparative-only, "
                 "not physical). D=slope/(2*dim); D[cm^2/s]=D[A^2/ps]*1e-4.\n")
        fh.write("model,temp_K,component,fit_start_ps,fit_end_ps,n_points,"
                 "slope_A2_per_ps,D_cm2_per_s,r2,linearity_ratio,regime\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    json.dump(summary, open("analysis/results/diffusion_vs_temperature.json", "w"), indent=2)
    print(f"Saved {csv_out}")
    print("Saved analysis/results/diffusion_vs_temperature.json")

    # ---- plots ----
    os.makedirs(FIGS, exist_ok=True)
    # (1) xy MSD curves at all T, one figure per model
    for model in MODELS:
        fig, ax = plt.subplots(figsize=(7, 5))
        for T in TEMPS:
            d = load_msd_csv(csv_path(model, T))
            ax.plot(d["time_ps"], d["msd_xy_A2"], lw=1.2, label=f"{T} K")
        ax.set_xlabel("lag time (ps)"); ax.set_ylabel("x-y MSD (Å²)")
        ax.set_title(f"Phase 7 sweep — {model}: in-plane Li MSD vs temperature\n"
                     f"(4 Li, 10 ps/stage; apparent/comparative only)")
        ax.grid(True, alpha=0.3); ax.legend()
        fig.tight_layout()
        out = os.path.join(FIGS, f"phase7_msd_xy_by_temperature_{model}.png")
        fig.savefig(out, dpi=150); plt.close(fig); print(f"Saved {out}")

    # (2) apparent xy-D vs T, both models
    fig, ax = plt.subplots(figsize=(7, 5))
    for model in MODELS:
        Ds = []
        for T in TEMPS:
            c = summary["data"][model][str(T)]["components"]["xy"]
            Ds.append(c["D_cm2_per_s"])
        ax.plot(TEMPS, Ds, "o-", label=model)
    ax.set_xlabel("temperature (K)"); ax.set_ylabel("apparent x-y D (cm²/s)")
    ax.set_title("Phase 7 sweep — apparent in-plane Li D vs temperature\n"
                 "(comparative-only; super-diffusive at high T — NOT physical D)")
    ax.grid(True, alpha=0.3); ax.legend()
    fig.tight_layout()
    out = os.path.join(FIGS, "phase7_apparent_D_xy_vs_temperature.png")
    fig.savefig(out, dpi=150); plt.close(fig); print(f"Saved {out}")


def main():
    ap = argparse.ArgumentParser(description="Li MSD/diffusion vs temperature sweep (Phase 7).")
    ap.add_argument("--stage", choices=["diagnose", "fit"], required=True)
    args = ap.parse_args()
    if args.stage == "diagnose":
        diagnose()
    else:
        fit_and_plot()


if __name__ == "__main__":
    main()
