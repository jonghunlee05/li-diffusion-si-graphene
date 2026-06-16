# Phase 5 — Model B Construction: Single-Vacancy Si-graphene-Li

## What Model B is

**Model B = Si(111) slab + single-vacancy (SV) graphene + Li.** It is the
defective counterpart to Model A (pristine), and the only difference between them
is **one removed central graphene carbon atom**. Phase 5 builds it and confirms it
**minimizes and equilibrates without collapse** — a structural model only (no
DV5-8-5, no production MD, no MSD/diffusion, no conclusions).

## How it differs from Model A

Model B is built by **importing Model A's exact construction**
(`build_model_a_pristine.assemble_model_a`) and removing one carbon. Everything
else is reused unchanged:

| Quantity | Model A | Model B |
|----------|---------|---------|
| Si slab (Si(111), 2×2×6, strained −3.64%) | 48 | **48 (same)** |
| graphene | 18 C | **17 C (one removed)** |
| Li | 9 | **9 (same)** |
| box | 7.401 × 7.401 × 40.330 Å | **identical** |
| Si–graphene gap, vacuum, type order | — | **identical** |
| ReaxFF file, QEq, fix-bottom, timestep, T | — | **identical** |

So Model B carbon count = Model A − 1, and the LAMMPS inputs are byte-identical to
Model A's except for file paths.

## How the vacancy is created (literature basis)

A **single vacancy (SV)** is made by removing one carbon atom:
- **Si et al. [6]** (primary): *"SV defects are created by removing a C atom"*;
  their C counts go 14 (p-Gr) → 13 (SV) — exactly one fewer.
- **Methodology Sec. 5** (defect construction): *"Remove one central C atom for
  SV; keep all other variables identical to Model A"* (Qin et al. [2]).

`build_model_b_sv.py` removes the carbon **nearest the graphene in-plane
centroid** (deterministic "central" choice), creating the vacancy.

## How the removed atom is recorded

`structures/model_b_sv_metadata.json` records, before deletion:
- `index_0based_in_model_a` and `lammps_id_1based_in_model_a` (id = index+1),
- `element` and `coordinates_xyz_A`,
- the selection criterion, build parameters, atom counts, box, and literature
  basis.

For the default build: removed C = Model A index **9** / LAMMPS id **10** at
**(2.467, 2.849, 20.030) Å**.

## How to compare Model A and Model B

```bash
python analysis/compare_model_a_b_structures.py
```
Confirms: Si identical, Li identical, C(B) = C(A) − 1, box identical, consistent
type mapping, and reports min distances for both + the removed-atom record.
Expect `RESULT: PASS`.

## How to run

```bash
source .venv/bin/activate

# 1. Build + inspect + compare to Model A
python structures/build_model_b_sv.py
python analysis/inspect_model_b.py
python analysis/compare_model_a_b_structures.py

# 2. Minimize, then short NVT equilibration (same ReaxFF/QEq as Model A)
lmp_serial -in lammps_inputs/in.model_b_minimize
lmp_serial -in lammps_inputs/in.model_b_equilibrate_short

# 3. Check logs; open trajectory in OVITO; save
#    figures/phase5_model_b_sv_equilibrated.png
python analysis/check_model_b_logs.py
```

## Pass / fail criteria

**PASS** (all of):
- Build + `inspect_model_b.py` report no overlaps; metadata written.
- `compare_model_a_b_structures.py` → `RESULT: PASS` (B differs only by 1 C).
- Minimization + short equilibration complete, energy finite/bounded, no NaN, no
  temperature blow-up (`check_model_b_logs.py` → `RESULT: PASS`).
- In OVITO the slab + defective graphene + Li stay intact — **no collapse**.

**FAIL** (any of): LAMMPS errors, NaN/Inf, temperature runaway (> 5000 K), atoms
flying apart, interface collapsing, or the A/B comparison failing.

## Why no diffusion results are interpreted yet

Phase 5 is **structural validation only**. Do **not** compare Model A vs Model B
energies or geometries as scientific results, and do **not** infer anything about
lithium diffusion. Production MD (Phase 6) and MSD/diffusion analysis (Phase 7)
come later; only then are D_A, D_B, and D_B/D_A computed — from project data, not
assumed. The short 125 fs equilibration is a stability check, not thermal
equilibration; the final temperature overshooting the 300 K setpoint is expected
and is not a result.
