# Phase 6 — Production MD Settings (Model A and Model B)

Settings are **identical for Model A and Model B** — the two production inputs
differ only in file paths. This is the single reference; keep it in sync with
`lammps_inputs/in.model_a_production` and `lammps_inputs/in.model_b_production`.

**Design:** Li start **above** the graphene (the permeation design) and the run
watches whether they cross **through** the sheet (vacancy in Model B) toward the
Si. A reflecting z-wall **above** the Li keeps them in the system (so the MSD is
valid); the graphene COM-z is pinned so the membrane stays the barrier.

| Setting | Value | Source / note |
|---------|-------|---------------|
| Ensemble | NVT (Nosé–Hoover) | methodology §6 (NVT, [1,3,5,9]) |
| Temperature | **1200 K** | Si et al. [9] (Si/p-Gr vs Si/SV comparison) |
| Timestep | **0.25 fs** | validated in Phases 4/5 |
| Thermostat damping | 25.0 fs | same as Phase 4/5 |
| Production length | **80,000 steps = 20 ps** | "long enough for MSD, not excessive" |
| Dump | `id type xu yu zu` (**unwrapped**) every 100 steps | required for Phase 7 Li-MSD across PBC |
| z boundary | `f` (non-periodic) | so the reflecting wall can act in z; 18 Å vacuum already prevents across-z interaction |
| **Containment wall** | `fix wall/reflect zhi 35.0` (Å) | reflecting only — stops Li evaporating. Li start ~22 Å, reach ~32 Å; 35 leaves ~2.5 Å headroom (no compression). **No force, no freezing, no deletion of Li.** |
| **Graphene anchor** | `fix recenter` pins graphene COM-**z** only (x,y free) | keeps the membrane on Si; Li can still cross it |
| Li placement | **above graphene** (~2.3–2.4 Å), vacuum side | the permeation design |
| ReaxFF file | `force_fields/ffield.reax.LiSiC_OlououGuifo2023.txt` | Olou'ou Guifo et al. [4] |
| pair_style / pair_coeff | `reaxff NULL safezone 3.0 mincap 150` / `* * <ffield> C Si Li` | validated Phase 3 (1=C, 2=Si, 3=Li) |
| QEq | `fix qeq/reaxff 1 0.0 10.0 1.0e-6 reaxff` | validated Phase 3 |
| Bottom Si | `setforce 0` **and** `velocity set 0 0 0` | no H in ffield → fix instead of passivate |
| Velocity init | `velocity mobile create 1200 90210 mom yes rot yes dist gaussian` | seed 90210 (both models) |
| Mobile temp readout | `compute ctemp mobile temp` → thermo `c_ctemp` | global `Temp` diluted by fixed bottom |

## Inputs / outputs

| | Model A (pristine) | Model B (single-vacancy) |
|--|--------------------|--------------------------|
| input | `lammps_inputs/in.model_a_production` | `lammps_inputs/in.model_b_production` |
| start structure | `structures/model_a_pristine_equilibrated.data` | `structures/model_b_sv_equilibrated.data` |
| trajectory | `trajectories/model_a_production.lammpstrj` | `trajectories/model_b_production.lammpstrj` |
| log | `logs/model_a_production.log` | `logs/model_b_production.log` |
| final structure | `structures/model_a_production_final.data` | `structures/model_b_production_final.data` |

## Run commands

```bash
lmp_serial -in lammps_inputs/in.model_a_production
lmp_serial -in lammps_inputs/in.model_b_production
python analysis/check_production_logs.py
python analysis/plot_temperature_energy.py
```

## Staged-ramp variant (300 → 600 → 900 → 1200 K)

The same physics as above, but run as a **temperature ramp** instead of a single
constant-1200 K production. `lammps_inputs/in.production_ramp` is one parameterized
NVT stage (40,000 × 0.25 fs ≈ 10 ps) driven by `-var`; each stage reads the
previous stage's `*_final.data` (continuous heat-up). Only these differ from the
table above:

| Setting | Constant-T production | Staged ramp |
|---------|-----------------------|-------------|
| Temperature | 1200 K (fixed) | per-stage `TSTAGE`: 300, 600, 900, 1200 K |
| Length | 80,000 steps (20 ps) | 40,000 steps (10 ps) **per stage** |
| Velocity init | `velocity mobile create 1200 …` | **none** — carried-over state, thermostat brings it to `TSTAGE` |
| Start structure | `*_equilibrated.data` | stage 1: `*_equilibrated.data`; later stages: previous `*_ramp_*_final.data` |
| Outputs | `*_production.{log,lammpstrj,_final.data}` | `*_ramp_${STAGE}.{log,lammpstrj,_final.data}` |

Run + check (see `docs/phase6_production_md.md` for the full per-stage commands):

```bash
# one stage (repeat for 600/900/1200 K and for model_b):
lmp_serial -in lammps_inputs/in.production_ramp -var MODEL model_a \
  -var INDATA structures/model_a_pristine_equilibrated.data -var TSTAGE 300 -var STAGE 300K
python analysis/plot_temperature_energy_ramp.py   # 4 stages stitched onto one ps axis
```

> Phase 6 generates trajectories only. **No MSD, no diffusion coefficients, no
> conclusions** — those are Phase 7.
