# Phase 2 — Structure Generation: How to Run

Step-by-step guide to build, inspect, and visualize the graphene + Li initial
structure. Phase 2 only — no silicon, no defects, no ReaxFF, no MD, no diffusion.

The physical values come from the project methodology document and are anchored
to cited papers: graphene lattice constant **2.467 Å** (Chou & Hwang [1]), Li
starting height **≈ 2.3 Å** (Chou & Hwang [1]), **≈ 20 Å** z-vacuum (Qin et al.
[2]), and a **48‑C rectangular sheet** matching Chou & Hwang [1]'s
12.8187 × 9.8680 Å² precedent. The Li count (6) is a documented project choice.
See `structures/README.md` for full sources and rationale.

---

## 0. Install Python dependencies

A virtual environment keeps this reproducible and avoids touching system Python.

```bash
# From the repository root:
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

(The `.venv/` directory is git-ignored.)

## 1. Run the build script

```bash
python structures/build_graphene_li.py
# optional: choose sheet size (in orthorhombic cells) / Li count
python structures/build_graphene_li.py --nx 4 --ny 3 --n-li 6
```

Produces:
- `structures/graphene_li.xyz`
- `structures/graphene_li.data`

Expected summary (default parameters): 48 C + 6 Li = 54 atoms,
box 9.868 × 12.819 × 22.300 Å.

## 2. Run the inspection script

```bash
python analysis/inspect_structure.py
# or point it at a specific file:
python analysis/inspect_structure.py structures/graphene_li.data
```

Expected: 48 C, 6 Li, 54 total; C–C ≈ 1.424 Å; min Li–C ≈ 2.369 Å; and
`OK: no obvious overlaps`. A non-zero exit + `OVERLAP WARNING` means something
is wrong with the geometry.

## 3. Open in OVITO

1. Launch **OVITO**.
2. `File → Load File…` → select `structures/graphene_li.xyz`
   (or `structures/graphene_li.data`).
3. Confirm: a flat hexagonal graphene sheet with 6 Li atoms in a layer above it.

## 4. Save a validation screenshot

In OVITO, render/screenshot a clear view (top + perspective is ideal) and save to:

```
figures/phase2_graphene_li_initial_structure.png
```

## 5. Tick the checklist

Complete `notes/phase2_graphene_li_validation.md`. When every box is checked and
the screenshot exists, Phase 2 is done.

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `ModuleNotFoundError: ase` | Activate the venv and re-run `pip install -r requirements.txt`. |
| `structure file not found` | Run the build script first (step 1). |
| `OVERLAP WARNING` | Check `--n-li` isn't too large for the sheet; rebuild with defaults. |
| OVITO won't load `.xyz` | Use the `.data` file instead, or confirm the file is non-empty. |
