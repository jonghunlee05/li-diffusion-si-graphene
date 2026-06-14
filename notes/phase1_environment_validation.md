# Phase 1 — Environment Validation (Run Guide)

This note tells you exactly what to run, in what order, and what output proves
each step succeeded. By the end you will have run one trivial Lennard-Jones MD
simulation, produced a trajectory, plotted the log, opened the trajectory in
OVITO, and saved a validation screenshot.

**Nothing here uses real materials or real force-field parameters.** No silicon,
graphene, or lithium is built. This is purely a toolchain smoke test.

Use the checklist in [../docs/sanity_checks.md](../docs/sanity_checks.md) to tick
off each item as you go.

---

## Step 0 — Set up Python

```bash
# From the repository root:
python --version            # expect 3.9+
pip install -r requirements.txt
python -c "import numpy, pandas, matplotlib, ase; print('imports OK')"
```

**Proof of success:** `imports OK` prints with no traceback.

---

## Step 1 — Run the LAMMPS Lennard-Jones test

```bash
cd lammps_inputs
lmp -in in.lj_test
# Your LAMMPS binary may instead be named: lmp_serial, lmp_mpi, or lammps
```

**Proof of success:**
- The run prints a thermo table (columns: `Step Temp PotEng KinEng TotEng Press`).
- The final lines include `Total wall time:` and the message
  `Phase 1 LJ test complete...`.
- Two files now exist in `lammps_inputs/`:
  - `log.lammps`
  - `dump.lj_test.lammpstrj`

---

## Step 2 — Confirm the outputs exist

```bash
# From the repository root:
python analysis/check_outputs.py --dir lammps_inputs
```

**Proof of success:** the script prints
`RESULT: PASS — both log and trajectory found.` and exits 0.

---

## Step 3 — Plot temperature and energy from the log

```bash
# From the repository root:
python analysis/plot_lammps_log.py lammps_inputs/log.lammps
```

**Proof of success:**
- The script prints `Saved plot to: figures/log_plot.png` (or similar).
- `figures/log_plot.png` exists and shows temperature and/or total energy
  vs. step. For this NVE run the total energy should be roughly flat and the
  temperature should settle after the initial transient.

---

## Step 4 — Open the trajectory in OVITO and save a screenshot

1. Launch **OVITO**.
2. `File → Load File…` and select
   `lammps_inputs/dump.lj_test.lammpstrj`.
3. Confirm:
   - atoms appear in the viewport,
   - the timeline shows multiple frames,
   - stepping/playing through frames shows the particles moving.
4. Save a screenshot or rendered image to
   `figures/ovito_validation.png`
   (in OVITO: `Render` tab → render an image → save; or use a viewport screenshot).

**Proof of success:** `figures/ovito_validation.png` exists and shows the LJ
particles.

---

## Phase 1 done when

- [ ] `lammps_inputs/log.lammps` exists
- [ ] `lammps_inputs/dump.lj_test.lammpstrj` exists
- [ ] `check_outputs.py` reports PASS
- [ ] `figures/log_plot.png` exists (temperature/energy plot)
- [ ] `figures/ovito_validation.png` exists (OVITO screenshot)

When all five are true, the toolchain is validated and we can move to Phase 2
(force-field selection — using only published, cited parameters).

---

## Troubleshooting

| Symptom | Likely cause / fix |
|--------|--------------------|
| `lmp: command not found` | LAMMPS not installed or not on PATH. Try `lmp_serial`, `lmp_mpi`, or install LAMMPS. |
| LAMMPS error about unknown `pair_style` | Your build lacks basic pair styles — rebuild/download a standard LAMMPS package. |
| `check_outputs.py` says MISSING | You may have run LAMMPS from a different directory; pass the correct `--dir`. |
| `plot_lammps_log.py` finds no thermo table | Point it at the real `log.lammps`; confirm the run actually produced thermo output. |
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` in the active environment. |
| OVITO won't load the dump | Ensure you selected the `.lammpstrj` file and that it is non-empty. |

---

## Scope reminders (do NOT do these in Phase 1)

- Do **not** build graphene, silicon, or lithium structures.
- Do **not** select or invent force-field parameters.
- Do **not** use ReaxFF.
- Do **not** record any of this LJ test as a scientific result.
