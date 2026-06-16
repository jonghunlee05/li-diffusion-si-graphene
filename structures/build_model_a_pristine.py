#!/usr/bin/env python3
"""
build_model_a_pristine.py  --  Phase 4: Model A (pristine Si-graphene-Li).

Builds the FIRST real interface model: a Si(111) slab + a PRISTINE graphene
sheet + Li, in one periodic cell, ready for ReaxFF minimization/equilibration.

SCOPE (Phase 4 only):
  - Pristine graphene -- NO vacancy, NO defects (that is Phase 5 / Model B).
  - Structural model only. NO production MD, NO MSD/diffusion here.
  - Pass condition (elsewhere): the model minimizes & equilibrates w/o collapse.

------------------------------------------------------------------------------
PARAMETER PROVENANCE (methodology doc + cited papers):

  Si slab orientation = Si(111)
        Qin et al. [2] (methodology Sec. 5): defect benchmark uses Gr/Si on Si(111).
  Si lattice constant = 5.431 A
        Standard experimental diamond-Si value (not specified by the methodology;
        used to build the slab geometry -- not a fitted/invented parameter).
  graphene lattice    = 2.467 A
        Chou & Hwang [1] (kept at the literature value; Si is strained instead).
  in-plane match      = graphene 3x3 hex (18 C) on Si(111) 2x2 hex.
        "Use a model commensurate with graphene" (methodology Sec. 5, Qin [2]).
        Si is compressed in-plane to the graphene cell (~ -3.6%), consistent with
        the methodology note that Si-Si is "adjusted approx. 4% for mismatch".
        Slab size is a documented project choice (precedent: 4x4 / two double
        layers [2], or 10 layers [9]); kept small here for ReaxFF cost.
  Si-graphene gap     = 2.0 A (initial, before relaxation)
        Chou & Hwang [1] (methodology Sec. 5: "start at approx. 2 A").
  Li starting height  = 2.3 A above graphene
        Chou & Hwang [1] interface-layer Li-Gr distance (methodology Sec. 5).
  Li count            = documented PROJECT CHOICE (methodology: Li loading is a
        project choice). A small layer above graphene is used for an overlap-free
        structural model; interface placement is a future refinement (see NOTE).
  z-vacuum            = 18.0 A
        Qin et al. [2] (methodology Sec. 5: >=18 A slab vacuum for periodic-z).

FORCED DEVIATIONS (documented):
  * NO hydrogen passivation. Qin et al. passivate bottom Si dangling bonds with
    H, but the Olou'ou Guifo et al. [4] Li-Si-C ReaxFF has NO hydrogen. Instead,
    the bottom Si layer is FIXED during MD (done in the LAMMPS input, not here).
  * Li is placed ABOVE the graphene (vacuum side), the methodology-permitted
    "near/above the graphene" option. This is overlap-safe for a structural
    model; burying Li at the Si-graphene interface is deferred.

No defects, no random manual edits, no invented force-field parameters.
------------------------------------------------------------------------------

Exports:
    structures/model_a_pristine.xyz    (extended-XYZ; OVITO-friendly)
    structures/model_a_pristine.data   (LAMMPS data, atom_style charge, w/ Masses)

Type order (matches Phase 3): type 1 = C, type 2 = Si, type 3 = Li
-> LAMMPS: pair_coeff * * <reaxff file> C Si Li

Usage:
    python structures/build_model_a_pristine.py
    python structures/build_model_a_pristine.py --si-layers 6 --n-li 9
"""

import argparse
import os

import numpy as np
from ase import Atoms
from ase.build import graphene, surface, bulk
from ase.io import write


# --- Provenance-tagged parameters -------------------------------------
A_C = 2.467        # A, graphene lattice -- Chou & Hwang [1]
A_SI = 5.431       # A, Si lattice constant -- standard experimental value
GAP_SI_GR = 2.0    # A, initial Si-graphene separation -- Chou & Hwang [1]
LI_HEIGHT = 2.3    # A, Li starting height above graphene -- Chou & Hwang [1]
VACUUM = 18.0      # A, z-vacuum above the slab -- Qin et al. [2]

SPECORDER = ["C", "Si", "Li"]   # type 1=C, 2=Si, 3=Li (consistent with Phase 3)
MIN_OK = 1.0       # A, below this any pair is treated as an overlap (warn)


def build_graphene_hex(nx, ny):
    """Pristine graphene on a hexagonal cell, nx x ny primitive cells."""
    g = graphene(a=A_C, size=(nx, ny, 1), vacuum=0.0)
    g.set_pbc([True, True, True])
    return g


def build_si111_slab(nlayers, nx, ny):
    """
    Si(111) slab, nlayers atomic layers, repeated nx x ny in-plane (hexagonal).
    Returns the slab with NO vacuum (z handled later).
    """
    si = bulk("Si", "diamond", a=A_SI, cubic=False)
    slab = surface(si, (1, 1, 1), layers=nlayers, vacuum=0.0)
    slab = slab.repeat((nx, ny, 1))
    slab.set_pbc([True, True, True])
    return slab


