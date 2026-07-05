#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

CONDA_SH="${CONDA_SH:-/home/liuly/anaconda3/etc/profile.d/conda.sh}"
LOG_DIR="experiments/ref_gs_limitation_analysis/sanity_logs"
mkdir -p "$LOG_DIR"

if [ -f "$CONDA_SH" ]; then
  # shellcheck source=/dev/null
  source "$CONDA_SH"
  conda activate ref_gs
else
  echo "conda init script not found at $CONDA_SH; falling back to conda run"
fi

PYTHON_BIN="$(command -v python || true)"
echo "python=${PYTHON_BIN}"
python --version || true

SANITY_SCRIPT="${SANITY_SCRIPT:-train.py}"
SANITY_SCENE="${SANITY_SCENE:-/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball}"
SANITY_MODEL="${SANITY_MODEL:-/tmp/ref_gs_limitation_sanity}"
SANITY_EXTRA="${SANITY_EXTRA:---eval --run_dim 64 --albedo_bias 0}"

echo "script=${SANITY_SCRIPT}"
echo "scene=${SANITY_SCENE}"
echo "model=${SANITY_MODEL}"
echo "extra=${SANITY_EXTRA}"

python "$SANITY_SCRIPT" --help > "$LOG_DIR/${SANITY_SCRIPT%.py}_help.txt"
echo "help_ok=$?"

if [ ! -d "$SANITY_SCENE" ]; then
  echo "Scene not found: $SANITY_SCENE"
  exit 2
fi

if [ "${RUN_TRAIN:-0}" != "1" ]; then
  echo "RUN_TRAIN is not 1; dry sanity stops after help/path validation."
  echo "To run a 2-iteration sanity: RUN_TRAIN=1 bash $0"
  exit 0
fi

set -x
python "$SANITY_SCRIPT" \
  -s "$SANITY_SCENE" \
  --iterations 2 \
  --save_iterations 1 2 \
  --test_iterations 1 2 \
  --model_path "$SANITY_MODEL" \
  $SANITY_EXTRA \
  2>&1 | tee "$LOG_DIR/${SANITY_SCRIPT%.py}_train_i2.log"
status=${PIPESTATUS[0]}
set +x
exit "$status"
