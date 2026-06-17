#!/usr/bin/env python3
"""
plot_msd.py  --  Phase 7: Model A vs Model B MSD comparison plots.

Reads the MSD CSVs produced by compute_li_msd.py and makes three A-vs-B figures:

    figures/phase7_msd_3d_model_a_vs_b.png    (total 3D MSD)
    figures/phase7_msd_xy_model_a_vs_b.png    (in-plane x-y MSD)
    figures/phase7_msd_z_model_a_vs_b.png     (z / interface-normal MSD)

These are diagnostic plots: they exist so the linear-regime fitting window can be
chosen by LOOKING at the data (Phase 7 rule: do not pick the window blindly). No
fit and no diffusion coefficient are computed here. Fails clearly if a CSV is
missing -- never fabricates.

Usage:
    python analysis/plot_msd.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

from msd_utils import load_msd_csv   # noqa: E402

RESULTS = "analysis/results"
FIGS = "figures"
MODELS = [("model_a", "Model A (pristine)", "tab:blue"),
          ("model_b", "Model B (single-vacancy)", "tab:red")]
# (csv column, title, output file)
COMPONENTS = [
    ("msd_3d_A2", "total 3D MSD", "phase7_msd_3d_model_a_vs_b.png"),
    ("msd_xy_A2", "in-plane x-y MSD", "phase7_msd_xy_model_a_vs_b.png"),
    ("msd_z_A2",  "z-direction MSD", "phase7_msd_z_model_a_vs_b.png"),
]


def load(model):
    return load_msd_csv(os.path.join(RESULTS, f"{model}_li_msd.csv"))


def main():
    os.makedirs(FIGS, exist_ok=True)
    cache = {m: load(m) for m, _, _ in MODELS}

    for col, title, fname in COMPONENTS:
        fig, ax = plt.subplots(figsize=(7, 5))
        for model, label, color in MODELS:
            d = cache[model]
            ax.plot(d["time_ps"], d[col], color=color, lw=1.2, label=label)
        ax.set_xlabel("lag time (ps)")
        ax.set_ylabel(f"{title} (Å²)")
        ax.set_title(f"Phase 7 — Li {title}: Model A vs Model B\n"
                     f"(4 Li, 1200 K ramp stage; large-lag tail is noisy)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        out = os.path.join(FIGS, fname)
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"Saved {out}")
    print("Done. Comparison plots only — no fit, no diffusion (see "
          "fit_diffusion_coefficients.py).")


if __name__ == "__main__":
    main()
