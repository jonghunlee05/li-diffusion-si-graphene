# Phase 1 Sanity Checks

A checklist to confirm that every part of the toolchain works **before** any real
silicon–graphene modeling begins. Work top to bottom. Each item has a concrete
command and a clear "pass" condition. Tick the box only when the pass condition is met.

> Goal of Phase 1: run one trivial Lennard-Jones simulation, produce a trajectory,
> open it in OVITO, and save a validation screenshot. Nothing here uses real
> materials or real force-field parameters.

---

## 1. Python environment

- [ ] **Python is available**
  - Run: `python --version` (or `python3 --version`)
  - Pass: prints Python 3.9 or newer.
- [ ] **Dependencies install cleanly**
  - Run: `pip install -r requirements.txt`
  - Pass: completes with no errors.
- [ ] **Core packages import**
  - Run: `python -c "import numpy, pandas, matplotlib, ase; print('imports OK')"`
  - Pass: prints `imports OK` with no traceback.

---

## 2. LAMMPS

- [ ] **LAMMPS is installed and on PATH**
  - Run: `lmp -h` (binary may also be named `lmp_serial`, `lmp_mpi`, or `lammps`)
  - Pass: prints LAMMPS help / version banner.
- [ ] **LAMMPS runs the LJ test input**
  - Run (from `lammps_inputs/`): `lmp -in in.lj_test`
  - Pass: exits with no error; prints a thermo table; ends with `Total wall time`.
- [ ] **Log file is produced**
  - Pass: `log.lammps` exists and contains a thermo table with columns such as
    `Step Temp ... TotEng ... Press`.
- [ ] **Trajectory dump is produced**
  - Pass: a dump file (e.g. `dump.lj_test.lammpstrj`) exists and is non-empty.

---

## 3. Python analysis scripts

- [ ] **Output checker passes**
  - Run: `python analysis/check_outputs.py --dir lammps_inputs`
  - Pass: reports that both the log file and a dump trajectory were found.
- [ ] **Log plotting works**
  - Run: `python analysis/plot_lammps_log.py lammps_inputs/log.lammps`
  - Pass: writes a PNG into `figures/` showing temperature and/or energy vs. step,
    with no traceback.

---

## 4. OVITO

- [ ] **OVITO opens**
  - Pass: the OVITO application launches.
- [ ] **Trajectory loads**
  - Action: File → Load File → select the dump trajectory (`*.lammpstrj`).
  - Pass: atoms appear; the timeline shows multiple frames; stepping through frames
    shows the particles moving.
- [ ] **Validation screenshot saved**
  - Action: render/screenshot a frame and save it to `figures/`
    (e.g. `figures/ovito_validation.png`).
  - Pass: the PNG exists in `figures/`.

---

## Phase 1 is complete when

All boxes above are checked **and** `figures/` contains:
- one plot from `plot_lammps_log.py`, and
- one OVITO validation screenshot.

If anything fails, see the troubleshooting notes in
[../notes/phase1_environment_validation.md](../notes/phase1_environment_validation.md).