def strain_inplane_to(slab, target_cell):
    """
    Strain ONLY the in-plane (x, y) coordinates of the slab so its in-plane cell
    matches `target_cell` (graphene's a1, a2). The z coordinates are left exactly
    as built, so the slab stays flat (no shear from the slab's tilted c-vector).
    Both cells are hexagonal, so this is a near-uniform in-plane strain (the
    documented Si mismatch adjustment). Returns (strained_slab, percent_strain).
    """
    a_before = np.linalg.norm(slab.cell[0])

    # The Si(111) surface cell and graphene may use different hexagonal cell
    # conventions (60 deg vs 120 deg). Re-express the slab's a2 (a2 or a2 - a1)
    # so its angle to a1 matches graphene's -- WITHOUT moving any atom -- so the
    # strain map below is a clean uniform scale, not a shear.
    def angle(u, v):
        u, v = u[:2], v[:2]
        return np.degrees(np.arccos(np.clip(
            np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1)))

    a1s, a2s = slab.cell[0], slab.cell[1]
    target_ang = angle(target_cell[0], target_cell[1])
    a2_fixed = min([a2s, a2s - a1s, a2s + a1s, a1s - a2s],
                   key=lambda c: abs(angle(a1s, c) - target_ang))
    fixed = slab.cell.copy()
    fixed[1] = a2_fixed
    slab.set_cell(fixed)                          # redefine a2 only; atoms unchanged

    # 2x2 in-plane (xy) bases as columns.
    S = np.array([slab.cell[0][:2], slab.cell[1][:2]]).T
    G = np.array([target_cell[0][:2], target_cell[1][:2]]).T
    M = G @ np.linalg.inv(S)                      # maps slab xy -> graphene xy

    pos = slab.get_positions()
    pos[:, :2] = (M @ pos[:, :2].T).T             # transform x, y; keep z
    slab.set_positions(pos)

    new_cell = slab.cell.copy()
    new_cell[0] = target_cell[0]
    new_cell[1] = target_cell[1]
    slab.set_cell(new_cell)                       # scale_atoms=False: keep xy as set
    a_after = np.linalg.norm(slab.cell[0])
    pct = 100.0 * (a_after - a_before) / a_before
    return slab, pct


def place_lithium(xy_cell, z_li, n_li):
    """Place n_li Li on a grid in the (a1,a2) cell at height z_li (Cartesian z)."""
    ncols = int(np.ceil(np.sqrt(n_li)))
    nrows = int(np.ceil(n_li / ncols))
    a1, a2 = xy_cell[0], xy_cell[1]
    pos = []
    for i in range(nrows):
        for j in range(ncols):
            if len(pos) < n_li:
                # fractional offsets inside the cell, with a margin from edges
                fa = (i + 0.5) / nrows
                fb = (j + 0.5) / ncols
                p = fa * a1 + fb * a2
                pos.append((p[0], p[1], z_li))
    return Atoms("Li" * n_li, positions=pos)


def min_dist(atoms, idx_a, idx_b):
    """
    Minimum periodic-aware distance between two index groups (A). When the two
    groups overlap (e.g. Si-Si), self-pairs (distance 0) are excluded.
    """
    if len(idx_a) == 0 or len(idx_b) == 0:
        return None
    best = np.inf
    for i in idx_a:
        targets = [j for j in idx_b if j != i]   # exclude self
        if not targets:
            continue
        d = atoms.get_distances(i, targets, mic=True)
        best = min(best, float(np.min(d)))
    return best if np.isfinite(best) else None


# Shared default build parameters (so Model B can reuse EXACTLY Model A's build).
DEFAULTS = dict(gx=3, gy=3, si_nx=2, si_ny=2, si_layers=6, n_li=9)


def assemble_model_a(gx=3, gy=3, si_nx=2, si_ny=2, si_layers=6, n_li=9):
    """
    Assemble the Model A structure (pristine Si-graphene-Li) and return
    (model, info_dict). This is the SINGLE SOURCE OF TRUTH for the Model A/B
    geometry: Model B (Phase 5) imports this and removes one C, guaranteeing the
    two models differ ONLY by the vacancy. Atom order: C (graphene), then Si
    (slab), then Li.
    """
    # 1. Pristine graphene (defines the common in-plane cell).
    g = build_graphene_hex(gx, gy)
    n_c = len(g)

    # 2. Si(111) slab, then strain its in-plane cell to the graphene cell.
    slab = build_si111_slab(si_layers, si_nx, si_ny)
    slab, strain_pct = strain_inplane_to(slab, g.cell)
    n_si = len(slab)

    # 3. Stack along z: Si slab at the bottom, graphene GAP above the top Si,
    #    Li LI_HEIGHT above graphene.
    slab.translate((0, 0, -slab.get_positions()[:, 2].min()))   # bottom Si at z=0
    si_top = slab.get_positions()[:, 2].max()

    gpos = g.get_positions()
    gpos[:, 2] -= gpos[:, 2].mean()           # zero graphene's own z-offset
    z_graphene = si_top + GAP_SI_GR
    gpos[:, 2] += z_graphene
    g.set_positions(gpos)

    z_li = z_graphene + LI_HEIGHT
    li = place_lithium(g.cell, z_li, n_li)

    # 4. Combine (carbons, then Si, then Li) in graphene's in-plane cell.
    model = g + slab + li
    cell = g.cell.copy()
    cell[2] = (0.0, 0.0, z_li + VACUUM)
    model.set_cell(cell)
    model.set_pbc([True, True, True])

    info = dict(n_c=n_c, n_si=n_si, n_li=len(li), strain_pct=strain_pct,
                z_graphene=z_graphene, gap=GAP_SI_GR, si_top=si_top)
    return model, info


