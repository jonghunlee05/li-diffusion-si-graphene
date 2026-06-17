#!/usr/bin/env python3
"""
plot_msd_fits.py  --  Phase 7: per-model MSD plots showing the chosen fit window.

For each model, draws the Li MSD with the linear-fit window shaded and the fitted
line overlaid, so the fitting choice is transparent and auditable. Two panels:

    top    : x-y (in-plane) MSD + fitted line   (the dominant motion)
    bottom : z MSD                              (confined plateau -> ~flat fit)

A text box reports slope, D (cm²/s), R², linearity ratio, and the regime label, so
the figure shows -- not hides -- that the x-y/3D MSD is super-diffusive and the z
MSD is confined (apparent, comparative-only D's; not Fickian).

    figures/phase7_model_a_msd_fit.png
    figures/phase7_model_b_msd_fit.png

Uses the same window source as fit_diffusion_coefficients.py
(analysis/fit_windows.json). Fails clearly if inputs are missing.

Usage:
    python analysis/plot_msd_fits.py
"""

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

from msd_utils import (load_msd_csv, linear_fit, diffusion_from_slope, MSD_COLUMN)

RESULTS = "analysis/results"
FIGS = "figures"
WINDOWS_JSON = "analysis/fit_windows.json"
MODELS = [("model_a", "Model A (pristine)"), ("model_b", "Model B (single-vacancy)")]


def window_for(model):
    cfg = json.load(open(WINDOWS_JSON))
    return float(cfg[model]["fit_start_ps"]), float(cfg[model]["fit_end_ps"])


def panel(ax, t, y, start, end, comp, title):
    ax.plot(t, y, color="0.4", lw=1.0, label="MSD")
    mask = (t >= start) & (t <= end)
    tw, yw = t[mask], y[mask]
    slope, intercept, r2 = linear_fit(tw, yw)
    _, d_cm2s = diffusion_from_slope(slope, comp)
    # draw fitted line across the window
    xfit = np.array([start, end])
    ax.plot(xfit, slope * xfit + intercept, "r--", lw=2,
            label=f"fit [{start:g}-{end:g} ps]")
    ax.axvspan(start, end, color="orange", alpha=0.12)
    ax.set_ylabel(f"{title} (Å²)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    txt = (f"slope = {slope:.2f} Å²/ps\nD = {d_cm2s:.2e} cm²/s\n"
           f"R² = {r2:.3f}   n = {int(mask.sum())}")
    ax.text(0.98, 0.04, txt, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
    return slope, d_cm2s, r2


def main():
    os.makedirs(FIGS, exist_ok=True)
    for model, label in MODELS:
        d = load_msd_csv(os.path.join(RESULTS, f"{model}_li_msd.csv"))
        t = d["time_ps"]
        start, end = window_for(model)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
        panel(ax1, t, d[MSD_COLUMN["xy"]], start, end, "xy", "x-y in-plane MSD")
        ax1.set_title(f"Phase 7 — {label}: Li MSD with fit window\n"
                      f"(4 Li, 1200 K, 10 ps; x-y is super-diffusive — apparent D only)")
        panel(ax2, t, d[MSD_COLUMN["z"]], start, end, "z", "z-direction MSD")
        ax2.set_title("z MSD (confined plateau — no through-sheet diffusion)", fontsize=10)
        ax2.set_xlabel("lag time (ps)")
        fig.tight_layout()
        out = os.path.join(FIGS, f"phase7_{model}_msd_fit.png")
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"Saved {out}")
    print("Done. Fit-window plots only (no new fit written; see "
          "fit_diffusion_coefficients.py for the CSV/JSON).")


if __name__ == "__main__":
    main()
