#!/usr/bin/env python3
"""
inspect_model_b.py  --  Phase 5 Model B structure inspection.

Reports factual geometry for the single-vacancy Si-graphene-Li model and judges
plausibility for minimization. Also reports the vacancy location (from the
metadata file). Does NOT run MD or compute diffusion.

Reported:
  - atom counts by element (Si, C, Li) and total
  - box dimensions (A)
  - minimum pair distances: Li-C, Li-Si, C-Si, Si-Si, C-C
  - vacancy location (removed carbon coordinates, from metadata)
  - overlap detection + plausibility verdict

Usage:
    python analysis/inspect_model_b.py
    python analysis/inspect_model_b.py structures/model_b_sv_minimized.data
"""

import argparse
import json
import os
import sys

import numpy as np
from ase.io import read

META = "structures/model_b_sv_metadata.json"
OVERLAP = {"C-C": 1.1, "Si-Si": 1.8, "C-Si": 1.3, "Li-C": 1.3, "Li-Si": 1.3}


def load(path):
    if not os.path.isfile(path):
        sys.exit(f"ERROR: not found: {path}\n"
                 f"Build it first: python structures/build_model_b_sv.py")
    if path.lower().endswith(".data"):
        return read(path, format="lammps-data", atom_style="charge",
                    Z_of_type={1: 6, 2: 14, 3: 3})
    return read(path)


def min_dist(atoms, ia, ib):
    if len(ia) == 0 or len(ib) == 0:
        return None
    best = np.inf
    for i in ia:
        tgt = [j for j in ib if j != i]
        if tgt:
            best = min(best, float(np.min(atoms.get_distances(i, tgt, mic=True))))
    return best if np.isfinite(best) else None


def main():
    ap = argparse.ArgumentParser(description="Inspect Model B (single-vacancy Si-graphene-Li).")
    ap.add_argument("structure", nargs="?",
                    default=os.path.join("structures", "model_b_sv.data"))
    args = ap.parse_args()

    atoms = load(args.structure)
    sym = np.array(atoms.get_chemical_symbols())
    idx = {e: np.where(sym == e)[0] for e in ("C", "Si", "Li")}
    box = atoms.get_cell().lengths()

    dists = {
        "Li-C": min_dist(atoms, idx["Li"], idx["C"]),
        "Li-Si": min_dist(atoms, idx["Li"], idx["Si"]),
        "C-Si": min_dist(atoms, idx["C"], idx["Si"]),
        "Si-Si": min_dist(atoms, idx["Si"], idx["Si"]),
        "C-C": min_dist(atoms, idx["C"], idx["C"]),
    }

    print(f"Structure : {args.structure}")
    print(f"Total atoms: {len(atoms)}")
    print(f"  Si : {len(idx['Si'])}")
    print(f"  C  : {len(idx['C'])}  (single vacancy: one C removed vs pristine)")
    print(f"  Li : {len(idx['Li'])}")
    print(f"Box (A)   : {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    print("Minimum distances (A):")
    for k in ("Li-C", "Li-Si", "C-Si", "Si-Si", "C-C"):
        d = dists[k]
        print(f"  {k:6s}: {d:.3f}" if d is not None else f"  {k:6s}: n/a")

    if os.path.isfile(META):
        rc = json.load(open(META)).get("removed_carbon", {})
        print("Vacancy location (removed C, from metadata):")
        print(f"  Model A index/id : {rc.get('index_0based_in_model_a')} / "
              f"{rc.get('lammps_id_1based_in_model_a')}")
        print(f"  coordinates (A)  : {rc.get('coordinates_xyz_A')}")
    else:
        print(f"NOTE: vacancy metadata not found ({META})")

    overlaps = [(k, dists[k]) for k in dists
                if dists[k] is not None and dists[k] < OVERLAP[k]]
    print()
    if overlaps:
        print("OVERLAP DETECTED -- structure is NOT plausible for minimization:")
        for k, d in overlaps:
            print(f"  - {k}: {d:.3f} A < {OVERLAP[k]} A")
        sys.exit(1)
    print("OK: no overlaps; structure is plausible for ReaxFF minimization.")
    sys.exit(0)


if __name__ == "__main__":
    main()
