#!/usr/bin/env python3
"""
build_model_b_sv.py  --  Phase 5: Model B (single-vacancy Si-graphene-Li).

Model B is IDENTICAL to Model A (pristine) EXCEPT for ONE graphene single vacancy
(SV): exactly one central carbon atom is removed. Everything else -- Si slab,
graphene dimensions, Li count/placement, box, gap, vacuum, atom-type order -- is
reused unchanged by importing Model A's single-source builder
(structures/build_model_a_pristine.assemble_model_a).

LITERATURE BASIS (SV = remove one C atom):
  - Si et al. [6] (primary): "SV defects are created by removing a C atom."
    Their C counts are 14 (p-Gr) -> 13 (SV): exactly one fewer carbon.
  - Methodology Sec. 5 (defect construction): "Remove one central C atom for SV;
    keep all other variables identical to Model A." (Qin et al. [2])

So Model B carbon count = Model A carbon count - 1 (here 18 -> 17).

SCOPE (Phase 5 only): structural model. NO DV5-8-5, NO production MD, NO
MSD/diffusion, NO scientific conclusions.

Exports:
    structures/model_b_sv.xyz
    structures/model_b_sv.data           (LAMMPS, atom_style charge; 1=C,2=Si,3=Li)
    structures/model_b_sv_metadata.json  (removed-atom record + provenance)

Usage:
    python structures/build_model_b_sv.py
"""

import json
import os

import numpy as np
from ase.io import write

# Single source of truth for the Model A/B geometry.
from build_model_a_pristine import (
    assemble_model_a, DEFAULTS, SPECORDER, min_dist,
)


def find_central_carbon(model):
    """
    Return the index of the carbon nearest the graphene sheet's in-plane
    centroid -- the 'central' C removed to make the single vacancy. Deterministic.
    """
    sym = np.array(model.get_chemical_symbols())
    c_idx = np.where(sym == "C")[0]
    cpos = model.get_positions()[c_idx]
    centroid_xy = cpos[:, :2].mean(axis=0)
    d = np.linalg.norm(cpos[:, :2] - centroid_xy, axis=1)
    return int(c_idx[int(np.argmin(d))])


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    xyz_path = os.path.join(out_dir, "model_b_sv.xyz")
    data_path = os.path.join(out_dir, "model_b_sv.data")
    meta_path = os.path.join(out_dir, "model_b_sv_metadata.json")

    # 1. Rebuild Model A exactly (same construction logic / parameters).
    model, info = assemble_model_a(**DEFAULTS)
    n_c_a = info["n_c"]

    # 2. Identify and remove ONE central carbon -> single vacancy.
    rm = find_central_carbon(model)
    rm_pos = model.get_positions()[rm].tolist()
    rm_symbol = model.get_chemical_symbols()[rm]
    assert rm_symbol == "C", "removed atom must be carbon"

    # Record BEFORE deleting. In the Model A data file, LAMMPS atom IDs are
    # 1..N in build order (C first), so the removed atom's Model A LAMMPS id is
    # (index + 1). After removal Model B is re-numbered 1..N-1.
    removed_record = {
        "index_0based_in_model_a": rm,
        "lammps_id_1based_in_model_a": rm + 1,
        "element": rm_symbol,
        "coordinates_xyz_A": [round(x, 6) for x in rm_pos],
        "selection_criterion": "carbon nearest the graphene in-plane centroid",
    }

    del model[rm]   # create the single vacancy

    # 3. Export structure.
    write(xyz_path, model, format="extxyz")
    write(data_path, model, format="lammps-data",
          atom_style="charge", specorder=SPECORDER, masses=True)

    # 4. Counts + distance summary.
    sym = np.array(model.get_chemical_symbols())
    idx = {e: np.where(sym == e)[0] for e in ("C", "Si", "Li")}
    box = model.get_cell().lengths()
    dists = {
        "Li-C": min_dist(model, idx["Li"], idx["C"]),
        "Li-Si": min_dist(model, idx["Li"], idx["Si"]),
        "C-Si": min_dist(model, idx["C"], idx["Si"]),
        "Si-Si": min_dist(model, idx["Si"], idx["Si"]),
        "C-C": min_dist(model, idx["C"], idx["C"]),
    }

    # 5. Metadata JSON (provenance + the removed-atom record).
    metadata = {
        "model": "B (single-vacancy graphene)",
        "derived_from": "Model A (build_model_a_pristine.assemble_model_a)",
        "differs_from_model_a_by": "one removed central graphene carbon (single vacancy)",
        "build_parameters": DEFAULTS,
        "removed_carbon": removed_record,
        "atom_counts": {
            "C_model_a": n_c_a,
            "C_model_b": int(len(idx["C"])),
            "C_difference": n_c_a - int(len(idx["C"])),
            "Si": int(len(idx["Si"])),
            "Li": int(len(idx["Li"])),
            "total": int(len(model)),
        },
        "box_A": [round(b, 6) for b in box],
        "type_order": SPECORDER,
        "literature_basis": (
            "SV = remove one C atom (Si et al. [6], 'SV defects are created by "
            "removing a C atom'); methodology Sec. 5 'remove one central C atom "
            "for SV, keep all other variables identical to Model A' (Qin et al. [2])."
        ),
    }
    with open(meta_path, "w") as fh:
        json.dump(metadata, fh, indent=2)

    # 6. Report.
    print("Built Model B (single-vacancy Si-graphene-Li):")
    print(f"  removed C : index {rm} (Model A LAMMPS id {rm + 1}) at "
          f"({rm_pos[0]:.3f}, {rm_pos[1]:.3f}, {rm_pos[2]:.3f}) A")
    print(f"  Si atoms  : {len(idx['Si'])}")
    print(f"  C atoms   : {len(idx['C'])}  (Model A had {n_c_a}; difference 1 = SV)")
    print(f"  Li atoms  : {len(idx['Li'])}")
    print(f"  total     : {len(model)}")
    print(f"  box (A)   : {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    for k in ("Li-C", "Li-Si", "C-Si", "Si-Si", "C-C"):
        v = dists[k]
        print(f"  min {k:6s}: {v:.3f} A" if v is not None else f"  min {k:6s}: n/a")
    print(f"  XYZ      : {xyz_path}")
    print(f"  data     : {data_path}  (type 1=C, 2=Si, 3=Li)")
    print(f"  metadata : {meta_path}")


if __name__ == "__main__":
    main()
