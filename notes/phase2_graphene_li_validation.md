# Phase 2 — graphene + Li validation checklist

Tick each item once its condition is met. Phase 2 is complete when **all** boxes
are checked. Nothing here involves silicon, defects, ReaxFF, MD, or diffusion.

Reference numbers (default parameters, from a verified run):
54 atoms (48 C + 6 Li); box 9.868 × 12.819 × 22.300 Å
(Chou & Hwang [1] 48-C sheet, 12.8187 × 9.8680 Å², axes transposed);
C–C ≈ 1.424 Å; min Li–C ≈ 2.369 Å.

---

- [x] **Build script runs without error**
  - `python structures/build_graphene_li.py`
  - Pass: prints the structure summary; exit code 0.

- [x] **XYZ file created**
  - Pass: `structures/graphene_li.xyz` exists and is non-empty.

- [x] **LAMMPS data file created**
  - Pass: `structures/graphene_li.data` exists and is non-empty, with a
    `Masses` block (type 1 = C, type 2 = Li).

- [x] **Inspection script reports sensible geometry**
  - `python analysis/inspect_structure.py`
  - Pass: 48 C, 6 Li, 54 total; C–C ≈ 1.42 Å; min Li–C ≈ 2.3 Å;
    prints `OK: no obvious overlaps`.

- [x] **Structure opens in OVITO**
  - `File → Load File…` → `structures/graphene_li.xyz` (or the `.data`).
  - Pass: atoms render without error.

- [x] **Graphene appears flat / hexagonal**
  - Pass: viewed from above, the carbon atoms form a regular honeycomb; from the
    side, all carbons lie in one flat plane.

- [x] **Li atoms are above graphene**
  - Pass: from the side, the 6 Li atoms sit in a layer clearly above the carbon
    plane (≈ 2.3–2.4 Å up).

- [x] **No obvious overlaps**
  - Pass: inspector prints `OK` (no `OVERLAP WARNING`); visually, no Li sits on
    top of / inside a carbon.

- [x] **Screenshot saved**
  - Save an OVITO image to
    `figures/phase2_graphene_li_initial_structure.png`.
  - Pass: that PNG exists.

---

## Phase 2 validation completed

**Generated structure:**
- Total atoms: 54
- Carbon atoms: 48
- Lithium atoms: 6
- Box: 9.868 × 12.819 × 22.300 Å
- Minimum Li–C distance: 2.369 Å
- C–C nearest-neighbor distance: 1.424 Å
- OVITO visualization: passed
  (`figures/phase2_graphene_li_initial_structure.png`)
- No obvious overlaps detected

**Conclusion:**
Phase 2 graphene + Li structure generation is validated. This is a preliminary
structure-validation model, **not** a production MD model.

---

## Done when

All boxes above are checked and
`figures/phase2_graphene_li_initial_structure.png` exists. Then Phase 2 is
complete — do **not** proceed to silicon, defects, or MD yet.
