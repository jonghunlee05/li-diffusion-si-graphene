# Phase 5 — Model B (single-vacancy Si-graphene-Li) validation checklist

Phase 5 builds **Model B = Si(111) slab + single-vacancy graphene + Li** and
confirms it **minimizes and equilibrates without collapse**. Model B differs from
Model A (Phase 4) by **exactly one removed central graphene carbon** — nothing
else. No DV5-8-5, no production MD, no MSD/diffusion, no conclusions.

Reference numbers (verified run):
69 atoms (48 Si + 17 C + 4 Li); box 7.401 × 7.401 × 40.330 Å (= Model A).
Removed C: Model A index 9 / LAMMPS id 10, at (2.467, 2.849, 20.030) Å.

> **Li loading revised 9 → 4 on 2026-06-16.** Structures, logs, and the numbers
> below were regenerated from the 4-Li build and re-derived from the current 4-Li
> files (`inspect_model_b.py`, `check_model_b_logs.py`).

---

- [x] **Model B generated** — `python structures/build_model_b_sv.py` →
  `structures/model_b_sv.{xyz,data}` + `model_b_sv_metadata.json`.
- [x] **One central C atom removed** — single vacancy (SV); built by importing
  Model A's exact builder and deleting one C (Si et al. [6]; methodology Sec. 5,
  Qin [2]).
- [x] **Removed C ID/index recorded** — index 9 (Model A LAMMPS id 10) in metadata.
- [x] **Removed C coordinates recorded** — (2.467, 2.849, 20.030) Å in metadata.
- [x] **Model A/B comparison passed** —
  `python analysis/compare_model_a_b_structures.py` → `RESULT: PASS`.
- [x] **Si count same as Model A** — 48 = 48.
- [x] **Li count same as Model A** — 4 = 4.
- [x] **C count = Model A − 1** — 17 = 18 − 1.
- [x] **Box dimensions same as Model A** — 7.401 × 7.401 × 40.330 Å.
- [ ] **Structure opens in OVITO** — open `structures/model_b_sv.xyz`; confirm the
  vacancy (one missing C in the sheet).
- [x] **Minimization completed** —
  `lmp_serial -in lammps_inputs/in.model_b_minimize`; `Total wall time`;
  wrote `structures/model_b_sv_minimized.data`. TotEng −7061.48 → −7183.81; no NaN;
  dangerous=0.
- [ ] **Minimized structure opens in OVITO** — `structures/model_b_sv_minimized.data`.
- [x] **Short equilibration completed** —
  `lmp_serial -in lammps_inputs/in.model_b_equilibrate_short`; `Total wall time`;
  wrote `structures/model_b_sv_equilibrated.data`. 500 steps @0.25 fs; final T
  290.2 K; TotEng −7133.74 → −7312.88 (finite, bounded).
- [x] **No atom explosion / collapse** —
  `python analysis/check_model_b_logs.py` → `RESULT: PASS`. Equilibrated geometry
  physical: C–C 1.28 (vacancy reconstruction), Si–Si 2.16, C–Si 2.07,
  Li–C 2.41 Å; no overlaps.
- [ ] **Final screenshot saved** — `figures/phase5_model_b_sv_equilibrated.png`.

---

## Phase 5 validation results (run 2026-06-16)

```
structure      : 69 atoms (48 Si + 17 C + 4 Li); box 7.401 x 7.401 x 40.330 A
differs from A : exactly one removed central graphene C (single vacancy)
removed C      : Model A index 9 / id 10 at (2.467, 2.849, 20.030) A
A/B comparison : RESULT: PASS (Si=, Li=, C=A-1, box=, types=)
mapping        : pair_coeff * * <reaxff> C Si Li   (identical to Model A)
protocol       : ReaxFF/QEq/fix-bottom/timestep/T -- byte-identical to Model A inputs
minimize       : completed; TotEng -7061.48 -> -7183.81; no NaN; dangerous=0
equilibrate    : completed; 500 steps @0.25 fs; final T 290.2 K; energy bounded
collapse?      : NO -- relaxed distances physical (C-C 1.28, Si-Si 2.16, C-Si 2.07)
check_model_b  : RESULT: PASS
OVITO          : PENDING (figures/phase5_model_b_sv_equilibrated.png)
```

**Conclusion:** Model B (single-vacancy Si–graphene–Li) **minimizes and
equilibrates without collapse** — Phase 5 structural validation met (pending OVITO
screenshot). Structural model only; no diffusion/MSD; no comparison conclusions
between A and B drawn yet. Do NOT build DV5-8-5 or run production MD (Phase 6).
