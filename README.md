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
| 1 | Environment validation | Confirm LAMMPS, OVITO, and the Python analysis stack all work using a trivial Lennard-Jones test. Produce a trajectory and a validation screenshot. | **Active** |
| 2 | Force-field selection | Identify and document (with citations) appropriate, *published* interatomic potentials for Si, C, and Li interactions. No parameters are invented. | Planned |
| 3 | Structure building | Build pristine graphene, silicon, and the Si–graphene interface; introduce controlled graphene defects. | Planned |
| 4 | Equilibration | Relax and thermally equilibrate each system. | Planned |
| 5 | Production MD | Run diffusion simulations with lithium present. | Planned |
| 6 | Analysis | Compute mean-squared displacement (MSD), diffusion coefficients, and pathway statistics; compare defect vs. pristine. | Planned |
| 7 | Reporting | Figures, write-up, and reproducibility package. | Planned |

---

## Current Phase 1 objective

Demonstrate a working toolchain. Concretely, you should be able to:

1. Run one simple LAMMPS example ([lammps_inputs/in.lj_test](lammps_inputs/in.lj_test)) — a
   generic Lennard-Jones fluid with **no real materials and no invented parameters**.
2. Produce a LAMMPS log file (`log.lammps`) and a dump trajectory file.
3. Plot temperature and energy from the log with
   [analysis/plot_lammps_log.py](analysis/plot_lammps_log.py).
4. Verify expected outputs exist with
   [analysis/check_outputs.py](analysis/check_outputs.py).
5. Open the trajectory in OVITO and save a validation screenshot into
   [figures/](figures/).

Follow the step-by-step guide in
[notes/phase1_environment_validation.md](notes/phase1_environment_validation.md) and the
checklist in [docs/sanity_checks.md](docs/sanity_checks.md).

---

## Repository layout

```
Li_Diffusion_Si_Graphene/
├── README.md          # This file
├── requirements.txt   # Python analysis dependencies
├── literature/        # Reference papers and citation notes (Phase 2+)
├── force_fields/      # Published potential files + provenance (Phase 2+)
├── structures/        # Atomic structures / data files (Phase 3+)
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
