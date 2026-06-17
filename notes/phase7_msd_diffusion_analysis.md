# Phase 7 — Li MSD & diffusion analysis (results)

Analysis-only phase: compute Li mean-squared displacement (MSD) from the Phase 6
trajectories, fit the linear regime, convert to diffusion coefficients, and compare
Model B (single-vacancy) vs Model A (pristine). **No new MD. No structure changes.**

> **Headline (read the limitations first):** over this short (10 ps), 4-Li run the
> in-plane / 3D Li MSD is **super-diffusive** (no clean linear/Fickian regime) and
> the z (through-sheet) MSD is a **confined plateau** (Li do not penetrate the
> sheet on this timescale). The diffusion coefficients below are therefore
> **apparent, comparative-only values under this MD protocol — not physical Li
> diffusivities, and say nothing about real battery performance.**

---

## Trajectory files analyzed

| Model | Trajectory | Frames | Li | Length |
|-------|-----------|--------|----|--------|
| A (pristine)        | `trajectories/model_a_ramp_1200K.lammpstrj` | 401 | 4 | 10 ps |
| B (single-vacancy)  | `trajectories/model_b_ramp_1200K.lammpstrj` | 401 | 4 | 10 ps |

**Why the ramp 1200 K trajectories, not `*_production.lammpstrj`?** The listed
`*_production.lammpstrj` files were generated with a **9-Li** configuration that was
later superseded — the current Model A/B structures (and the Phase 4/5 commit) use
**4 Li**. The 4-Li `*_ramp_1200K` stage is at the same 1200 K and is the dataset
**consistent with the current structures**, so it was used for a valid comparison.
Re-running production with 4 Li was out of scope (Phase 7 rule: no new MD). Both
models were analyzed with byte-identical code and the same parameters.

## Li atom selection

Li = **LAMMPS atom type 3** (1 = C, 2 = Si, 3 = Li), selected per frame from the
dump `type` column; both trajectories contain exactly **4 Li**. (`compute_li_msd.py`.)

## Coordinates: wrapped or unwrapped

**Unwrapped** (`xu yu zu`). The Phase 6 dump was written unwrapped specifically so
the MSD is valid across periodic boundaries. `compute_li_msd.py` verifies the dump
columns and **aborts** if only wrapped `x y z` (no image flags) are present rather
than fabricating an MSD. (In OVITO these unwrapped coords make lateral diffusion
look like atoms leaving the box — expected; not used here.)

## Time step and frame spacing

- MD timestep: **0.25 fs** (validated Phases 4/5).
- Dump every **100 steps** → frame spacing = 100 × 0.25 fs = **25 fs = 0.025 ps**.
- 401 frames → lag times 0 … 10.0 ps. Frame spacing is read from the actual dump
  TIMESTEP values (not assumed) and checked for uniformity.

## MSD formula

Multiple-time-origin average over Li atoms **and** all valid time origins:

```
MSD_d(τ) = ⟨ | r_i(t0+τ) − r_i(t0) |²_d ⟩   averaged over i ∈ Li and over t0
  3D : dx² + dy² + dz²      x-y : dx² + dy²      z : dz²
```

Reported per lag with `n_origins` (origins averaged) so the noisy large-lag tail
(few origins) is transparent. No center-of-mass drift removal was applied (kept
simple and identical for A and B; see limitations).

## Diffusion coefficient formula

Fickian long-time limit `MSD_d(τ) = 2·dim·D·τ` ⇒ **D = slope / (2·dim)**:

| Component | dim | D from slope |
|-----------|-----|--------------|
| 3D        | 3   | slope / 6 |
| x-y       | 2   | slope / 4 |
| z         | 1   | slope / 2 |

## Unit conversion

Slope is in Å²/ps. `1 Å = 1e-8 cm` ⇒ `1 Å² = 1e-16 cm²`; `1 ps = 1e-12 s`. So
`1 Å²/ps = 1e-16/1e-12 = 1e-4 cm²/s`, i.e. **D[cm²/s] = D[Å²/ps] × 1e-4**.
(Single source of truth: `analysis/msd_utils.py`.)

## Fitting-window rule

Chosen **after** plotting the MSD (`plot_msd.py`), never blindly:
1. skip the sub-ps ballistic onset;
2. fit only where time origins are statistically adequate (`n_origins ≥ ~50%` of
   frames → lag ≤ ~5 ps);
3. apply the **same** window to both models.

Recorded in `analysis/fit_windows.json`; override with
`--fit-start/--fit-end`. A `linearity_ratio` (late-half slope ÷ early-half slope in
the window) is reported with every fit: ~1 = linear, ≫1 = super-diffusive,
≪1 = saturating.

- **Selected window, Model A:** 1.0 – 5.0 ps (161 points)
- **Selected window, Model B:** 1.0 – 5.0 ps (161 points)

## Results (apparent, comparative-only)

D in cm²/s; `lin` = linearity ratio; regime is the honest classification.

| Model | comp | slope (Å²/ps) | D (cm²/s) | R² | lin | regime |
|-------|------|---------------|-----------|----|-----|--------|
| A | 3D | 290.6 | 4.84e-03 | 0.977 | 1.86 | super-diffusive |
| A | x-y | 290.6 | 7.26e-03 | 0.977 | 1.86 | super-diffusive |
| A | z  | 0.027 | 1.34e-06 | 0.175 | 0.95 | confined plateau |
| B | 3D | 286.7 | 4.78e-03 | 0.997 | 1.08 | ~linear (this window) |
| B | x-y | 286.7 | 7.17e-03 | 0.997 | 1.08 | ~linear (this window) |
| B | z  | −0.040 | −2.0e-06 | 0.254 | −0.47 | confined plateau |

