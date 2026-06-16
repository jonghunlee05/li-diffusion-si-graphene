# Phase 6 — Production MD validation checklist

Production NVT MD for **Model A (pristine)** and **Model B (single-vacancy)** with
identical settings, producing trajectories for Phase 7 MSD/diffusion. **No MSD, no
diffusion coefficients, no conclusions here.**

**Permeation design:** Li start **above** graphene; a reflecting z-wall (35 Å)
keeps them in the system so the MSD is valid; the graphene COM-z is pinned so the
membrane stays the barrier (Li can still cross it). Settings:
`docs/phase6_production_settings.md`.

---

> **All items verified (2026-06-16).** Log/data/figure items from the logs,
> trajectory analysis, and produced figures (constant-1200 K production + 8-stage
> ramp; see results section); OVITO visual items (graphene-on-Si, trajectories
> open, no explosion) confirmed interactively, snapshots saved.

- [x] **Model A production run completed** — `in.model_a_production` (PASS) **and** the 4-stage ramp.
- [x] **Model B production run completed** — `in.model_b_production` (PASS) **and** the 4-stage ramp.
- [x] **Same protocol used for both models** — inputs byte-identical except paths;
  `check_production_logs.py` → `RESULT: PASS`, same timestep (0.25 fs). (A-vs-B
  2nd-half mobile-T differs in the constant run as a `WARN` — thermal fluctuation,
  not a protocol difference; the ramp matches per-stage within ~12 K.)
- [x] **No NaN values** — both production logs (checker) and all 8 ramp logs.
- [x] **No unresolved QEq failure** — both production logs and all 8 ramp logs.
- [x] **No temperature blow-up** — mobile T bounded near setpoint at every stage.
- [x] **No energy divergence** — total energy finite/bounded throughout.
- [x] **Li contained (no evaporation)** — max Li z **27.3 Å** (ramp) / below wall in
  production; 35 Å wall never reached; none escape.
- [x] **Graphene stays on Si** — membrane anchored (COM-z pinned); confirmed in OVITO (not desorbed).
- [x] **Model A trajectory opens in OVITO** (wrap on) — `trajectories/model_a_production.lammpstrj`.
- [x] **Model B trajectory opens in OVITO** (wrap on) — `trajectories/model_b_production.lammpstrj`.
- [x] **No atom explosion/collapse observed** — structure intact in OVITO.
- [x] **Figures saved:**
  - [x] `figures/phase6_model_a_production_snapshot.png`
  - [x] `figures/phase6_model_b_production_snapshot.png`
  - [x] `figures/phase6_temperature_energy_model_a.png` (+ `..._model_a_ramp.png`)
  - [x] `figures/phase6_temperature_energy_model_b.png` (+ `..._model_b_ramp.png`)

---

## Phase 6 validation results (run 2026-06-16)

Phase 6 was run as a **staged temperature ramp** (`in.production_ramp`): one
parameterized NVT stage at each of **300 → 600 → 900 → 1200 K**, ~10 ps each
(40,000 × 0.25 fs), continuous heat-up (each stage reads the previous stage's
`*_final.data`). Byte-identical physics for both models — only `MODEL`, `INDATA`,
`TSTAGE`, and `STAGE` differ. Plots: `analysis/plot_temperature_energy_ramp.py`.

**Per-stage thermostat / energy / containment** (mobile T = 2nd-half mean of
`c_ctemp`; energy bounded over the whole stage; max Li `zu` over the stage, wall
at 35 Å; DT = 0.25 fs for all stages; QEq converged, no failures):

| Model | Stage | mobile T (2nd half) | total E range (kcal/mol) | max Li z (Å) | NaN/Inf | wall time |
|-------|-------|---------------------|--------------------------|--------------|---------|-----------|
| A | 300 K  |  300.1 K | [−7764.7, −7446.0] | 24.95 | none | 0:06:07 |
| A | 600 K  |  602.0 K | [−7755.1, −7598.0] | 26.58 | none | 0:05:47 |
| A | 900 K  |  898.2 K | [−7631.7, −7449.3] | 25.85 | none | 0:06:11 |
| A | 1200 K | 1188.1 K | [−7536.1, −7336.7] | 27.30 | none | 0:06:12 |
| B | 300 K  |  301.0 K | [−7427.8, −7312.9] | 25.03 | none | 0:06:21 |
| B | 600 K  |  607.8 K | [−7414.0, −7265.7] | 25.60 | none | 0:06:01 |
| B | 900 K  |  895.4 K | [−7383.5, −7189.9] | 25.57 | none | 0:06:11 |
| B | 1200 K | 1202.1 K | [−7359.0, −7096.0] | 27.17 | none | 0:06:14 |

- **Completion:** all 8 stages exited 0, wrote `structures/model_{a,b}_ramp_{T}K_final.data`.
- **Thermostat:** mobile T tracks each setpoint within ~12 K (worst case A@1200 K = 1188 K).
- **No blow-up / divergence:** total energy finite and bounded at every stage; no NaN/Inf; no QEq failure.
- **Li containment:** highest Li ever reached **27.30 Å** (A@1200 K) vs the 35 Å wall —
  **zero** Li reached the wall at any temperature; **none evaporated**. The reflecting
  wall never had to act.
- **Graphene anchor:** COM-z pinned (`fix recenter`); membrane stayed on the Si (no desorption).
- **Same protocol A vs B:** identical input/timestep/thermostat/wall/force field — only paths + `TSTAGE` differ.

> Visualization note: trajectories use **unwrapped** coords (`xu yu zu`) for Phase 7
> MSD, so lateral Li diffusion looks like atoms leaving the box in OVITO. Enable
> **"Wrap at periodic boundaries"**; z (the permeation axis) is steady at ~23.5 Å.

**Conclusion:** the staged-ramp production runs are stable, comparable trajectories
suitable for Phase 7, with Li contained above graphene and the membrane intact at
all four temperatures. Phase 6 makes **no** diffusion claim. Do NOT compute
MSD/diffusion or draw A-vs-B conclusions until Phase 7. The MSD fitting window is a
project-discovered value chosen only after seeing Phase 7 data.
