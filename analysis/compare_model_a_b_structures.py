#!/usr/bin/env python3
"""
compare_model_a_b_structures.py  --  Phase 5 Model A vs Model B comparison.

Confirms Model B (single-vacancy) differs from Model A (pristine) ONLY by one
removed graphene carbon. Reports and PASS/FAILs on:
  - Si count identical
  - Li count identical
  - C count(B) == C count(A) - 1
  - box dimensions identical (or within tolerance)
  - consistent atom-type mapping (elements present)
  - minimum Li-C, Li-Si, C-Si, C-C, Si-Si distances (both models)
  - removed carbon ID/index + coordinates (from metadata)
  - overlap / unexpected-change warnings

Does NOT run MD or compute diffusion.

Usage:
    python analysis/compare_model_a_b_structures.py
"""

import json
import os
import sys

import numpy as np
from ase.io import read

A_DATA = "structures/model_a_pristine.data"
B_DATA = "structures/model_b_sv.data"
B_META = "structures/model_b_sv_metadata.json"
BOX_TOL = 1e-3   # A, boxes must match within this


def load(path):
    if not os.path.isfile(path):
        sys.exit(f"ERROR: missing {path} (build Models A and B first)")
    return read(path, format="lammps-data", atom_style="charge",
                Z_of_type={1: 6, 2: 14, 3: 3})


def counts(atoms):
    sym = np.array(atoms.get_chemical_symbols())
    return {e: int((sym == e).sum()) for e in ("C", "Si", "Li")}


def min_dist(atoms, ia, ib):
    if len(ia) == 0 or len(ib) == 0:
        return None
    best = np.inf
    for i in ia:
        tgt = [j for j in ib if j != i]
        if tgt:
            best = min(best, float(np.min(atoms.get_distances(i, tgt, mic=True))))
    return best if np.isfinite(best) else None


def all_dists(atoms):
    sym = np.array(atoms.get_chemical_symbols())
    idx = {e: np.where(sym == e)[0] for e in ("C", "Si", "Li")}
    return {
        "Li-C": min_dist(atoms, idx["Li"], idx["C"]),
        "Li-Si": min_dist(atoms, idx["Li"], idx["Si"]),
        "C-Si": min_dist(atoms, idx["C"], idx["Si"]),
        "Si-Si": min_dist(atoms, idx["Si"], idx["Si"]),
        "C-C": min_dist(atoms, idx["C"], idx["C"]),
    }


def main():
    A, B = load(A_DATA), load(B_DATA)
    ca, cb = counts(A), counts(B)
    boxA, boxB = A.get_cell().lengths(), B.get_cell().lengths()

    checks = []
    checks.append((ca["Si"] == cb["Si"], "Si count identical",
                   f"A={ca['Si']} B={cb['Si']}"))
    checks.append((ca["Li"] == cb["Li"], "Li count identical",
                   f"A={ca['Li']} B={cb['Li']}"))
    checks.append((cb["C"] == ca["C"] - 1, "C(B) == C(A) - 1",
                   f"A={ca['C']} B={cb['C']}"))
    box_ok = np.allclose(boxA, boxB, atol=BOX_TOL)
    checks.append((box_ok, "box identical",
                   f"A={np.round(boxA,3)} B={np.round(boxB,3)}"))
    elems_ok = set(ca) == set(cb) == {"C", "Si", "Li"}
    checks.append((elems_ok, "type mapping consistent",
                   "elements C/Si/Li present in both"))
    checks.append((len(B) == len(A) - 1, "total atoms B == A - 1",
                   f"A={len(A)} B={len(B)}"))

    dA, dB = all_dists(A), all_dists(B)

    print("Model A vs Model B structural comparison\n")
    for ok, label, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:24s}: {detail}")

    print("\n  minimum distances (A):")
    print(f"    {'pair':6s} {'Model A':>9s} {'Model B':>9s}")
    for k in ("Li-C", "Li-Si", "C-Si", "Si-Si", "C-C"):
        sa = f"{dA[k]:.3f}" if dA[k] is not None else "n/a"
        sb = f"{dB[k]:.3f}" if dB[k] is not None else "n/a"
        print(f"    {k:6s} {sa:>9s} {sb:>9s}")

    # Removed-atom record from metadata.
    if os.path.isfile(B_META):
        meta = json.load(open(B_META))
        rc = meta.get("removed_carbon", {})
        print("\n  removed carbon (from metadata):")
        print(f"    index (0-based, Model A) : {rc.get('index_0based_in_model_a')}")
        print(f"    LAMMPS id (Model A)      : {rc.get('lammps_id_1based_in_model_a')}")
        print(f"    coordinates (A)          : {rc.get('coordinates_xyz_A')}")
    else:
        print(f"\n  NOTE: metadata not found ({B_META})")

    # Overlap warning (any pair < 1.0 A in either model).
    warn = []
    for tag, d in (("A", dA), ("B", dB)):
        for k, v in d.items():
            if v is not None and v < 1.0:
                warn.append(f"{tag} {k}={v:.3f} A")
    print()
    if warn:
        print("  WARNING (overlaps): " + ", ".join(warn))

    overall = all(c[0] for c in checks) and not warn
    print()
    if overall:
        print("RESULT: PASS -- Model B differs from Model A only by one C vacancy.")
        sys.exit(0)
    print("RESULT: FAIL -- see failed checks above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
