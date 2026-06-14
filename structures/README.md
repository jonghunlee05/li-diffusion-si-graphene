# structures/ — Phase 2: graphene + Li initial structure

This directory holds the structure builder and its generated output for
**Phase 2** of the project.

## What Phase 2 is

Phase 2 creates and validates a **reproducible graphene + lithium initial
structure**. It is the first structure-building step. Nothing here is a
scientific result — it is an initial geometry to be inspected and visualized.

**Phase 2 explicitly does NOT:** add silicon, add graphene defects, use ReaxFF,
run MD, or compute MSD/diffusion. Those come in later phases.

## Generated files

Run `python structures/build_graphene_li.py` to (re)generate:

| File | Description |
|------|-------------|
| `graphene_li.xyz` | Extended-XYZ (elements + periodic cell). Easy to open in OVITO and re-readable by the inspector. |
| `graphene_li.data` | LAMMPS data file, `atom_style atomic`, with a Masses block. Type 1 = C, type 2 = Li. |

These outputs are git-ignored (regenerable from the script).

## Current structure (default parameters)

| Property | Value | Source |
|----------|-------|--------|
| Graphene sheet | 48 C, rectangular | Chou & Hwang [1] precedent (12.8187 × 9.8680 Å²) |
| Built as | 4 × 3 orthorhombic graphene cells | — |
| Carbon atoms | 48 | Chou & Hwang [1] |
| Lithium atoms | 6 | documented project choice |
| Total atoms | 54 | — |
| Graphene lattice constant | **2.467 Å** | Chou & Hwang [1] (exp ≈ 2.46 Å) |
| Li starting height above graphene | **2.3 Å** | Chou & Hwang [1] |
| z-vacuum (total) | **20.0 Å** | Qin et al. [2] |
| Box (Å) | 9.868 × 12.819 × 22.300 | matches Chou & Hwang [1] sheet (axes transposed) |
| C–C nearest-neighbor distance | 1.424 Å | = 2.467/√3 (ideal graphene ≈ 1.42 Å) |
| Minimum Li–C distance | 2.369 Å | — |

References [1], [2] follow the methodology document's numbering
(Chou & Hwang 2013; Qin et al. 2021). Size and Li count are adjustable via
`--nx`, `--ny`, `--n-li`.

## Provenance — every number is sourced or documented

Per the methodology document (§3, §4.1, §5), Phase 2 parameters split into two
kinds, and **no number is invented**:

**Literature-backed anchors** (physical values from cited papers):
- **Lattice constant 2.467 Å** — Chou & Hwang [1] (experimental ≈ 2.46 Å).
- **Li height ≈ 2.3 Å** — Chou & Hwang [1], verbatim: *"the first layer
  (|z| ≈ 1.7 to 3.0 Å) comprises only Li atoms with the average Li‑Gr distance
  around 2.3 Å."* A *starting placement* to avoid overlap, **not** an equilibrium
  adsorption distance (relaxed in later phases).
  - **Decision — 2.3 Å, not 1.73 Å.** The same paper also reports *"1.73 Å for
    single Li adsorption on graphene"* (isolated bare-graphene value). We use
    **2.3 Å** because: (a) the project target system is the Si–graphene
    **composite** interface, for which 2.3 Å is Chou & Hwang's own
    interface-layer distance; (b) the height is only a pre-relaxation placeholder
    and does not affect results (minimization moves Li to the potential's energy
    minimum regardless); and (c) 2.3 Å is the larger, overlap-safe gap. The
    silicon-free Phase 2 sheet is a build stepping stone, not a single-adsorption
    study, so 2.3 Å is the correct anchor. The methodology document (§5) also
    selects 2.3 Å. Both quotes are from Chou & Hwang 2013 (*J. Phys. Chem. C*
    117, 9598–9604) [1].
- **Vacuum ≈ 20 Å** — Qin et al. [2]'s isolated-graphene vacuum.
- **48‑C rectangular sheet** — Chou & Hwang [1]'s 12.8187 × 9.8680 Å² sheet,
  adopted so the sheet size is paper-anchored rather than arbitrary.

**Documented project choices** (the methodology explicitly classifies these as
project choices, §4.1: *"Exact Phase 2 sheet size and Li count remain documented
project choices"*):
- **Li count = 6** — no cited paper specifies an *isolated* graphene+Li loading;
  the only literature Li loading (30 Li, Si et al. [9]) is for a 30‑Si
  **composite** cell and is not transferable to a silicon-free sheet. A small
  count is chosen to keep the visualization structure overlap-free.

These exist only to produce a clean initial structure for visualization and
sanity checking (§5: *"Visual validation only; not final science model"*).
Equilibrium geometry comes later, once real interatomic potentials are selected
and the system is relaxed.

## See also

- `analysis/inspect_structure.py` — geometry sanity report.
- `docs/phase2_structure_generation.md` — how to run Phase 2 end to end.
- `notes/phase2_graphene_li_validation.md` — validation checklist.
