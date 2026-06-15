#!/usr/bin/env python3
"""
inspect_model_a.py  --  Phase 4 Model A structure inspection.

Reports factual geometry for the pristine Si-graphene-Li model and judges whether
it is plausible to minimize (no overlaps). Does NOT run MD or compute diffusion.

Reported:
  - atom counts by element (Si, C, Li) and total
  - box dimensions (A)
  - minimum distances: Li-C, Li-Si, C-Si, Si-Si, C-C
  - overlap detection
  - a plausibility verdict for minimization

Default input: structures/model_a_pristine.data (LAMMPS, type 1=C,2=Si,3=Li).
A .xyz may also be passed.

Usage:
    python analysis/inspect_model_a.py
    python analysis/inspect_model_a.py structures/model_a_pristine_minimized.data
"""

import argparse
import os
import sys

import numpy as np
from ase.io import read


# Below these per-pair distances, treat as an overlap (unphysical starting point).
# Reference NN: C-C ~1.42, Si-Si ~2.35, C-Si ~1.9, Li-C/Li-Si a few A.
OVERLAP = {"C-C": 1.1, "Si-Si": 1.8, "C-Si": 1.3, "Li-C": 1.3, "Li-Si": 1.3}


def load(path):
    if not os.path.isfile(path):
        sys.exit(f"ERROR: not found: {path}\n"
                 f"Build it first: python structures/build_model_a_pristine.py")
    if path.lower().endswith(".data"):
        return read(path, format="lammps-data", atom_style="charge",
                    Z_of_type={1: 6, 2: 14, 3: 3})   # 1=C, 2=Si, 3=Li
    return read(path)


def min_dist(atoms, ia, ib):
    if len(ia) == 0 or len(ib) == 0:
        return None
    best = np.inf
    for i in ia:
        tgt = [j for j in ib if j != i]
        if not tgt:
            continue
        best = min(best, float(np.min(atoms.get_distances(i, tgt, mic=True))))
    return best if np.isfinite(best) else None


def main():
    ap = argparse.ArgumentParser(description="Inspect Model A (pristine Si-graphene-Li).")
    ap.add_argument("structure", nargs="?",
                    default=os.path.join("structures", "model_a_pristine.data"))
    args = ap.parse_args()

    atoms = load(args.structure)
    sym = np.array(atoms.get_chemical_symbols())
    idx = {el: np.where(sym == el)[0] for el in ("C", "Si", "Li")}
    box = atoms.get_cell().lengths()

    pairs = {
        "Li-C": (idx["Li"], idx["C"]),
        "Li-Si": (idx["Li"], idx["Si"]),
        "C-Si": (idx["C"], idx["Si"]),
        "Si-Si": (idx["Si"], idx["Si"]),
        "C-C": (idx["C"], idx["C"]),
    }
    dists = {k: min_dist(atoms, a, b) for k, (a, b) in pairs.items()}

    print(f"Structure : {args.structure}")
    print(f"Total atoms: {len(atoms)}")
    print(f"  Si : {len(idx['Si'])}")
    print(f"  C  : {len(idx['C'])}")
    print(f"  Li : {len(idx['Li'])}")
    print(f"Box (A)   : {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    print("Minimum distances (A):")
    for k in ("Li-C", "Li-Si", "C-Si", "Si-Si", "C-C"):
        d = dists[k]
        print(f"  {k:6s}: {d:.3f}" if d is not None else f"  {k:6s}: n/a")

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