**D_A (apparent):** x-y ≈ 7.3e-03 cm²/s, 3D ≈ 4.8e-03 cm²/s; z ≈ 0 (confined).
**D_B (apparent):** x-y ≈ 7.2e-03 cm²/s, 3D ≈ 4.8e-03 cm²/s; z ≈ 0 (confined).

**D_B / D_A:** 3D = 0.986, x-y = 0.987 (**"similar"**, |ratio−1| ≤ 0.15);
z = undetermined (confined plateau; ratio not physically meaningful).

So **under this protocol the apparent in-plane Li mobility of Model B ≈ Model A
(within ~1.5%)**, and neither model shows Li crossing through the graphene on this
timescale (z confined; B's z plateau sits slightly higher than A's — a hint of
larger z-excursion at the vacancy, but still confined, not diffusive).

## Temperature sweep (all four ramp stages: 300 / 600 / 900 / 1200 K)

The same analysis was run for both models at every ramp temperature
(`analysis/msd_temperature_sweep.py`), using the **identical 1.0–5.0 ps window** for
all (model, T) so temperatures and models are directly comparable. Windows were
chosen after a `--stage diagnose` pass (`analysis/fit_windows_by_temperature.json`).

**Apparent in-plane (x-y) Li D (cm²/s) and regime:**

| T (K) | Model A D_xy | regime A | Model B D_xy | regime B | D_B/D_A (x-y) |
|-------|--------------|----------|--------------|----------|---------------|
| 300  | 1.10e-03 | super-diff | 7.43e-05 | sub-diff (~immobile) | 0.07 |
| 600  | 7.81e-03 | super-diff | 1.20e-03 | super-diff | 0.15 |
| 900  | 1.13e-02 | super-diff | 1.52e-03 | ~linear | 0.13 |
| 1200 | 7.26e-03 | super-diff | 7.17e-03 | ~linear | 0.99 |

**z (through-sheet) MSD is a confined plateau at EVERY temperature for both models**
(plateau mean rises with T: A 0.11→1.40 Å², B 0.32→1.61 Å²) — Li never enter a
z-diffusive regime; they do **not** cross the graphene at any temperature sampled.

**Observation (comparative-only):** apparent in-plane Li mobility rises with
temperature (as expected), and across 300–900 K Model B (single-vacancy) shows
**lower** apparent in-plane mobility than Model A (pristine), converging only at
1200 K. The trend is non-monotonic and noisy because the motion is super-diffusive
(not converged diffusion) and only 4 Li / 10 ps are sampled. **No physical or
real-battery conclusion is drawn.**

Sweep outputs: `analysis/results/by_temperature/model_{a,b}_{T}K_li_msd.csv`,
`analysis/results/diffusion_vs_temperature.csv`/`.json`,
`figures/phase7_msd_xy_by_temperature_model_{a,b}.png`,
`figures/phase7_apparent_D_xy_vs_temperature.png`.

## Limitations

1. **No clean Fickian regime.** The x-y/3D MSD is super-diffusive (apparent D's are
   ~1e-3 cm²/s — ~10³× larger than any physical Li diffusivity), consistent with
   ballistic / drift-dominated motion of a hot, sparse Li layer in a small periodic
   cell, not converged self-diffusion. **Do not quote these as Li diffusivities.**
2. **Tiny statistics:** only **4 Li**, **10 ps**, one trajectory per model → large
   noise, especially at lag > 5 ps (few time origins).
3. **z is confined,** so the through-sheet (permeation) diffusion the project asks
   about cannot be quantified from this run — the z-MSD never enters a diffusive
   regime (Li stay above the sheet).
   - **"z-confined" is a property of the motion, not an imposed boundary.** It does
     **not** mean the reflecting wall held the Li in. The wall is on the **top only**
     (z = 35 Å) and **never acted** (max Li z ≈ 27 Å). The Li are pinned in a narrow
     z-band (RMS ≈ ±1.2 Å) by physics: **the graphene sheet is an energy barrier
     below** (they would have to permeate *through* it to go lower — the research
     question), and **adsorption binding** keeps them ~2.3 Å above the sheet rather
     than desorbing upward. There is no bottom wall — only the fixed bottom Si, far
     below. So "confined" = **the Li are not crossing the graphene**, the meaningful
     (negative) permeation result. Model B's slightly higher z-plateau hints the
     vacancy lets Li probe a bit deeper, but still not through within 10 ps.
4. **No COM-drift correction** was applied; for so few atoms this can inflate the
   apparent MSD. Identical treatment for A and B keeps the comparison fair but does
   not make the absolute values physical.
5. **Comparative only under this MD protocol — no real-battery claim** (Phase 7
   rule #9).

**Recommendation for a physical result:** a longer trajectory (≥ hundreds of ps),
more Li, multiple independent seeds, a constant-T (not ramp) production at the
target temperature, and verification of a true linear MSD region (linearity_ratio
≈ 1) before quoting any D. That is a new production effort (a future phase), not
Phase 7.

## Files produced

- `analysis/results/model_a_li_msd.csv`, `analysis/results/model_b_li_msd.csv`
- `analysis/results/diffusion_coefficients.csv`, `analysis/results/diffusion_summary.json`
- `analysis/results/model_b_over_model_a_ratio.csv`
- `figures/phase7_msd_{3d,xy,z}_model_a_vs_b.png`
- `figures/phase7_model_{a,b}_msd_fit.png`

Temperature sweep (all four ramp stages):
- `analysis/results/by_temperature/model_{a,b}_{300,600,900,1200}K_li_msd.csv`
- `analysis/results/diffusion_vs_temperature.csv`, `analysis/results/diffusion_vs_temperature.json`
- `figures/phase7_msd_xy_by_temperature_model_{a,b}.png`
- `figures/phase7_apparent_D_xy_vs_temperature.png`
