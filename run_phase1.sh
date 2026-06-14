#!/usr/bin/env bash
# =====================================================================
# run_phase1.sh  —  Phase 1 toolchain validation runner
# =====================================================================
# Chains the non-interactive Phase 1 steps:
#   1. Auto-detect the LAMMPS binary.
#   2. Run the Lennard-Jones test (lammps_inputs/in.lj_test).
#   3. Check that the log + trajectory were produced.
#   4. Plot temperature/energy from the log into figures/.
#
# It does NOT cover the OVITO screenshot (step 4 in the notes) — that is a
# manual GUI step. See notes/phase1_environment_validation.md.
#
# Usage:
#   ./run_phase1.sh
#   LMP=lmp_serial ./run_phase1.sh      # force a specific LAMMPS binary
#
# This runs the trivial LJ smoke test only — no real materials, no real
# force-field parameters, no scientific results.
# =====================================================================

# Stop on first error, treat unset vars as errors, fail on any pipe stage.
set -euo pipefail

# Resolve the repository root as the directory containing this script, so the
# script works no matter where it is called from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Pick a Python interpreter (prefer python3).
PYTHON="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON" ]]; then
    echo "ERROR: no python3/python found on PATH." >&2
    exit 1
fi

# ---- 1. Detect the LAMMPS binary -------------------------------------
# Honor an explicit override via the LMP environment variable; otherwise try
# the common binary names in order.
if [[ -n "${LMP:-}" ]]; then
    LMP_BIN="$LMP"
else
    LMP_BIN=""
    for candidate in lmp lmp_serial lmp_mpi lammps; do
        if command -v "$candidate" >/dev/null 2>&1; then
            LMP_BIN="$candidate"
            break
        fi
    done
fi

if [[ -z "$LMP_BIN" ]] || ! command -v "$LMP_BIN" >/dev/null 2>&1; then
    echo "ERROR: could not find a LAMMPS binary (tried: lmp, lmp_serial, lmp_mpi, lammps)." >&2
    echo "       Install LAMMPS or set LMP=<your-binary> and re-run." >&2
    exit 1
fi
echo ">>> Using LAMMPS binary : $LMP_BIN"
echo ">>> Using Python        : $PYTHON"
echo

# ---- 2. Run the Lennard-Jones test -----------------------------------
echo ">>> [1/3] Running LJ test (lammps_inputs/in.lj_test) ..."
( cd lammps_inputs && "$LMP_BIN" -in in.lj_test )
echo

# ---- 3. Check outputs ------------------------------------------------
echo ">>> [2/3] Checking outputs ..."
"$PYTHON" analysis/check_outputs.py --dir lammps_inputs
echo

# ---- 4. Plot the log -------------------------------------------------
echo ">>> [3/3] Plotting log ..."
"$PYTHON" analysis/plot_lammps_log.py lammps_inputs/log.lammps
echo

echo "============================================================"
echo "Automated Phase 1 steps complete."
echo "Remaining MANUAL step: open lammps_inputs/dump.lj_test.lammpstrj"
echo "in OVITO and save figures/ovito_validation.png"
echo "(see notes/phase1_environment_validation.md, Step 4)."
echo "============================================================"
