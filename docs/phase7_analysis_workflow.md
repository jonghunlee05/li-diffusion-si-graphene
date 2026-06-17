# Phase 7 — Analysis Workflow (Li MSD & Diffusion)

## What Phase 7 does

Phase 7 is **analysis only**. It reads the Phase 6 production trajectories and
computes the lithium **mean-squared displacement (MSD)**, fits the linear regime to
get **diffusion coefficients**, and compares **Model B (single-vacancy)** against
**Model A (pristine)**. It runs **no new MD** and **modifies no structures**
(Phase 7 rules #1, #2).

The results (numbers, fitting windows, and the important caveats) live in
[notes/phase7_msd_diffusion_analysis.md](../notes/phase7_msd_diffusion_analysis.md).

## Dataset note (important)

The originally listed `trajectories/model_{a,b}_production.lammpstrj` were built with
a **9-Li** configuration that was later superseded; the current structures use
**4 Li**. Phase 7 therefore analyzes the **4-Li `*_ramp_1200K.lammpstrj`**
trajectories (same 1200 K), which are consistent with the current structures. All
scripts take trajectory paths as arguments, so this is configurable.

## How to run (in order)

```bash
source .venv/bin/activate

# 1) Compute Li MSD (3D, x-y, z) for both models -> CSVs
python analysis/compute_li_msd.py

# 2) Plot MSD vs time FIRST and look at it (choose the fit window from data, not blindly)
python analysis/plot_msd.py

# 3) Fit the linear regime -> diffusion coefficients (window from analysis/fit_windows.json,
#    or override for BOTH models on the command line)
python analysis/fit_diffusion_coefficients.py
python analysis/fit_diffusion_coefficients.py --fit-start 1.0 --fit-end 5.0   # override

# 4) Plot the chosen fit windows over the MSD (auditable)
python analysis/plot_msd_fits.py

# 5) Compare Model B vs Model A (D_B / D_A)
python analysis/compare_diffusion.py
```

### Temperature sweep (optional: all four ramp stages, 300/600/900/1200 K)

```bash
# (a) compute MSDs at every temperature and PRINT regime diagnostics (choose windows from data)
python analysis/msd_temperature_sweep.py --stage diagnose
# (b) after windows are set in analysis/fit_windows_by_temperature.json, fit + plot
python analysis/msd_temperature_sweep.py --stage fit
```

This reuses the exact MSD/fit core (same method), writes per-temperature CSVs under
`analysis/results/by_temperature/`, a combined `diffusion_vs_temperature.csv`/`.json`,
and the figures `phase7_msd_xy_by_temperature_model_{a,b}.png` and
`phase7_apparent_D_xy_vs_temperature.png`. Same caveats apply: z is confined at every
temperature and x-y is super-diffusive where Li move, so the D's stay
**apparent / comparative-only**.

`compute_li_msd.py` accepts `--model-a-traj/--model-b-traj/--dt-fs/--outdir` to
point at a different dataset (e.g. another ramp temperature) with the same method.

## How MSD is calculated

Li atoms only (LAMMPS **type 3**) are selected from the **unwrapped** (`xu yu zu`)
dump. The MSD uses a **multiple-time-origin** average over Li atoms and over all
valid origins:

```
MSD_d(τ) = ⟨ |r_i(t0+τ) − r_i(t0)|²_d ⟩      d ∈ {3D, x-y, z}
```

Each lag τ also stores `n_origins`, so the noisy large-lag tail (few origins) is
visible. The script **aborts** (does not fabricate) if the dump is wrapped-only.

## Why 3D, x-y, and z MSD are all reported

The geometry is anisotropic by design: Li sit **above** the graphene, a reflecting
wall caps z, and the question is whether Li **penetrate through** the sheet.

- **x-y (in-plane)** — lateral Li mobility on/above the sheet.
- **z (interface-normal)** — the **permeation** direction: through-sheet motion is
  the actual research question; a confined z-MSD plateau means Li are *not* crossing.
- **3D** — the total; here it is dominated by x-y (z is confined).

Splitting them is essential: a large 3D MSD could be pure in-plane wandering with
**zero** through-sheet transport, which is exactly what this run shows.

## How diffusion coefficients are fitted

A straight line is least-squares fit to the MSD over the chosen window, and the
slope → D via the Fickian relation `MSD_d = 2·dim·D·τ`:

```
3D : D = slope/6     x-y : D = slope/4     z : D = slope/2
D[cm²/s] = D[Å²/ps] × 1e-4        (1 Å²/ps = 1e-4 cm²/s)
```

Every fit also reports **R²** and a **linearity_ratio** (late-half vs early-half
slope in the window) plus a **regime** label (`approximately linear` /
`super-diffusive` / `confined plateau`) so non-linearity is exposed, not hidden.
Conversion + formulas are centralized in `analysis/msd_utils.py` (same code for A
and B).

## How fitting windows are selected

**After** plotting the MSD (never blindly). Rule:
1. skip the sub-ps ballistic onset;
2. fit only where origins are statistically adequate (`n_origins ≥ ~50%` of frames,
   ≈ lag ≤ 5 ps for a 10 ps / 401-frame run);
3. use the **same** window for both models.

Windows are stored in `analysis/fit_windows.json` (documented per model) and can be
overridden with `--fit-start/--fit-end`.

## Files produced

| File | Contents |
|------|----------|
| `analysis/results/model_a_li_msd.csv` | Model A MSD (time, 3D, x-y, z, n_origins) |
| `analysis/results/model_b_li_msd.csv` | Model B MSD |
| `analysis/results/diffusion_coefficients.csv` | slope, D (Å²/ps, cm²/s), R², linearity, regime |
| `analysis/results/diffusion_summary.json` | same, structured |
| `analysis/results/model_b_over_model_a_ratio.csv` | D_B/D_A per component + verdict |
| `figures/phase7_msd_{3d,xy,z}_model_a_vs_b.png` | A-vs-B MSD comparisons |
| `figures/phase7_model_{a,b}_msd_fit.png` | MSD with fit window + fitted line |

## Pass / fail criteria

**PASS (analysis is valid and honestly reported):**
- MSD computed from unwrapped coords for both models with identical code;
- 3D, x-y, and z MSD all reported;
- fitting window chosen from the plotted data and documented per model;
- unit conversion documented;
- diffusion coefficients reported **with** R²/linearity/regime, and any non-Fickian
  behavior (super-diffusive / confined) stated rather than masked;
- D_B/D_A computed; conclusions are comparative-only with **no real-battery claim**.

**FAIL:** fabricating a diffusion coefficient where no linear region exists; forcing
a fit through a confined plateau and calling it diffusion; using wrapped coordinates
silently; analyzing A and B with different methods/windows; or claiming absolute /
real-battery diffusivities.

> **This run's outcome:** the analysis PASSES as an honest report, but its physics
> conclusion is a **negative/limited** one — the x-y/3D MSD is super-diffusive and z
> is confined over 10 ps with 4 Li, so the diffusion coefficients are **apparent and
> comparative-only**, not physical. A longer, larger, multi-seed production is needed
> for real D values (a future phase).
