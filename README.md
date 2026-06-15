# Effect of Graphene Defects on Lithium Diffusion at a Silicon–Graphene Composite Anode Interface

A reproducible classical molecular dynamics (MD) study of how defects in graphene
influence lithium-ion diffusion at the interface of a silicon–graphene composite
anode. Silicon–graphene composites are promising next-generation Li-ion battery
anodes: silicon offers very high lithium capacity, while graphene buffers the large
volume changes and improves electrical conductivity. The behavior of lithium at the
Si–graphene interface — especially around graphene defects — is central to rate
performance and cycle life.

> **Status: Phases 1–4 complete; Phase 5 next.**
> Toolchain validated (Phase 1), pristine graphene + Li structure built (Phase 2),
> Li–Si–C ReaxFF QEq smoke test passed (Phase 3), and **Model A (pristine
> Si–graphene–Li) minimizes and equilibrates without collapse** (Phase 4). **No
> production MD has been run and no diffusion results exist yet.** Next: Phase 5 —
> Model B (vacancy-defective graphene).

---

## Scientific goal

Quantify how graphene defects (e.g. vacancies, Stone–Wales defects, edges) affect
the lithium diffusion coefficient and diffusion pathways near a silicon–graphene
interface, and compare against pristine graphene as a baseline.

This is the project's end goal. The phases below track progress toward it; Phases
1–4 are complete and Phase 5 (Model B, vacancy-defective graphene) is next.

---

## Workflow stages

| Phase | Name | Goal | Status |
|------|------|------|--------|
| 1 | Environment validation | Confirm LAMMPS, OVITO, and the Python analysis stack all work using a trivial Lennard-Jones test. Produce a trajectory and a validation screenshot. | **Complete** |
| 2 | Graphene + Li structure | Build and validate a reproducible pristine graphene + lithium initial structure (no silicon, no defects). Export XYZ + LAMMPS data; sanity-check geometry; visualize in OVITO. | **Complete** |
| 3 | Force-field / ReaxFF validation | Confirm the published Li–Si–C ReaxFF loads in LAMMPS, atom types map correctly, QEq runs, and a tiny test is stable. No invented parameters. | **Complete** |
| 4 | Model A: pristine Si–graphene–Li | Build, minimize, and equilibrate the pristine Si–graphene interface with Li. | **Complete** |
| 5 | Model B: defective Si–graphene–Li | Same as Model A plus a graphene vacancy defect; identical protocol. | **Active** |
| 6 | Production MD | Run diffusion simulations for Models A and B. | Planned |
| 7 | MSD & diffusion analysis | Compute MSD, diffusion coefficients, and pathway statistics; compare defect vs. pristine. | Planned |

---

## Phase 1 (complete) — toolchain validation

A trivial Lennard-Jones LAMMPS run ([lammps_inputs/in.lj_test](lammps_inputs/in.lj_test))
that produces a log and a trajectory, plotted with
[analysis/plot_lammps_log.py](analysis/plot_lammps_log.py) and checked with
[analysis/check_outputs.py](analysis/check_outputs.py). No real materials, no
invented parameters. This confirmed LAMMPS, OVITO, and the Python stack all work.

---

## Phase 2 (complete) — graphene + Li initial structure

A reproducible pristine graphene + Li structure
([structures/build_graphene_li.py](structures/build_graphene_li.py)): 48‑C
Chou & Hwang sheet (lattice 2.467 Å), 6 Li at 2.3 Å, 20 Å vacuum; exported to
XYZ + LAMMPS data and sanity-checked with
[analysis/inspect_structure.py](analysis/inspect_structure.py). Every parameter
is sourced to a primary PDF or documented as a project choice. Details:
[structures/README.md](structures/README.md) ·
[notes/phase2_graphene_li_validation.md](notes/phase2_graphene_li_validation.md).

---

## Phase 3 (complete) — force-field (ReaxFF/QEq) validation

