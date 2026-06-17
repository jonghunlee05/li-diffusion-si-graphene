#!/usr/bin/env python3
"""
compute_li_msd.py  --  Phase 7: Li mean-squared-displacement from Phase 6 trajectories.

Reads the Phase 6 production trajectories for Model A and Model B, selects the Li
atoms only (LAMMPS type 3), and computes the Li MSD as a function of lag time using
a multiple-time-origin average (average over all valid time origins AND over all Li
atoms). Three components are reported:

    * total 3D MSD : <|r(t0+tau) - r(t0)|^2>          (dx^2 + dy^2 + dz^2)
    * x-y in-plane : <dx^2 + dy^2>
    * z-direction  : <dz^2>

Coordinates: the Phase 6 dump is UNWRAPPED (`xu yu zu`), which is required for a
valid MSD across periodic boundaries. This script checks the dump column names and
**fails clearly** if only wrapped (`x y z`) coordinates are present (it cannot
safely unwrap a charge-style dump with no image flags) -- it never fabricates.

NOTE ON DATASET: the listed Phase 6 *_production.lammpstrj trajectories were built
with a since-superseded 9-Li configuration. Phase 7 therefore defaults to the
4-Li `*_ramp_1200K.lammpstrj` trajectories, which are consistent with the current
Model A/B structures (same 1200 K). Override with --model-a-traj/--model-b-traj.
See notes/phase7_msd_diffusion_analysis.md.

Phase 7 is ANALYSIS ONLY: no new MD, no structure changes. With only 4 Li and a
short trajectory the MSD is expected to be noisy; that is reported, not hidden.

Usage:
    python analysis/compute_li_msd.py
    python analysis/compute_li_msd.py --model-a-traj <path> --model-b-traj <path> --dt-fs 0.25
"""

import argparse
import os
import sys

import numpy as np

LI_TYPE = 3                       # LAMMPS atom type for Li (1=C, 2=Si, 3=Li)
DEFAULT_DT_FS = 0.25              # MD timestep (fs), validated Phases 4/5
DEFAULT_A = "trajectories/model_a_ramp_1200K.lammpstrj"
DEFAULT_B = "trajectories/model_b_ramp_1200K.lammpstrj"


def read_dump(path):
    """Parse a LAMMPS custom dump.

    Returns (timesteps, types, coords, unwrapped):
      timesteps : (F,) int MD step of each frame
      types     : (N,) int atom type (from the first frame; sort id assumed)
      coords    : (F, N, 3) float positions, atoms ordered by id
      unwrapped : bool, True if columns were xu/yu/zu
    Exits clearly on a malformed dump or wrapped-only coordinates.
    """
    if not os.path.isfile(path):
        sys.exit(f"ERROR: trajectory not found: {path}")

    timesteps, frames, types0 = [], [], None
    with open(path) as fh:
        lines = fh.read().splitlines()

    i, n = 0, len(lines)
    cols = None
    xcol = ycol = zcol = idcol = typecol = None
    unwrapped = None
    while i < n:
        line = lines[i]
        if line.startswith("ITEM: TIMESTEP"):
            timesteps.append(int(lines[i + 1])); i += 2; continue
        if line.startswith("ITEM: NUMBER OF ATOMS"):
            natoms = int(lines[i + 1]); i += 2; continue
        if line.startswith("ITEM: BOX"):
            i += 4; continue
        if line.startswith("ITEM: ATOMS"):
            cols = line.split()[2:]
            idcol = cols.index("id")
            typecol = cols.index("type")
            # prefer unwrapped columns; detect wrapped-only and refuse
            if {"xu", "yu", "zu"}.issubset(cols):
                xcol, ycol, zcol = cols.index("xu"), cols.index("yu"), cols.index("zu")
                unwrapped = True
            elif {"x", "y", "z"}.issubset(cols):
                xcol, ycol, zcol = cols.index("x"), cols.index("y"), cols.index("z")
                unwrapped = False
            else:
                sys.exit(f"ERROR: {path} ATOMS line has no x/y/z columns: {cols}")
            block = lines[i + 1:i + 1 + natoms]
            arr = np.array([r.split() for r in block], dtype=float)
            order = np.argsort(arr[:, idcol])
            arr = arr[order]
            if types0 is None:
                types0 = arr[:, typecol].astype(int)
            frames.append(arr[:, [xcol, ycol, zcol]])
            i += 1 + natoms
            continue
        i += 1

    if unwrapped is False:
        sys.exit(
            f"ERROR: {path} stores WRAPPED coordinates (x y z) with no image flags; "
            f"a charge-style dump cannot be safely unwrapped post hoc. Re-dump with "
            f"`xu yu zu`. Refusing to compute a fake MSD.")
    if not frames:
        sys.exit(f"ERROR: no frames parsed from {path}")

    return np.array(timesteps), types0, np.stack(frames), unwrapped


