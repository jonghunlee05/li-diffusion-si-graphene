#!/usr/bin/env python3
"""
fit_diffusion_coefficients.py  --  Phase 7: fit Li MSD slopes -> diffusion coefficients.

Loads the MSD CSVs (compute_li_msd.py), fits a straight line to the chosen linear
window of each MSD component, and converts the slope to a diffusion coefficient:

    3D  : D = slope / 6   (Å²/ps)         x-y : D = slope / 4         z : D = slope / 2
    D[cm²/s] = D[Å²/ps] * 1e-4            (1 Å²/ps = 1e-4 cm²/s; see msd_utils.py)

FITTING WINDOW: chosen AFTER looking at the MSD (Phase 7 rule -- not blind). Default
windows come from analysis/fit_windows.json (per model, documented there); override
on the command line with --fit-start/--fit-end (applies to BOTH models).

HONESTY: this script does NOT assume the MSD is linear. For every fit it also
reports R² and a `linearity_ratio` (late-half slope / early-half slope inside the
window: ~1 = linear; >>1 = super-diffusive; <<1 = sub-diffusive/saturating) and a
`regime` label. For this dataset the x-y/3D MSD is super-diffusive and the z MSD is
a confined plateau, so the reported D's are APPARENT and comparative-only under this
MD protocol -- not physical Fickian diffusion coefficients. That is stated in the
output, not hidden. (Phase 7: analysis only; no MD, no structure changes.)

Outputs:
    analysis/results/diffusion_coefficients.csv
    analysis/results/diffusion_summary.json

Usage:
    python analysis/fit_diffusion_coefficients.py
    python analysis/fit_diffusion_coefficients.py --fit-start 1.0 --fit-end 5.0
"""

import argparse
import json
import os

import numpy as np

from msd_utils import (load_msd_csv, linear_fit, diffusion_from_slope,
                       MSD_COLUMN, DIM_DIVISOR, ANG2_PER_PS_TO_CM2_PER_S)

RESULTS = "analysis/results"
WINDOWS_JSON = "analysis/fit_windows.json"
MODELS = ["model_a", "model_b"]
COMPONENTS = ["3d", "xy", "z"]


def classify_regime(component, t_win, y_win, slope, r2):
    """Label the fit regime honestly from the in-window curvature."""
    # split the window in half and compare local slopes
    mid = len(t_win) // 2
    if mid >= 2 and (len(t_win) - mid) >= 2:
        s_early = np.polyfit(t_win[:mid], y_win[:mid], 1)[0]
        s_late = np.polyfit(t_win[mid:], y_win[mid:], 1)[0]
        ratio = float(s_late / s_early) if abs(s_early) > 1e-9 else float("inf")
    else:
        ratio = float("nan")

    span = float(y_win.max() - y_win.min())
    mean = float(np.mean(y_win))
    # confined: tiny absolute MSD that barely grows (e.g. z plateau)
    if component == "z" and mean < 10.0 and abs(slope) * (t_win[-1] - t_win[0]) < 0.5 * mean:
        regime = "confined plateau (no diffusion; D not physically meaningful)"
    elif np.isfinite(ratio) and ratio > 1.5:
        regime = "super-diffusive (slope rising; no clear Fickian regime)"
    elif np.isfinite(ratio) and ratio < 0.5:
        regime = "sub-diffusive / saturating"
    else:
        regime = "approximately linear"
    return regime, ratio, span


def load_windows(cli_start, cli_end):
    win = {}
    if cli_start is not None and cli_end is not None:
        for m in MODELS:
            win[m] = (float(cli_start), float(cli_end))
        src = f"CLI (--fit-start {cli_start} --fit-end {cli_end}, both models)"
    elif os.path.isfile(WINDOWS_JSON):
        cfg = json.load(open(WINDOWS_JSON))
        for m in MODELS:
            win[m] = (float(cfg[m]["fit_start_ps"]), float(cfg[m]["fit_end_ps"]))
        src = WINDOWS_JSON
    else:
        for m in MODELS:
            win[m] = (1.0, 5.0)
        src = "built-in default (1.0–5.0 ps)"
    return win, src


