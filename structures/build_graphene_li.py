#!/usr/bin/env python3
"""
build_graphene_li.py  --  Phase 2 structure generation.

Builds a small, PRISTINE graphene sheet and places a few lithium atoms above it,
then exports the combined structure to:
    structures/graphene_li.xyz    (extended-XYZ: elements + cell; opens in OVITO)
    structures/graphene_li.data   (LAMMPS data file, atom_style atomic, w/ Masses)

SCOPE (Phase 2 only):
  - Pristine graphene  -- NO defects yet.
  - A small number of Li atoms above the sheet.
  - NO silicon. NO ReaxFF. NO MD. NO MSD/diffusion.
The single goal is one reproducible graphene + Li INITIAL structure to validate
and visualize in OVITO.

------------------------------------------------------------------------------
PROVENANCE OF EVERY NUMERIC PARAMETER (per the project methodology document,
literature/si_graphene_li_diffusion_methodology_paper.docx):

  GRAPHENE_A = 2.467 A   graphene lattice constant.
                         LITERATURE-BACKED: Chou & Hwang 2013 [1]
                         (methodology Sec. 3 & 5; experimental ~2.46 A).

  Sheet size = 48 C, rectangular ~12.819 x 9.868 A^2.
                         LITERATURE PRECEDENT: Chou & Hwang 2013 [1] used a
                         48-C rectangular sheet of 12.8187 x 9.8680 A^2
                         (methodology Sec. 3). The methodology (Sec. 4.1 / 5)
                         states Phase 2 sheet size is a DOCUMENTED PROJECT
                         CHOICE; we deliberately adopt the 48-C literature
                         precedent so the size is paper-anchored, not arbitrary.
                         Built as 4 x 3 orthogonal graphene cells (4 atoms each).

  LI_HEIGHT  = 2.3 A     Li starting height above the graphene plane.
                         LITERATURE-BACKED: Chou & Hwang 2013 [1], verbatim:
                         "the first layer (|z| ~ 1.7 to 3.0 A) comprises only Li
                         atoms with the average Li-Gr distance around 2.3 A".
                         This is a STARTING placement to avoid overlap, NOT an
                         equilibrium distance (relaxed in later phases).

                         REJECTED ALTERNATIVE: the same paper also reports
                         "1.73 A for single Li adsorption on graphene" -- the
                         isolated bare-graphene value. We do NOT use 1.73 A,
                         because (a) the project target system is the Si-graphene
                         COMPOSITE interface, for which 2.3 A is Chou & Hwang's
                         own interface-layer distance; (b) this height is only a
                         pre-relaxation placeholder and does not affect results;
                         and (c) 2.3 A is the larger, overlap-safe gap. The
                         silicon-free Phase 2 sheet is a build stepping stone,
                         not a single-adsorption study, so 2.3 A is the correct
                         anchor. (methodology Sec. 5 selects 2.3 A.)

  N_LI       = 6         number of Li atoms.
                         DOCUMENTED PROJECT CHOICE (methodology Sec. 4.1: "Exact
                         Phase 2 sheet size and Li count remain documented
                         project choices"). No cited paper specifies an isolated
                         graphene+Li loading -- the only literature Li loading
                         (30 Li, Si et al. [9]) is for a 30-Si COMPOSITE cell,
                         so it is not transferable here. A small count is used
                         for an overlap-free visualization structure only.

  VACUUM     = 20.0 A    total z-vacuum (isolated graphene).
                         LITERATURE-BACKED: Qin et al. 2021 [2] ~20 A vacuum for
                         isolated graphene tests (methodology Sec. 5).

This script assigns NO force-field parameters and produces NO scientific
results. References [1], [2], [9] are the methodology document's numbering.
------------------------------------------------------------------------------

Usage:
    python structures/build_graphene_li.py
    python structures/build_graphene_li.py --nx 4 --ny 3 --n-li 6
"""

import argparse
import os

import numpy as np
from ase import Atoms
from ase.io import write


# --- Methodology-sourced parameters (see PROVENANCE block above) ------
GRAPHENE_A = 2.467   # A, lattice constant -- Chou & Hwang [1] (literature-backed)
LI_HEIGHT = 2.3      # A, Li starting height -- Chou & Hwang [1] interface-layer
                     # value (~2.3 A); NOT the 1.73 A single-adsorption value.
                     # See PROVENANCE block above for why 2.3 A is used.
VACUUM = 20.0        # A, total z-vacuum -- Qin et al. [2] (literature-backed)

# Default sheet = 48-C Chou & Hwang [1] precedent = 4 x 3 orthogonal cells.
DEFAULT_NX = 4       # orthogonal graphene cells along x (zigzag period a)
DEFAULT_NY = 3       # orthogonal graphene cells along y (period a*sqrt(3))
DEFAULT_N_LI = 6     # documented project choice (methodology Sec. 4.1)


