# Phase 6 — Production MD: How to Run and Check

## What Phase 6 is

Production **NVT MD** for Model A (pristine) and Model B (single-vacancy), from
their Phase 4/5 **equilibrated** structures, using the **same validated Li–Si–C
ReaxFF/QEq protocol**. It produces the trajectories Phase 7 will analyze for Li
**MSD** and diffusion. Phase 6 produces **trajectories only** — no MSD, no
diffusion coefficients, no conclusions.

## The permeation design (why the geometry is this way)

The research question is whether graphene **vacancy defects** help Li **penetrate**
the Si–graphene interface. So the geometry is:

```
top / +z
   vacuum buffer
   ---- reflecting containment wall (z = 35 Å) ----
   Li region            (Li START above graphene)
   graphene             (single vacancy in Model B)
   Si slab              (bottom fixed)
bottom / -z
```

Li start **above** the graphene and the run watches whether they cross **through**
it toward the Si — expected to be easier through the vacancy (Model B). This is
**free thermal diffusion** (no driving force); penetration shows up in Phase 7 as
the **z-component of the Li MSD** / Li crossing below the sheet.

### Why a containment wall (and why not other things)

At 1200 K with open vacuum above them, Li **evaporate upward** — and evaporated Li
fly ballistically, which **breaks the MSD** (Phase 7's main metric). So a
**reflecting z-wall** is placed *above* the Li to keep them in the system. The
wall:
- only **reflects** Li that reach it (no force otherwise),
- is placed with headroom (Li reach ~32 Å; wall at 35 Å) so it does **not compress**
  the Li layer,
- does **not** push Li down, freeze Li z, tightly restrain Li, or delete escaping Li.

The graphene COM-z is also pinned (`fix recenter`) so the weakly-bound sheet does
not desorb into the vacuum (a finite-slab artifact) — it stays the barrier, while
Li remain free to cross it.

## Why Model A and Model B must use identical settings

It is a controlled comparison (pristine vs vacancy). Any difference in temperature,
timestep, thermostat, length, wall, or force field could masquerade as a defect
effect. The two inputs are byte-identical except file paths.

## How to run

### Option 1 — single constant-temperature production (1200 K)

```bash
source .venv/bin/activate
lmp_serial -in lammps_inputs/in.model_a_production   # ~15-20 min
lmp_serial -in lammps_inputs/in.model_b_production   # ~15-20 min
```

### Option 2 — staged temperature ramp (300 → 600 → 900 → 1200 K)

This is what was run on 2026-06-16 (see `notes/phase6_production_validation.md`).
`lammps_inputs/in.production_ramp` is **one parameterized NVT stage** driven from
the command line, so every stage/model uses byte-identical physics — only the
temperature changes. Each stage is ~10 ps and reads the **previous** stage's final
state (continuous heat-up):

```bash
source .venv/bin/activate
# Model A: climb 300 -> 600 -> 900 -> 1200 K (repeat for model_b)
lmp_serial -in lammps_inputs/in.production_ramp -var MODEL model_a \
  -var INDATA structures/model_a_pristine_equilibrated.data -var TSTAGE 300 -var STAGE 300K
lmp_serial -in lammps_inputs/in.production_ramp -var MODEL model_a \
  -var INDATA structures/model_a_ramp_300K_final.data       -var TSTAGE 600  -var STAGE 600K
lmp_serial -in lammps_inputs/in.production_ramp -var MODEL model_a \
  -var INDATA structures/model_a_ramp_600K_final.data       -var TSTAGE 900  -var STAGE 900K
lmp_serial -in lammps_inputs/in.production_ramp -var MODEL model_a \
  -var INDATA structures/model_a_ramp_900K_final.data       -var TSTAGE 1200 -var STAGE 1200K
```

Each stage writes `structures/${MODEL}_ramp_${STAGE}_final.data`,
`logs/${MODEL}_ramp_${STAGE}.log`, and
`trajectories/${MODEL}_ramp_${STAGE}.lammpstrj`. The two models share the input
verbatim — only `MODEL`/`INDATA`/`TSTAGE`/`STAGE` differ — so the A-vs-B comparison
stays controlled.

## How to check

```bash
python analysis/check_production_logs.py        # completion, NaN, QEq, temp/energy, same protocol
python analysis/plot_temperature_energy.py      # constant-1200K production: mobile-T + energy plots
python analysis/plot_temperature_energy_ramp.py # staged ramp: 4 stages stitched onto one ps axis
```

`plot_temperature_energy_ramp.py` reuses the parser from
`plot_temperature_energy.py`, reads the four `*_ramp_{300,600,900,1200}K.log`
stage logs per model, and writes
`figures/phase6_temperature_energy_model_{a,b}_ramp.png` (mobile T should step
300 → 600 → 900 → 1200 K; energy rises but stays bounded). Both plotting scripts
are visualization-only and **fail clearly** rather than fabricate.

## OVITO inspection

Open `trajectories/model_{a,b}_production.lammpstrj` (constant 1200 K) or, for the
staged ramp, `trajectories/model_{a,b}_ramp_{300,600,900,1200}K.lammpstrj`.
**Turn on "Wrap at periodic boundaries"** (the dump is unwrapped for MSD, so Li
diffusing sideways otherwise appear to leave the box — by 900/1200 K the unwrapped
Li sit several box-widths away in x/y even though z is steady at ~23.5 Å). Confirm:
Li stay in the region between graphene and the wall (not boiling off), graphene
stays on the Si, and watch for any Li crossing below the sheet. Save
`figures/phase6_model_{a,b}_production_snapshot.png`.

## Pass / fail criteria

**PASS** (both models): production completes; no NaN/Inf; no QEq failure; mobile T
bounded near 1200 K; energy finite; `check_production_logs.py` → `RESULT: PASS`
with same timestep and target T; in OVITO the slab + graphene + contained Li stay
intact (no collapse/explosion; Li do not evaporate).

**FAIL** (any): LAMMPS error, NaN/Inf, QEq divergence, temperature runaway
(> 5000 K), energy divergence, atoms flying apart, or Li escaping the wall.

## Why diffusion is not reported until Phase 7

Phase 6 only establishes stable, comparable production trajectories. Computing Li
MSD (3D, in-plane x-y, z/interface-normal), choosing the MSD fitting window (a
**project-discovered** value), converting to D_A and D_B, and comparing (D_B/D_A)
are all Phase 7. Reading any diffusion result from the Phase 6 temperature/energy
plots would be premature and is out of scope.