def main():
    ap = argparse.ArgumentParser(description="Fit Li MSD -> diffusion coefficients (Phase 7).")
    ap.add_argument("--fit-start", type=float, default=None, help="window start (ps); overrides config for BOTH models")
    ap.add_argument("--fit-end", type=float, default=None, help="window end (ps); overrides config for BOTH models")
    ap.add_argument("--resultsdir", default=RESULTS)
    args = ap.parse_args()
    if (args.fit_start is None) != (args.fit_end is None):
        ap.error("provide both --fit-start and --fit-end, or neither.")

    windows, win_src = load_windows(args.fit_start, args.fit_end)
    print(f"Fitting windows from: {win_src}")

    rows = []
    summary = {"fit_window_source": win_src, "unit_conversion": "D[cm^2/s] = D[A^2/ps] * 1e-4",
               "dimension_divisors": DIM_DIVISOR, "models": {}}

    for model in MODELS:
        d = load_msd_csv(os.path.join(args.resultsdir, f"{model}_li_msd.csv"))
        t = d["time_ps"]
        start, end = windows[model]
        mask = (t >= start) & (t <= end)
        npts = int(mask.sum())
        n_li = int(d["n_li"][0]) if "n_li" in d else None
        print(f"\n=== {model}  window [{start}, {end}] ps  ({npts} points, n_li={n_li}) ===")
        summary["models"][model] = {"fit_start_ps": start, "fit_end_ps": end,
                                    "n_points": npts, "n_li": n_li, "components": {}}
        if npts < 3:
            print("  ERROR: <3 points in window; cannot fit. Reported as not-fittable.")
        for comp in COMPONENTS:
            y = d[MSD_COLUMN[comp]]
            tw, yw = t[mask], y[mask]
            if npts < 3:
                rows.append([model, comp, start, end, npts, "", "", "", "", "", "not-fittable"])
                summary["models"][model]["components"][comp] = {"error": "fewer than 3 points"}
                continue
            slope, intercept, r2 = linear_fit(tw, yw)
            d_a2ps, d_cm2s = diffusion_from_slope(slope, comp)
            regime, ratio, span = classify_regime(comp, tw, yw, slope, r2)
            rows.append([model, comp, start, end, npts,
                         f"{slope:.4f}", f"{d_a2ps:.6e}", f"{d_cm2s:.6e}",
                         f"{r2:.4f}", f"{ratio:.3f}", regime])
            summary["models"][model]["components"][comp] = {
                "slope_A2_per_ps": slope, "D_A2_per_ps": d_a2ps, "D_cm2_per_s": d_cm2s,
                "r2": r2, "linearity_ratio_late_over_early": ratio, "regime": regime,
                "divisor": DIM_DIVISOR[comp]}
            print(f"  {comp:3s}: slope={slope:8.3f} A^2/ps  D={d_cm2s:.3e} cm^2/s  "
                  f"R^2={r2:.3f}  lin_ratio={ratio:.2f}  [{regime}]")

    os.makedirs(args.resultsdir, exist_ok=True)
    csv_path = os.path.join(args.resultsdir, "diffusion_coefficients.csv")
    with open(csv_path, "w") as fh:
        fh.write("# Phase 7 Li diffusion coefficients (APPARENT/comparative under this MD protocol).\n")
        fh.write("# D = slope/(2*dim): 3D /6, xy /4, z /2.  D[cm^2/s] = D[A^2/ps]*1e-4.\n")
        fh.write("# linearity_ratio = late-half slope / early-half slope in window "
                 "(~1 linear; >1 super-diffusive; <1 saturating).\n")
        fh.write("model,component,fit_start_ps,fit_end_ps,n_points,slope_A2_per_ps,"
                 "D_A2_per_ps,D_cm2_per_s,r2,linearity_ratio,regime\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    json_path = os.path.join(args.resultsdir, "diffusion_summary.json")
    with open(json_path, "w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"\nSaved {csv_path}")
    print(f"Saved {json_path}")
    print("\nNOTE: x-y/3D MSD is super-diffusive and z MSD is a confined plateau over "
          "this 10 ps / 4-Li run; the D values are APPARENT and comparative-only, not "
          "physical Fickian coefficients. See notes/phase7_msd_diffusion_analysis.md.")


if __name__ == "__main__":
    main()
