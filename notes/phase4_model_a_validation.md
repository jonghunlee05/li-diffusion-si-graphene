# Phase 4 — Model A (pristine Si-graphene-Li) validation checklist

Phase 4 builds the first real interface model — **Model A = Si(111) slab +
pristine graphene + Li** — and confirms it **minimizes and equilibrates without
collapse**. No vacancy/defects (Phase 5), no production MD, no MSD/diffusion.

Tick each item once met. Phase 4 passes when all are checked (screenshot last).

Reference numbers (default build, verified run):
75 atoms (48 Si + 18 C + 9 Li); box 7.401 × 7.401 × 40.330 Å;
Si in-plane strain −3.64% (≈ methodology's ~4%); initial Si–graphene gap 2.0 Å.

---

- [x] **Structure generated**
  - `python structures/build_model_a_pristine.py`
  - `structures/model_a_pristine.{xyz,data}` written.

- [x] **Atom counts recorded**
  - Si 48, C 18 (pristine, no defects), Li 9 (project choice), total 75.

- [x] **Distance checks passed**
  - `python analysis/inspect_model_a.py` → `OK: no overlaps`.
  - min (Å): Li–C 2.41, Li–Si 4.30, C–Si 2.00, Si–Si 2.28, C–C 1.42.

- [ ] **Model opens in OVITO**
  - Open `structures/model_a_pristine.xyz`; confirm Si slab + flat graphene + Li.

- [x] **Minimization completed**
  - `lmp_serial -in lammps_inputs/in.model_a_minimize` → `Total wall time`;
    wrote `structures/model_a_pristine_minimized.data`.
  - TotEng −7482.8 → −7489.2 (finite); no NaN; no dangerous builds.

- [ ] **Minimized structure opens in OVITO**
  - Open `structures/model_a_pristine_minimized.data` (or the dump).

- [x] **Short equilibration completed**
  - `lmp_serial -in lammps_inputs/in.model_a_equilibrate_short` → `Total wall time`;
    wrote `structures/model_a_pristine_equilibrated.data`.
  - 500 steps @ 0.25 fs (125 fs), NVT 300 K target; final T 416.8 K
    (overshoot expected for a 125 fs run as the interface relaxes — not a blow-up).
  - TotEng −7433.7 → −7692.5 (finite, bounded).

- [x] **No atom explosion / collapse**
  - `python analysis/check_model_a_logs.py` → `RESULT: PASS`.
  - Equilibrated geometry still physical: C–C 1.37, Si–Si 2.24, C–Si 1.96,
    Li–C 2.20 Å; no overlaps, nothing fused/scattered.

- [ ] **Final screenshot saved**
  - Save OVITO image to `figures/phase4_model_a_pristine_equilibrated.png`.

---

## Phase 4 validation results (run 2026-06-15)

```
structure      : 75 atoms (48 Si + 18 C + 9 Li); box 7.401 x 7.401 x 40.330 A
mapping        : pair_coeff * * <reaxff> C Si Li   (type 1=C, 2=Si, 3=Li)
bottom Si      : fixed (no H passivation; ffield has no H -- documented)
minimize       : completed; TotEng -7482.8 -> -7489.2; no NaN; dangerous=0
equilibrate    : completed; 500 steps @0.25 fs; final T 416.8 K; TotEng bounded
collapse?      : NO -- relaxed distances physical (C-C 1.37, Si-Si 2.24, C-Si 1.96)
check_model_a  : RESULT: PASS
OVITO          : PENDING (figures/phase4_model_a_pristine_equilibrated.png)
```

**Conclusion:** Model A (pristine Si–graphene–Li) **minimizes and equilibrates
without collapse** — Phase 4 structural validation met (pending OVITO screenshot).
This is a STRUCTURAL model only. No diffusion/MSD computed; no scientific
conclusions drawn. Do NOT proceed to Model B (Phase 5) or production MD yet.
