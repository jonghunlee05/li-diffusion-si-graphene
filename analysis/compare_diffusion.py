#!/usr/bin/env python3
"""
compare_diffusion.py  --  Phase 7: Model B vs Model A diffusion comparison.

Reads analysis/results/diffusion_coefficients.csv, computes the ratio D_B / D_A for
each component (3D, x-y, z), and reports -- based ONLY on the calculated values --
whether Model B (single-vacancy) appears higher, lower, or similar to Model A
(pristine). Saves:

    analysis/results/model_b_over_model_a_ratio.csv

IMPORTANT (does not fabricate / does not overclaim): the underlying D's are
APPARENT, comparative-only values from a short (10 ps), 4-Li run whose x-y/3D MSD is
super-diffusive and whose z MSD is a confined plateau. This script therefore carries
each component's `regime` through to the output and flags any ratio whose components
are not a clean Fickian fit. It makes NO real-battery or absolute-diffusivity claim
(Phase 7 rule #9). "Similar" is defined as |ratio - 1| <= 0.15 (15%).

Usage:
    python analysis/compare_diffusion.py
"""

import csv
import os
import sys

RESULTS = "analysis/results"
SIM_TOL = 0.15            # |ratio-1| <= 15% -> "similar"
COMPONENTS = ["3d", "xy", "z"]


def load_coeffs(path):
    if not os.path.isfile(path):
        sys.exit(f"ERROR: {path} not found (run fit_diffusion_coefficients.py first).")
    table = {}
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("model,") or not line.strip():
                continue
            r = next(csv.reader([line]))
            model, comp = r[0], r[1]
            table[(model, comp)] = {
                "slope": float(r[5]) if r[5] else float("nan"),
                "D_cm2_s": float(r[7]) if r[7] else float("nan"),
                "r2": float(r[8]) if r[8] else float("nan"),
                "regime": r[10],
            }
    return table


def verdict(ratio):
    if ratio != ratio:                       # NaN
        return "undetermined"
    if abs(ratio - 1.0) <= SIM_TOL:
        return "similar"
    return "higher" if ratio > 1.0 else "lower"


def main():
    table = load_coeffs(os.path.join(RESULTS, "diffusion_coefficients.csv"))
    rows = []
    print("Model B / Model A diffusion comparison (apparent, comparative-only):\n")
    for comp in COMPONENTS:
        a = table.get(("model_a", comp)); b = table.get(("model_b", comp))
        if not a or not b:
            print(f"  {comp}: missing data"); continue
        da, db = a["D_cm2_s"], b["D_cm2_s"]
        ratio = db / da if da not in (0.0,) and da == da else float("nan")
        v = verdict(ratio)
        # confined z (near-zero / sign-flipping D) -> ratio is not meaningful
        note = ""
        if "confined" in a["regime"] or "confined" in b["regime"]:
            note = "z is a confined plateau; ratio not physically meaningful"
            v = "undetermined (confined)"
        elif "super-diffusive" in a["regime"] or "super-diffusive" in b["regime"]:
            note = "super-diffusive window; apparent ratio only"
        print(f"  {comp:3s}: D_A={da:.3e}  D_B={db:.3e}  D_B/D_A={ratio:.3f}  -> "
              f"Model B {v}" + (f"   [{note}]" if note else ""))
        rows.append([comp, f"{da:.6e}", f"{db:.6e}",
                     f"{ratio:.6f}" if ratio == ratio else "nan", v,
                     a["regime"], b["regime"], note])

    out = os.path.join(RESULTS, "model_b_over_model_a_ratio.csv")
    with open(out, "w") as fh:
        fh.write("# Phase 7: D_B/D_A by component. APPARENT, comparative-only under "
                 "this MD protocol -- NOT a real-battery claim.\n")
        fh.write(f"# 'similar' = |ratio-1| <= {SIM_TOL}; z is confined (ratio not meaningful).\n")
        fh.write("component,D_A_cm2_s,D_B_cm2_s,ratio_B_over_A,verdict,regime_A,regime_B,note\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    print(f"\nSaved {out}")
    print("\nReminder: comparative only under this MD protocol; no real-battery "
          "performance is implied (Phase 7 rule #9).")


if __name__ == "__main__":
    main()
