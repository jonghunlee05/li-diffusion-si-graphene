#!/usr/bin/env python3
"""
build_reaxff_smoke_test.py  --  Phase 3 ReaxFF/QEq smoke-test structure.

Creates a TINY, well-separated Li-Si-C cluster whose ONLY purpose is to check
that the Li-Si-C ReaxFF force field loads in LAMMPS, that atom types map to the
right elements, that charge equilibration (QEq) runs, and that a very short run
does not crash. It is NOT a physical model of anything.

SCOPE (Phase 3 smoke test only):
  - A handful of C, Si, Li atoms, deliberately well separated (no overlaps).
  - NO graphene sheet, NO silicon slab, NO interface (those are Phase 4+).
  - NO production MD, NO MSD/diffusion.

Exports (atom_style = charge, so it matches the LAMMPS input's atom_style):
    structures/reaxff_smoke_test.data   LAMMPS data file (id type q x y z) + Masses
    structures/reaxff_smoke_test.xyz    extended-XYZ for OVITO

IMPORTANT -- ATOM TYPE ORDER:
  We fix the type order as  type 1 = C, type 2 = Si, type 3 = Li  (via specorder).
  The LAMMPS input's pair_coeff line MUST list element labels in this SAME order:
      pair_coeff * * <reaxff file> C Si Li
  and those labels must match element names present in the real ReaxFF file.
  See force_fields/README.md and lammps_inputs/in.reaxff_smoke_test.

This script assigns NO force-field parameters and produces NO scientific results.
Initial charges are written as 0.0; QEq assigns real charges at run time.

Usage:
    python structures/build_reaxff_smoke_test.py
"""

import os

import numpy as np
from ase import Atoms
from ase.io import write


# Fixed type order -> must match pair_coeff element order in the LAMMPS input.
SPECORDER = ["C", "Si", "Li"]

# Cubic box edge (A). Large enough that periodic images are far apart for a
# small ReaxFF cluster. Not physical -- just a roomy box for a smoke test.
BOX = 20.0

# Minimum acceptable interatomic separation (A). Below this we abort, because
# overlapping atoms would make ReaxFF/QEq blow up and invalidate the test.
MIN_SEP = 2.0

# A small, deliberately well-separated arrangement of C/Si/Li atoms.
# Spacing ~2.7 A keeps atoms within ReaxFF interaction range while avoiding
# any overlap. Positions are arbitrary smoke-test coordinates, not a structure.
ATOMS = [
    ("C",  (0.00, 0.00, 0.00)),
    ("C",  (2.70, 0.00, 0.00)),
    ("Si", (0.00, 2.70, 0.00)),
    ("Si", (2.70, 2.70, 0.00)),
    ("Li", (1.35, 1.35, 2.70)),
    ("Li", (1.35, 1.35, -2.70)),
]


def build_cluster():
    """Build the tiny Li-Si-C ASE Atoms cluster, centered in a cubic box."""
    symbols = [a[0] for a in ATOMS]
    positions = np.array([a[1] for a in ATOMS], dtype=float)

    atoms = Atoms(symbols=symbols, positions=positions,
                  cell=[BOX, BOX, BOX], pbc=[True, True, True])
    atoms.center()  # move the cluster to the middle of the box
    return atoms


def min_separation(atoms):
    """Smallest pairwise distance (periodic-aware) among all atoms, in A."""
    best = np.inf
    n = len(atoms)
    for i in range(n):
        d = atoms.get_distances(i, [j for j in range(n) if j != i], mic=True)
        best = min(best, float(np.min(d)))
    return best


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(out_dir, "reaxff_smoke_test.data")
    xyz_path = os.path.join(out_dir, "reaxff_smoke_test.xyz")

    atoms = build_cluster()

    # Safety: refuse to write an overlapping structure.
    sep = min_separation(atoms)
    if sep < MIN_SEP:
        raise SystemExit(f"ERROR: minimum separation {sep:.3f} A < {MIN_SEP} A "
                         f"(atoms overlap). Adjust ATOMS positions.")

    # Export. atom_style 'charge' writes an (id type q x y z) Atoms section with
    # q = 0; masses=True writes a Masses block; specorder fixes the type order.
    write(data_path, atoms, format="lammps-data",
          atom_style="charge", specorder=SPECORDER, masses=True)
    write(xyz_path, atoms, format="extxyz")

    # Count atoms per element for the summary.
    syms = atoms.get_chemical_symbols()
    counts = {el: syms.count(el) for el in SPECORDER}

    print("Built Li-Si-C ReaxFF smoke-test cluster (Phase 3):")
    print(f"  atoms        : {len(atoms)}  "
          f"(C={counts['C']}, Si={counts['Si']}, Li={counts['Li']})")
    print(f"  type order   : 1=C, 2=Si, 3=Li  "
          f"-> pair_coeff must be: C Si Li")
    print(f"  box (A)      : {BOX} x {BOX} x {BOX}")
    print(f"  min sep (A)  : {sep:.3f}  (>= {MIN_SEP} required; no overlaps)")
    print(f"  LAMMPS data  : {data_path}  (atom_style charge)")
    print(f"  XYZ          : {xyz_path}")
    print("Next: add the real ReaxFF file, then run "
          "lmp -in lammps_inputs/in.reaxff_smoke_test")


if __name__ == "__main__":
    main()
