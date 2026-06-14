# Phase 3 — Force-Field (ReaxFF/QEq) Validation: How to Run

## Why Phase 3 exists

The production study needs a single **ternary Li–Si–C** reactive potential
(covering Li–Li, Si–Si, C–C, Li–Si, Li–C, Si–C). Before building any real
Si–graphene–Li model, we must confirm the chosen ReaxFF actually **loads and
runs** in LAMMPS with charge equilibration. Phase 3 is that smoke test — it
catches setup problems (wrong atom mapping, QEq failure, instant blow-up) on a
trivial 6-atom cluster instead of a 1000-atom model.

Phase 3 is **NOT**: production MD, MSD/diffusion, or Model A/B. No physical
result comes out of it.

Force field: **Olou'ou Guifo et al., *J. Phys. Chem. C* 2023, 127, 2818−2834,
DOI 10.1021/acs.jpcc.2c07773** (methodology ref [4]). See
`force_fields/README.md`.

---

## Step 1 — Add the real ReaxFF file (researcher)

The parameter file is **not** in the repo and must not be invented.

1. Obtain the Li–Si–C ReaxFF file from the paper's Supporting Information /
   van Duin group source (DOI above).
2. Put it in `force_fields/` (e.g. `force_fields/LiSiC.reaxff`).
3. Fill in the provenance record in `force_fields/README.md`
   (filename, source URL, atom order, date added).
4. (Any "add the file here" placeholder is removed once the real file is in.)

## Step 2 — Confirm atom mapping

1. Open the ReaxFF file; read the element list in its header. Record it in
   `force_fields/README.md`.
2. Confirm `C`, `Si`, `Li` all appear among those elements.
3. Our smoke-test data file defines **type 1 = C, type 2 = Si, type 3 = Li**, so
   the LAMMPS input maps:
   ```
   pair_coeff * * force_fields/<your_file>.reaxff C Si Li
   ```
   The element order after the filename follows the **data-file type order**,
   not the order inside the ReaxFF file. If you rebuild with a different type
   order, update `pair_coeff` to match.
4. Set `variable REAXFF_FILE` in `lammps_inputs/in.reaxff_smoke_test` to the
   real filename.

## Step 3 — Build the smoke-test structure

```bash
source .venv/bin/activate            # if not already active
python structures/build_reaxff_smoke_test.py
```
Produces `structures/reaxff_smoke_test.{data,xyz}` (6 atoms: 2 C, 2 Si, 2 Li,
min separation 2.7 Å, `atom_style charge`).

## Step 4 — Run the smoke test

```bash
lmp -in lammps_inputs/in.reaxff_smoke_test
# binary may be lmp / lmp_serial / lmp_mpi / lammps; needs the REAXFF package
```
Writes `logs/reaxff_smoke_test.log` and
`trajectories/reaxff_smoke_test.lammpstrj`.

## Step 5 — Inspect the log

```bash
python analysis/check_reaxff_log.py
```
Checks completion, NaN/Inf, QEq warnings, dangerous neighbor builds, final
temperature, and energy finiteness. Expect `RESULT: PASS`.

## Step 6 — Visualize and screenshot

Open `trajectories/reaxff_smoke_test.lammpstrj` in OVITO. The atoms should stay
a compact cluster. Save `figures/phase3_reaxff_smoke_test.png`.

---

## Pass / fail criteria

**PASS** (all of):
- ReaxFF file loads; `pair_style reaxff` + `pair_coeff` accepted.
- `fix qeq/reaxff` runs with no unresolved convergence warnings.
- Run finishes (`Total wall time`); no `NaN`/`Inf`; energies finite.
- `check_reaxff_log.py` prints `RESULT: PASS`.
- In OVITO, atoms do not explode (no scattering to box edges).
- `logs/…log`, `trajectories/…lammpstrj`, and the screenshot all exist.

**FAIL** (any of):
- LAMMPS errors on `pair_coeff` (atom label not in file / wrong count).
- QEq fails to converge or charges go `NaN`.
- Atoms blow apart in the trajectory.
- Missing REAXFF package in the LAMMPS build (rebuild/install with REAXFF).

---

## Common issues

| Symptom | Likely cause / fix |
|--------|--------------------|
| `Cannot open ReaxFF potential file` | Wrong path/filename in `REAXFF_FILE`. |
| `Element not found in ReaxFF file` | A `pair_coeff` label isn't in the file's element list; fix the label. |
| `pair_coeff` count mismatch | Number of element labels ≠ number of atom types (3 here). |
| `Unknown pair style reaxff` | LAMMPS built without the REAXFF package; rebuild/install it. |
| Atoms fly apart immediately | Overlap or wrong mapping; rebuild structure; re-check atom order. |
