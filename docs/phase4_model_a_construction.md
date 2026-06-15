# Phase 4 — Model A Construction: How to Build, Minimize, Equilibrate

## What Model A is

**Model A = Si(111) slab + pristine graphene + Li**, in one periodic cell — the
first real Si–graphene interface model. Phase 4 builds it and confirms it
**minimizes and equilibrates without collapse**. It is a STRUCTURAL model:

- **No defects** — graphene is pristine (the vacancy model is Model B, Phase 5).
- **No production MD, no MSD/diffusion, no scientific conclusions** here.

## How the structure was built (`structures/build_model_a_pristine.py`)

1. **Pristine graphene** on a hexagonal cell (lattice 2.467 Å, Chou & Hwang [1]),
   3×3 = 18 C. This defines the common in-plane cell.
2. **Si(111) slab** (`ase.build.surface`, diamond Si, a = 5.431 Å — standard
   experimental value), 2×2 in-plane × 6 layers = 48 Si.
3. **Lattice match:** the Si slab is strained in-plane to the graphene cell
   (**−3.64%**), consistent with the methodology note that Si–Si is "adjusted
   ~4% for mismatch." Graphene is kept at its literature lattice; Si takes the
   strain. (Both cells are hexagonal; the builder reconciles the 60°/120° cell
   conventions so the strain is a clean scale, not a shear.)
4. **Stacking:** graphene placed **2.0 Å** above the top Si layer (initial
   Si–graphene separation, Chou & Hwang [1]); Li placed **2.3 Å** above graphene
   (Chou & Hwang [1] interface Li–Gr distance).
5. **z-vacuum 18 Å** above the slab (Qin et al. [2]).

Exports `structures/model_a_pristine.{xyz,data}` (LAMMPS `atom_style charge`,
Masses; type 1=C, 2=Si, 3=Li → `pair_coeff * * <reaxff> C Si Li`).

## Chosen parameters (all documented / sourced)

| Parameter | Value | Source |
|-----------|-------|--------|
| Si orientation | Si(111) | Qin et al. [2] |
| Si lattice constant | 5.431 Å | standard experimental Si |
| Si slab | 2×2 × 6 layers (48 Si) | project choice (precedent 4×4 / 2-double [2], 10-layer [9]) |
| graphene | 2.467 Å, 3×3 (18 C) | Chou & Hwang [1] |
| Si in-plane strain | −3.64% | methodology "~4% mismatch" |
| Si–graphene gap | 2.0 Å | Chou & Hwang [1] |
| Li height / count | 2.3 Å / 9 | Chou & Hwang [1] / project choice |
| z-vacuum | 18 Å | Qin et al. [2] |
| timestep | 0.25 fs | Phase 3 conservative (Olou'ou Guifo [4] used 0.5/0.1 fs) |
| equilibration T | 300 K | conservative (production is 800/1200 K [1,9]) |

### Two forced deviations (documented)

- **No H passivation.** Qin et al. [2] passivate bottom Si dangling bonds with H;
  the Olou'ou Guifo [4] Li–Si–C ReaxFF has **no hydrogen**, so instead the
  **bottom Si layer is fixed** (`fix setforce 0`, atoms with z ≤ 3.5 Å).
- **Li above graphene.** Li is placed on the vacuum side of graphene (the
  methodology-permitted "near/above graphene" option), which is overlap-safe for
  a structural model. Burying Li at the interface is a future refinement.

## How to run

```bash
source .venv/bin/activate

# 1. Build + inspect
python structures/build_model_a_pristine.py
python analysis/inspect_model_a.py            # expect "OK: no overlaps"

# 2. Minimize (writes structures/model_a_pristine_minimized.data)
lmp_serial -in lammps_inputs/in.model_a_minimize

# 3. Short NVT equilibration (writes structures/model_a_pristine_equilibrated.data)
lmp_serial -in lammps_inputs/in.model_a_equilibrate_short

# 4. Check both logs
python analysis/check_model_a_logs.py         # expect "RESULT: PASS"

# 5. Open trajectories/structures in OVITO; save
#    figures/phase4_model_a_pristine_equilibrated.png
```

## Pass / fail criteria

**PASS** (all of):
- Build + `inspect_model_a.py` report no overlaps.
- Minimization completes (`Total wall time`), writes the minimized data, no NaN.
- Short equilibration completes, energy stays finite/bounded, no temperature
  blow-up (`check_model_a_logs.py` → `RESULT: PASS`).
- In OVITO the slab + graphene + Li stay intact — **no collapse, no explosion,
  nothing fused or scattered**.

**FAIL** (any of): LAMMPS errors, NaN/Inf charges or energies, temperature
runaway (> 5000 K), atoms flying apart, or the interface collapsing/fusing.

## What NOT to interpret yet

This is a **structural** validation. Do **not** read anything into the energies,
the 300 K equilibration, or atom positions as physical results. No diffusion, no
MSD, no comparison to defective graphene — those come in Phases 5–7. The short
125 fs equilibration is a stability check, **not** thermal equilibration; the
final temperature overshooting the 300 K setpoint is expected for such a short
run and is not a result.