Confirmed the published **Li–Si–C ReaxFF** (Olou'ou Guifo et al., *J. Phys. Chem.
C* 2023, 127, 2818; DOI 10.1021/acs.jpcc.2c07773) loads in LAMMPS, that atom
types map to C/Si/Li correctly (`pair_coeff * * <file> C Si Li`), that charge
equilibration runs, and that a tiny 6‑atom test is stable (no NaN, no explosion).
**Smoke test only** — no production MD, no diffusion, no Model A/B, and **no
invented parameters**. Reproduce with:

> **ReaxFF file:** the real Li–Si–C parameter file
> (`force_fields/ffield.reax.LiSiC_OlououGuifo2023.txt`) has been added and the
> smoke test passes. Provenance and the verified header correction are recorded
> in [force_fields/README.md](force_fields/README.md). Parameters must never be
> invented.

```bash
# 0. (once) add the real ReaxFF file to force_fields/ and set the filename in
#    lammps_inputs/in.reaxff_smoke_test (variable REAXFF_FILE)

# 1. Build the tiny Li-Si-C smoke-test structure (atom_style charge)
python structures/build_reaxff_smoke_test.py

# 2. Run the ReaxFF/QEq smoke test
lmp -in lammps_inputs/in.reaxff_smoke_test

# 3. Inspect the log (completion, QEq, NaN, energies)
python analysis/check_reaxff_log.py

# 4. Open trajectories/reaxff_smoke_test.lammpstrj in OVITO; confirm atoms do
#    not explode; save figures/phase3_reaxff_smoke_test.png
```

Details and validation:
[docs/phase3_force_field_validation.md](docs/phase3_force_field_validation.md) ·
[force_fields/README.md](force_fields/README.md) ·
[notes/phase3_reaxff_validation.md](notes/phase3_reaxff_validation.md).

---

## Phase 4 (complete) — Model A: pristine Si–graphene–Li

Built the first real interface model — a **Si(111) slab + pristine graphene + Li**
(48 Si + 18 C + 9 Li) — and confirmed it **minimizes and equilibrates without
collapse** using the validated Li–Si–C ReaxFF. Si is strained −3.64% to match
graphene (methodology's ~4% mismatch); Si–graphene gap 2.0 Å (Chou [1]); 18 Å
vacuum (Qin [2]). Bottom Si is fixed (the ReaxFF has no H, so Qin's H-passivation
isn't possible — documented deviation). **Structural validation only** — no
defects, no production MD, no diffusion.

```bash
# 1. Build + sanity-check the structure
python structures/build_model_a_pristine.py
python analysis/inspect_model_a.py

# 2. Minimize, then short NVT equilibration (ReaxFF + QEq)
lmp_serial -in lammps_inputs/in.model_a_minimize
lmp_serial -in lammps_inputs/in.model_a_equilibrate_short

# 3. Check logs; open trajectory in OVITO; save
#    figures/phase4_model_a_pristine_equilibrated.png
python analysis/check_model_a_logs.py
```

Details and validation:
[docs/phase4_model_a_construction.md](docs/phase4_model_a_construction.md) ·
[notes/phase4_model_a_validation.md](notes/phase4_model_a_validation.md).

---

## Repository layout

```
Li_Diffusion_Si_Graphene/
├── README.md          # This file
├── requirements.txt   # Python analysis dependencies
├── literature/        # Reference papers (primary PDFs) + methodology doc
├── force_fields/      # Real ReaxFF parameter file + provenance (Phase 3)
├── structures/        # ASE structure builders + generated data/XYZ files
├── lammps_inputs/     # LAMMPS input scripts (LJ test, ReaxFF smoke test)
├── trajectories/      # MD dump/trajectory outputs
├── logs/              # LAMMPS log files
├── analysis/          # Python analysis & plotting scripts
├── figures/           # Generated plots and validation screenshots
├── docs/              # How-to documentation per phase
└── notes/             # Phase validation notes/checklists
```

---

## Requirements

- **LAMMPS** with the **REAXFF** package (Phase 3+); basic pair styles suffice for
  the Phase 1 LJ test. Check your build with `lmp -h | grep reaxff`.
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
