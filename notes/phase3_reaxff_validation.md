# Phase 3 — ReaxFF / QEq validation checklist

Phase 3 confirms the **Li–Si–C ReaxFF force-field setup works in LAMMPS** before
any real Si–graphene model is built. It is a smoke test only: no production MD,
no MSD/diffusion, no Model A/B.

Tick each item once met. Phase 3 is complete when **all** boxes are checked.

> ReaxFF file added and smoke test passed — see `force_fields/README.md` for the
> file provenance and the verified header correction.

---

- [x] **Actual ReaxFF file added**
  - `force_fields/ffield.reax.LiSiC_OlououGuifo2023.txt` (Olou'ou Guifo et al.
    2023, NOT invented). `variable REAXFF_FILE` points to it.
  - NOTE: a verified metadata-only header correction was required (stale section
    counts + a no-H h-bond entry); parameter values unchanged and confirmed
    complete against the paper SI. See `force_fields/README.md`.

- [x] **Atom order confirmed**
  - File internal order is Li, Si, C (recorded in `force_fields/README.md`); all
    three labels present.

- [x] **pair_coeff mapping confirmed**
  - Data file type order (1=C, 2=Si, 3=Li) matches `pair_coeff * * <file> C Si Li`.

- [x] **LAMMPS run completed**
  - `lmp_serial -in lammps_inputs/in.reaxff_smoke_test` finished; log ends with
    `Total wall time`.

- [x] **QEq ran without unresolved warnings**
  - `fix qeq/reaxff` ran; no convergence/maxiter warnings.

- [x] **Charges finite**
  - No `NaN`/`Inf`; energies finite/bounded.
  - `python analysis/check_reaxff_log.py` prints `RESULT: PASS`.

- [ ] **No atom explosion in OVITO**
  - Open `trajectories/reaxff_smoke_test.lammpstrj`; confirm the cluster stays
    compact. (Inspector already shows final coord spread ~4×1.4×5.3 Å — compact.)

- [x] **Log and dump saved**
  - `logs/reaxff_smoke_test.log` and
    `trajectories/reaxff_smoke_test.lammpstrj` exist and are non-empty.

- [ ] **Screenshot saved**
  - Save an OVITO image to `figures/phase3_reaxff_smoke_test.png`.

---

## Phase 3 validation results (run 2026-06-15)

```
ReaxFF file        : force_fields/ffield.reax.LiSiC_OlououGuifo2023.txt
                     (header counts corrected; values verified vs paper SI)
mapping            : pair_coeff * * <file> C Si Li   (type 1=C, 2=Si, 3=Li)
run completed      : YES (Total wall time present)
QEq warnings       : none
NaN/Inf            : none
final temperature  : 223.7 K  (NVT block; noisy for a 6-atom/25 fs run -- expected)
energy behavior    : finite & bounded (minimize -186 -> -358; NVT -357 -> -362)
atoms compact      : YES (final coord spread ~4 x 1.4 x 5.3 A; no explosion)
check_reaxff_log   : RESULT: PASS
OVITO screenshot   : PENDING (figures/phase3_reaxff_smoke_test.png)
```

**Conclusion:** the Li–Si–C ReaxFF/QEq setup **loads, maps, equilibrates charge,
and runs stably** in LAMMPS. Phase 3 is validated pending the OVITO screenshot.
This is a force-field smoke test, **not** a production MD model.

---

## Done when

All boxes checked and `figures/phase3_reaxff_smoke_test.png` exists. Then Phase 3
is complete — do **not** build Model A/B or run production MD yet.