def main():
    ap = argparse.ArgumentParser(description="Build Model A: pristine Si-graphene-Li.")
    ap.add_argument("--gx", type=int, default=3, help="graphene cells along a1 (default 3)")
    ap.add_argument("--gy", type=int, default=3, help="graphene cells along a2 (default 3)")
    ap.add_argument("--si-nx", type=int, default=2, help="Si(111) cells along a1 (default 2)")
    ap.add_argument("--si-ny", type=int, default=2, help="Si(111) cells along a2 (default 2)")
    ap.add_argument("--si-layers", type=int, default=6,
                    help="Si(111) atomic layers (default 6; project choice)")
    ap.add_argument("--n-li", type=int, default=9,
                    help="number of Li atoms above graphene (default 9; project choice)")
    args = ap.parse_args()

    out_dir = os.path.dirname(os.path.abspath(__file__))
    xyz_path = os.path.join(out_dir, "model_a_pristine.xyz")
    data_path = os.path.join(out_dir, "model_a_pristine.data")

    # Assemble via the shared single-source builder (also used by Model B).
    model, info = assemble_model_a(gx=args.gx, gy=args.gy,
                                   si_nx=args.si_nx, si_ny=args.si_ny,
                                   si_layers=args.si_layers, n_li=args.n_li)
    n_c, n_si, n_li, strain_pct = info["n_c"], info["n_si"], info["n_li"], info["strain_pct"]

    # 5. Export.
    write(xyz_path, model, format="extxyz")
    write(data_path, model, format="lammps-data",
          atom_style="charge", specorder=SPECORDER, masses=True)

    # 6. Geometry summary + distance sanity checks.
    sym = np.array(model.get_chemical_symbols())
    c_idx = np.where(sym == "C")[0]
    si_idx = np.where(sym == "Si")[0]
    li_idx = np.where(sym == "Li")[0]
    box = model.get_cell().lengths()

    d_li_c = min_dist(model, li_idx, c_idx)
    d_li_si = min_dist(model, li_idx, si_idx)
    d_c_si = min_dist(model, c_idx, si_idx)
    d_si_si = min_dist(model, si_idx, si_idx)
    d_c_c = min_dist(model, c_idx, c_idx)

    print("Built Model A (pristine Si-graphene-Li):")
    print(f"  Si atoms        : {n_si}")
    print(f"  C atoms         : {n_c}  (pristine graphene, no defects)")
    print(f"  Li atoms        : {n_li}  (documented project choice)")
    print(f"  total atoms     : {len(model)}")
    print(f"  box (A)         : {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    print(f"  Si in-plane strain to graphene : {strain_pct:+.2f}%  "
          f"(methodology: ~4% mismatch adjustment)")
    print(f"  initial Si-graphene gap        : {GAP_SI_GR:.2f} A  (Chou & Hwang [1])")
    print(f"  min Li-C distance : {d_li_c:.3f} A" if d_li_c else "  min Li-C : n/a")
    print(f"  min Li-Si distance: {d_li_si:.3f} A" if d_li_si else "  min Li-Si: n/a")
    print(f"  min C-Si distance : {d_c_si:.3f} A" if d_c_si else "  min C-Si : n/a")
    print(f"  min Si-Si distance: {d_si_si:.3f} A  (ideal Si ~2.35 A, strained)" if d_si_si else "")
    print(f"  min C-C distance  : {d_c_c:.3f} A  (ideal graphene ~1.42 A)" if d_c_c else "")

    warnings = [(n, d) for n, d in
                [("Li-C", d_li_c), ("Li-Si", d_li_si), ("C-Si", d_c_si),
                 ("Si-Si", d_si_si), ("C-C", d_c_c)]
                if d is not None and d < MIN_OK]
    if warnings:
        print("  WARNING: unphysically short distances:")
        for n, d in warnings:
            print(f"    - {n}: {d:.3f} A < {MIN_OK} A")
    else:
        print("  OK: no unphysically short distances.")

    print(f"  XYZ  : {xyz_path}")
    print(f"  data : {data_path}  (type 1=C, 2=Si, 3=Li)")


if __name__ == "__main__":
    main()
