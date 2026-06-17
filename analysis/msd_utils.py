#!/usr/bin/env python3
"""
msd_utils.py  --  Phase 7 shared helpers (single source of truth).

Centralizes the MSD CSV loader, the linear fit, the diffusion-coefficient
dimensional factors, and the unit conversion so Model A and Model B are analyzed
by *byte-identical* code (Phase 7 rule: same method for both models).

MSD definition (computed in compute_li_msd.py):
    MSD_d(tau) = < |r(t0+tau) - r(t0)|^2 >   averaged over Li atoms and origins
For normal (Fickian) diffusion the long-time MSD is linear in tau:
    MSD_d(tau) = 2 * dim * D * tau   ->   D = slope / (2 * dim)
  3D  (dim=3): D = slope / 6
  x-y (dim=2): D = slope / 4
  z   (dim=1): D = slope / 2

Unit conversion (slope is in Å²/ps):
    1 Å = 1e-8 cm        ->  1 Å²   = 1e-16 cm²
    1 ps = 1e-12 s       ->  1 Å²/ps = 1e-16/1e-12 = 1e-4 cm²/s
So D[cm²/s] = D[Å²/ps] * 1e-4.
"""

import csv
import sys

import numpy as np

# slope (Å²/ps) -> D (Å²/ps): divide by 2*dim
DIM_DIVISOR = {"3d": 6.0, "xy": 4.0, "z": 2.0}
# CSV MSD column for each component
MSD_COLUMN = {"3d": "msd_3d_A2", "xy": "msd_xy_A2", "z": "msd_z_A2"}
# Å²/ps -> cm²/s
ANG2_PER_PS_TO_CM2_PER_S = 1.0e-4


def load_msd_csv(path):
    """Load an MSD CSV (skips '#' comment lines). Returns dict col -> np.ndarray."""
    rows, header = [], None
    try:
        with open(path) as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                parts = next(csv.reader([line]))
                if header is None:
                    header = [p.strip() for p in parts]
                    continue
                rows.append([float(x) for x in parts])
    except FileNotFoundError:
        sys.exit(f"ERROR: MSD CSV not found: {path} (run compute_li_msd.py first)")
    if header is None or not rows:
        sys.exit(f"ERROR: no data parsed from {path}")
    arr = np.array(rows, dtype=float)
    return {h: arr[:, i] for i, h in enumerate(header)}


def linear_fit(t, y):
    """Least-squares line y = slope*t + intercept. Returns (slope, intercept, r2)."""
    if len(t) < 2:
        sys.exit("ERROR: need >= 2 points to fit a line.")
    slope, intercept = np.polyfit(t, y, 1)
    yhat = slope * t + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(slope), float(intercept), r2


def diffusion_from_slope(slope_A2_per_ps, component):
    """Convert an MSD slope (Å²/ps) to D in Å²/ps and cm²/s for a component."""
    div = DIM_DIVISOR[component]
    d_ang2_ps = slope_A2_per_ps / div
    d_cm2_s = d_ang2_ps * ANG2_PER_PS_TO_CM2_PER_S
    return d_ang2_ps, d_cm2_s


def select_window(data, start_ps, end_ps):
    """Boolean mask + (t, n_origins) for the time window [start_ps, end_ps]."""
    t = data["time_ps"]
    mask = (t >= start_ps) & (t <= end_ps)
    return mask
