#!/usr/bin/env python3
"""
inspect_structure.py  --  Phase 2 structure inspection / sanity check.

Reads a graphene + Li structure and reports basic, factual geometry so you can
confirm the initial structure is sensible BEFORE doing anything else. It does
NOT run MD, compute MSD, or produce any diffusion result.

Reported quantities:
  - total atom count
  - number of C atoms
  - number of Li atoms
  - box dimensions (cell lengths, A)
  - minimum Li-C distance (A, minimum-image / periodic-aware)
  - approximate C-C nearest-neighbor distance (A, periodic-aware)
  - an overlap WARNING if any distance looks unphysically short

Default input is structures/graphene_li.xyz (extended-XYZ, which carries both
elements and the periodic cell). A LAMMPS .data file may also be passed.

Usage:
    python analysis/inspect_structure.py
    python analysis/inspect_structure.py structures/graphene_li.xyz
    python analysis/inspect_structure.py structures/graphene_li.data
"""

import argparse
import os
import sys

import numpy as np
from ase.io import read


# --- Sanity thresholds (clearly labeled, not physics parameters) ------
# Below these distances, atoms are almost certainly overlapping / unphysical.
# Reference values: ideal graphene C-C ~1.42 A; Li starts ~2.3 A above C here.
CC_MIN_OK = 1.2      # A, C-C shorter than this => warn (graphene is ~1.42)
LIC_MIN_OK = 1.5     # A, Li-C shorter than this => warn (start is ~2.3)


def load_structure(path):
    """Read the structure, choosing a reader based on the file extension."""
    if not os.path.isfile(path):
        sys.exit(f"ERROR: structure file not found: {path}\n"
                 f"Hint: build it first with  python structures/build_graphene_li.py")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".data":
        # LAMMPS data: map type 1 -> C, type 2 -> Li (the build script's order).
        atoms = read(path, format="lammps-data", atom_style="atomic",
                     Z_of_type={1: 6, 2: 3})
    else:
        # extended-XYZ (and plain XYZ) carry element symbols directly.
        atoms = read(path)
    return atoms


def min_pair_distance(atoms, idx_a, idx_b):
    """
    Minimum periodic-aware distance between atom group A and atom group B.

    Uses ASE's minimum-image convention via get_distances() so distances across
    the periodic graphene cell are handled correctly. Returns None if either
    group is empty.
    """
    if len(idx_a) == 0 or len(idx_b) == 0:
        return None
    best = np.inf
    for i in idx_a:
        d = atoms.get_distances(i, idx_b, mic=True)
        best = min(best, float(np.min(d)))
    return best


def main():
    parser = argparse.ArgumentParser(description="Inspect a graphene + Li structure (Phase 2).")
    parser.add_argument("structure", nargs="?",
                        default=os.path.join("structures", "graphene_li.xyz"),
                        help="path to the structure file "
                             "(default: structures/graphene_li.xyz)")
    args = parser.parse_args()

    atoms = load_structure(args.structure)
    symbols = np.array(atoms.get_chemical_symbols())

    c_idx = np.where(symbols == "C")[0]
    li_idx = np.where(symbols == "Li")[0]

    n_total = len(atoms)
    n_c = len(c_idx)
    n_li = len(li_idx)
    box = atoms.get_cell().lengths()

    # Minimum Li-C distance (across the periodic cell).
    min_li_c = min_pair_distance(atoms, li_idx, c_idx)

    # Approximate C-C nearest-neighbor distance: smallest C-C separation.
    cc_nn = None
    if n_c > 1:
        best = np.inf
        for k, i in enumerate(c_idx):
            others = c_idx[c_idx != i]
            d = atoms.get_distances(i, others, mic=True)
            best = min(best, float(np.min(d)))
        cc_nn = best

    # --- Report -------------------------------------------------------
    print(f"Structure file : {args.structure}")
    print(f"Total atoms    : {n_total}")
    print(f"  C atoms      : {n_c}")
    print(f"  Li atoms     : {n_li}")
    print(f"Box (A)        : {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    if min_li_c is not None:
        print(f"Min Li-C dist  : {min_li_c:.3f} A")
    else:
        print("Min Li-C dist  : n/a (need both Li and C atoms)")
    if cc_nn is not None:
        print(f"C-C nn dist    : {cc_nn:.3f} A   (ideal graphene ~1.42 A)")
    else:
        print("C-C nn dist    : n/a (need >1 C atom)")

    # --- Overlap / sanity warnings ------------------------------------
    warnings = []
    if cc_nn is not None and cc_nn < CC_MIN_OK:
        warnings.append(f"C-C nearest neighbor {cc_nn:.3f} A < {CC_MIN_OK} A "
                        f"(possible overlap / wrong lattice)")
    if min_li_c is not None and min_li_c < LIC_MIN_OK:
        warnings.append(f"Li-C distance {min_li_c:.3f} A < {LIC_MIN_OK} A "
                        f"(Li may overlap graphene)")

    print()
    if warnings:
        print("OVERLAP WARNING:")
        for w in warnings:
            print(f"  - {w}")
        sys.exit(1)
    else:
        print("OK: no obvious overlaps; geometry looks reasonable for an "
              "initial structure.")
        sys.exit(0)


if __name__ == "__main__":
    main()