def build_orthogonal_graphene(nx, ny):
    """
    Build a pristine graphene sheet on a RECTANGULAR (orthogonal) cell.

    We construct the 4-atom orthorhombic graphene cell explicitly (rather than
    shearing the rhombic primitive) so the cell is a clean rectangle matching the
    Chou & Hwang [1] precedent. The cell is:
        Lx = a            = 2.467 A   (zigzag period)
        Ly = a * sqrt(3)  = 4.273 A   (armchair period)
    with C-C bond length d = a / sqrt(3) = 1.424 A.

    The 4 basis atoms (fractional coords of the Lx x Ly cell) are the standard
    orthorhombic graphene basis:
        (0, 0), (1/2, 1/6), (1/2, 1/2), (0, 2/3)

    Repeating (nx, ny) = (4, 3) gives 48 carbon atoms and a box of
    9.868 x 12.819 A -- i.e. the Chou & Hwang [1] 12.8187 x 9.8680 A^2 sheet
    (axes transposed). Returns carbon-only ASE Atoms.
    """
    Lx = GRAPHENE_A                      # 2.467 A
    Ly = GRAPHENE_A * np.sqrt(3.0)       # 4.273 A
    # z is a temporary placeholder; the documented VACUUM is applied later.
    cell = [Lx, Ly, 1.0]

    # Standard 4-atom orthorhombic graphene basis (fractional in x, y; z = 0).
    frac = np.array([
        [0.0, 0.0],
        [0.5, 1.0 / 6.0],
        [0.5, 0.5],
        [0.0, 2.0 / 3.0],
    ])
    positions = np.column_stack([frac[:, 0] * Lx, frac[:, 1] * Ly, np.zeros(len(frac))])

    unit = Atoms("C4", positions=positions, cell=cell, pbc=[True, True, True])
    sheet = unit.repeat((nx, ny, 1))
    return sheet


def add_lithium(sheet, n_li):
    """
    Place `n_li` lithium atoms in a flat layer LI_HEIGHT above the graphene
    plane, on a near-square grid so they do not overlap each other or sit
    directly on a carbon by construction.

    Returns a NEW Atoms object (graphene + Li); the input is not modified.
    """
    c_positions = sheet.get_positions()
    xmin, ymin = c_positions[:, 0].min(), c_positions[:, 1].min()
    xmax, ymax = c_positions[:, 0].max(), c_positions[:, 1].max()
    z_li = c_positions[:, 2].mean() + LI_HEIGHT  # documented starting height

    ncols = int(np.ceil(np.sqrt(n_li)))
    nrows = int(np.ceil(n_li / ncols))
    # [1:-1] margins keep Li off the very edge of the sheet.
    xs = np.linspace(xmin, xmax, ncols + 2)[1:-1]
    ys = np.linspace(ymin, ymax, nrows + 2)[1:-1]

    li_positions = []
    for y in ys:
        for x in xs:
            if len(li_positions) < n_li:
                li_positions.append((x, y, z_li))

    li = Atoms("Li" * n_li, positions=li_positions)

    combined = sheet + li
    combined.set_cell(sheet.get_cell())
    combined.set_pbc(sheet.get_pbc())
    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Build a pristine graphene sheet with Li atoms above it (Phase 2)."
    )
    parser.add_argument("--nx", type=int, default=DEFAULT_NX,
                        help=f"orthogonal graphene cells along x (default: {DEFAULT_NX})")
    parser.add_argument("--ny", type=int, default=DEFAULT_NY,
                        help=f"orthogonal graphene cells along y (default: {DEFAULT_NY})")
    parser.add_argument("--n-li", type=int, default=DEFAULT_N_LI,
                        help=f"number of Li atoms above the sheet (default: {DEFAULT_N_LI})")
    args = parser.parse_args()

    out_dir = os.path.dirname(os.path.abspath(__file__))
    xyz_path = os.path.join(out_dir, "graphene_li.xyz")
    data_path = os.path.join(out_dir, "graphene_li.data")

    # 1. Pristine orthogonal graphene (no defects).
    sheet = build_orthogonal_graphene(args.nx, args.ny)
    n_carbon = len(sheet)

    # 2. Add lithium above it at the documented starting height.
    structure = add_lithium(sheet, args.n_li)
    n_li = len(structure) - n_carbon

    # 3. Apply the documented z-vacuum: VACUUM/2 of empty space on each side in z
    #    (total VACUUM). Only z is padded; the in-plane graphene cell is untouched.
    structure.center(vacuum=VACUUM / 2.0, axis=2)

    # 4. Export. extxyz keeps elements AND the cell in the .xyz; LAMMPS data uses
    #    atom_style atomic + a Masses block; specorder fixes type 1 = C, 2 = Li.
    write(xyz_path, structure, format="extxyz")
    write(data_path, structure, format="lammps-data",
          atom_style="atomic", specorder=["C", "Li"], masses=True)

    # 5. Factual summary (counts + box only; no physics).
    cell = structure.get_cell().lengths()
    print("Built pristine graphene + Li initial structure (Phase 2):")
    print(f"  orthogonal cells : {args.nx} x {args.ny}")
    print(f"  carbon atoms     : {n_carbon}   (Chou & Hwang [1] precedent: 48)")
    print(f"  lithium atoms    : {n_li}   (documented project choice)")
    print(f"  total atoms      : {len(structure)}")
    print(f"  lattice const    : {GRAPHENE_A} A  -- Chou & Hwang [1]")
    print(f"  Li height        : {LI_HEIGHT} A above graphene -- Chou & Hwang [1]")
    print(f"  z-vacuum         : {VACUUM} A total -- Qin et al. [2]")
    print(f"  box (A)          : {cell[0]:.4f} x {cell[1]:.4f} x {cell[2]:.4f}")
    print(f"                     (Chou & Hwang [1] sheet: 12.8187 x 9.8680 A^2)")
    print(f"  XYZ              : {xyz_path}")
    print(f"  LAMMPS data      : {data_path}  (type 1 = C, type 2 = Li)")
    print("Next: python analysis/inspect_structure.py")


if __name__ == "__main__":
    main()
