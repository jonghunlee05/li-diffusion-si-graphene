# Effect of Graphene Defects on Lithium Diffusion at a Silicon–Graphene Composite Anode Interface

A reproducible classical molecular dynamics (MD) study of how defects in graphene
influence lithium-ion diffusion at the interface of a silicon–graphene composite
anode. Silicon–graphene composites are promising next-generation Li-ion battery
anodes: silicon offers very high lithium capacity, while graphene buffers the large
volume changes and improves electrical conductivity. The behavior of lithium at the
Si–graphene interface — especially around graphene defects — is central to rate
performance and cycle life.

> **Status: Phase 1 — Environment validation only.**
> No silicon, graphene, or lithium structures have been built yet. No force-field
> parameters have been chosen. No production results exist. This repository currently
> exists to prove that the simulation and analysis toolchain works end to end.

---

## Scientific goal

Quantify how graphene defects (e.g. vacancies, Stone–Wales defects, edges) affect
the lithium diffusion coefficient and diffusion pathways near a silicon–graphene
interface, and compare against pristine graphene as a baseline.

This is a *future* objective. The phases below describe the intended workflow; only
Phase 1 is active.

---

## Workflow stages

| Phase | Name | Goal | Status |
|------|------|------|--------|
| 1 | Environment validation | Confirm LAMMPS, OVITO, and the Python analysis stack all work using a trivial Lennard-Jones test. Produce a trajectory and a validation screenshot. | **Complete** |
| 2 | Graphene + Li structure | Build and validate a reproducible pristine graphene + lithium initial structure (no silicon, no defects). Export XYZ + LAMMPS data; sanity-check geometry; visualize in OVITO. | **Active** |
| 3 | Structure building | Add silicon and the Si–graphene interface; introduce controlled graphene defects. Select published interatomic potentials (no invented parameters). | Planned |
| 4 | Equilibration | Relax and thermally equilibrate each system. | Planned |
| 5 | Production MD | Run diffusion simulations with lithium present. | Planned |
| 6 | Analysis | Compute mean-squared displacement (MSD), diffusion coefficients, and pathway statistics; compare defect vs. pristine. | Planned |
| 7 | Reporting | Figures, write-up, and reproducibility package. | Planned |

---

## Phase 1 (complete) — toolchain validation

A trivial Lennard-Jones LAMMPS run ([lammps_inputs/in.lj_test](lammps_inputs/in.lj_test))
that produces a log and a trajectory, plotted with
[analysis/plot_lammps_log.py](analysis/plot_lammps_log.py) and checked with
[analysis/check_outputs.py](analysis/check_outputs.py). No real materials, no
invented parameters. This confirmed LAMMPS, OVITO, and the Python stack all work.

---

## Current Phase 2 objective — graphene + Li initial structure

Build and validate a **reproducible pristine graphene + lithium initial
structure**. No silicon, no defects, no ReaxFF, no MD, no diffusion yet. The
physical values are literature-informed starting values from the project
methodology document: graphene lattice constant **2.467 Å**, Li starting height
**≈ 2.3 Å**, z-vacuum **≈ 20 Å**.

```bash
# 0. Set up the environment (once)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Build the structure -> structures/graphene_li.xyz and .data
python structures/build_graphene_li.py

# 2. Sanity-check the geometry (atom counts, box, Li–C / C–C distances)
python analysis/inspect_structure.py

# 3. Open structures/graphene_li.xyz in OVITO and save a screenshot to
#    figures/phase2_graphene_li_initial_structure.png
```

Details and validation:
[docs/phase2_structure_generation.md](docs/phase2_structure_generation.md) ·
[structures/README.md](structures/README.md) ·
[notes/phase2_graphene_li_validation.md](notes/phase2_graphene_li_validation.md).

---

## Repository layout

```
Li_Diffusion_Si_Graphene/
├── README.md          # This file
├── requirements.txt   # Python analysis dependencies
├── literature/        # Reference papers and citation notes (Phase 2+)
├── force_fields/      # Published potential files + provenance (Phase 2+)
├── structures/        # Structure builder + generated graphene/Li files (Phase 2)
├── lammps_inputs/     # LAMMPS input scripts (Phase 1: LJ test only)
├── trajectories/      # MD dump/log outputs
├── analysis/          # Python analysis & plotting scripts
├── figures/           # Generated plots and validation screenshots
├── docs/              # Sanity checks and documentation
└── notes/             # Working notes per phase
```

---

## Requirements

- **LAMMPS** (any recent stable build with the `MOLECULE`/basic pair styles).
- **OVITO** (Basic or Pro) for trajectory visualization.
- **Python 3.9+** with the packages in [requirements.txt](requirements.txt).

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

---

## Guiding principles

- **No invented physics.** Force-field parameters will only ever come from published,
  cited sources.
- **No fabricated results.** Every number traces back to a script and an input.
- **Reproducible.** Inputs, analysis, and figures live in version control together.
- **Simple first.** The toolchain is validated on a trivial system before any real
  materials work begins.