def compute_msd(coords):
    """Multiple-time-origin MSD averaged over atoms and origins.

    coords : (F, M, 3) for the M selected (Li) atoms.
    Returns dict of (F,) arrays: msd_3d, msd_xy, msd_z, n_origins (lag 0..F-1).
    """
    F = coords.shape[0]
    msd_3d = np.zeros(F)
    msd_xy = np.zeros(F)
    msd_z = np.zeros(F)
    n_orig = np.zeros(F, dtype=int)
    for lag in range(1, F):
        d = coords[lag:] - coords[:-lag]          # (F-lag, M, 3)
        sq = d ** 2
        msd_3d[lag] = sq.sum(axis=2).mean()       # mean over origins AND atoms
        msd_xy[lag] = sq[:, :, :2].sum(axis=2).mean()
        msd_z[lag] = sq[:, :, 2].mean()
        n_orig[lag] = d.shape[0]                   # time origins at this lag
    return {"msd_3d": msd_3d, "msd_xy": msd_xy, "msd_z": msd_z, "n_origins": n_orig}


def process(model, path, dt_fs, outdir, label=""):
    tag = f"{model}_{label}" if label else model
    print(f"\n=== {tag}: {path} ===")
    timesteps, types, coords, unwrapped = read_dump(path)
    li_mask = types == LI_TYPE
    n_li = int(li_mask.sum())
    if n_li == 0:
        sys.exit(f"ERROR: no Li (type {LI_TYPE}) atoms found in {path}")
    li = coords[:, li_mask, :]                     # (F, n_li, 3)

    F = coords.shape[0]
    # frame spacing in ps from the actual MD steps (robust; not assumed)
    dsteps = np.diff(timesteps)
    if len(set(dsteps.tolist())) != 1:
        print(f"  WARNING: non-uniform frame spacing in {path}: {sorted(set(dsteps))}")
    frame_steps = int(dsteps[0])
    frame_dt_ps = frame_steps * dt_fs / 1000.0
    lag_ps = np.arange(F) * frame_dt_ps

    print(f"  frames={F}  Li atoms={n_li}  unwrapped={unwrapped}")
    print(f"  dt={dt_fs} fs, {frame_steps} steps/frame -> {frame_dt_ps:.4f} ps/frame, "
          f"total {lag_ps[-1]:.3f} ps")
    if n_li < 8 or F < 200:
        print(f"  NOTE: small Li count / short trajectory -> MSD will be noisy "
              f"(especially at large lag where few time origins remain).")

    m = compute_msd(li)
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{tag}_li_msd.csv")
    header = ("time_ps,msd_3d_A2,msd_xy_A2,msd_z_A2,n_origins,n_li\n")
    with open(out, "w") as fh:
        fh.write(f"# MSD for {tag} from {path}\n")
        fh.write(f"# unwrapped={unwrapped}; n_li={n_li}; dt_fs={dt_fs}; "
                 f"frame_steps={frame_steps}; frame_dt_ps={frame_dt_ps:.6f}\n")
        fh.write("# columns: lag time (ps), 3D MSD, x-y MSD, z MSD (all A^2), "
                 "time origins averaged, Li atoms averaged\n")
        fh.write(header)
        for k in range(F):
            fh.write(f"{lag_ps[k]:.6f},{m['msd_3d'][k]:.6f},{m['msd_xy'][k]:.6f},"
                     f"{m['msd_z'][k]:.6f},{m['n_origins'][k]},{n_li}\n")
    print(f"  saved {out}  ({F} rows)")
    return out


def main():
    ap = argparse.ArgumentParser(description="Compute Li MSD (3D, x-y, z) from Phase 6 trajectories.")
    ap.add_argument("--model-a-traj", default=DEFAULT_A)
    ap.add_argument("--model-b-traj", default=DEFAULT_B)
    ap.add_argument("--dt-fs", type=float, default=DEFAULT_DT_FS,
                    help="MD timestep in fs (default 0.25)")
    ap.add_argument("--outdir", default="analysis/results")
    args = ap.parse_args()

    process("model_a", args.model_a_traj, args.dt_fs, args.outdir)
    process("model_b", args.model_b_traj, args.dt_fs, args.outdir)
    print("\nDone. Li MSD (3D / x-y / z) written. No diffusion fit here "
          "(see fit_diffusion_coefficients.py); no MD, no structure changes.")


if __name__ == "__main__":
    main()
