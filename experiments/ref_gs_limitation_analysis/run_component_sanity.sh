#!/usr/bin/env bash
set +e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

LOG_DIR="experiments/ref_gs_limitation_analysis/sanity_logs"
mkdir -p "$LOG_DIR"
SUMMARY="$LOG_DIR/component_sanity_summary.md"
TRAIN_LOG="$LOG_DIR/component_sanity_train.log"
EXPORT_LOG="$LOG_DIR/component_sanity_export.log"
EVAL_LOG="$LOG_DIR/component_sanity_eval.log"

RUN_TRAIN="${RUN_TRAIN:-0}"
SANITY_ITER="${SANITY_ITER:-2}"
SCENE_PATH="${SCENE_PATH:-/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball}"
MODEL_PATH="${MODEL_PATH:-output/ref_gs_limitation_sanity/ball_iter${SANITY_ITER}}"
EXPORT_DIR="${EXPORT_DIR:-experiments/ref_gs_limitation_analysis/exports/component_sanity_ball}"
METRIC_DIR="${METRIC_DIR:-experiments/ref_gs_limitation_analysis/metrics/component_sanity_ball_pbr_eval}"

: > "$EXPORT_LOG"
: > "$EVAL_LOG"

bash experiments/ref_gs_limitation_analysis/env_check.sh
ENV_STATUS=$?

for candidate in \
  "$HOME/miniconda3/etc/profile.d/conda.sh" \
  "$HOME/anaconda3/etc/profile.d/conda.sh" \
  "/opt/conda/etc/profile.d/conda.sh"
do
  if [ -f "$candidate" ]; then
    # shellcheck source=/dev/null
    source "$candidate"
    break
  fi
done
conda activate ref_gs
ACTIVATE_STATUS=$?

{
  echo "# Component Sanity Summary"
  echo
  echo "- env_check_exit: $ENV_STATUS"
  echo "- activate_exit: $ACTIVATE_STATUS"
  echo "- python: \`$(command -v python || true)\`"
  echo "- python_version: \`$(python --version 2>&1 || true)\`"
  echo "- RUN_TRAIN: $RUN_TRAIN"
  echo "- SANITY_ITER: $SANITY_ITER"
  echo "- SCENE_PATH: \`$SCENE_PATH\`"
  echo "- MODEL_PATH: \`$MODEL_PATH\`"
} > "$SUMMARY"

if [ "$RUN_TRAIN" = "1" ]; then
  echo "Running ${SANITY_ITER}-iteration training sanity..."
  mkdir -p "$(dirname "$MODEL_PATH")"
  python train.py \
    -s "$SCENE_PATH" \
    --eval \
    --resolution 8 \
    --run_dim 64 \
    --albedo_bias 0 \
    --iterations "$SANITY_ITER" \
    --save_iterations "$SANITY_ITER" \
    --checkpoint_iterations "$SANITY_ITER" \
    --test_iterations "$SANITY_ITER" \
    --model_path "$MODEL_PATH" \
    > "$TRAIN_LOG" 2>&1
  TRAIN_STATUS=$?
else
  echo "RUN_TRAIN is not 1; skipping actual training." | tee "$TRAIN_LOG"
  TRAIN_STATUS=99
fi

{
  echo "- train_exit: $TRAIN_STATUS"
  echo "- train_log: \`$TRAIN_LOG\`"
} >> "$SUMMARY"

CHECKPOINT="$MODEL_PATH/chkpnt${SANITY_ITER}.pth"
if [ -f "$CHECKPOINT" ]; then
  python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
    --source_path "$SCENE_PATH" \
    --model_path "$MODEL_PATH" \
    --checkpoint "$CHECKPOINT" \
    --split test \
    --max_views 1 \
    --out_dir "$EXPORT_DIR" \
    >> "$EXPORT_LOG" 2>&1
  EXPORT_STATUS=$?
else
  python experiments/ref_gs_limitation_analysis/export_pbr_views.py --dry-run \
    --source_path "$SCENE_PATH" \
    --model_path "$MODEL_PATH" \
    --split test \
    --max_views 1 \
    --out_dir "$EXPORT_DIR" \
    >> "$EXPORT_LOG" 2>&1
  EXPORT_STATUS=$?
fi

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir "$EXPORT_DIR" \
  --out "$METRIC_DIR" \
  >> "$EVAL_LOG" 2>&1
EVAL_STATUS=$?

{
  echo "- checkpoint: \`$CHECKPOINT\`"
  echo "- checkpoint_exists: $([ -f "$CHECKPOINT" ] && echo true || echo false)"
  echo "- export_exit: $EXPORT_STATUS"
  echo "- eval_exit: $EVAL_STATUS"
  echo "- export_log: \`$EXPORT_LOG\`"
  echo "- eval_log: \`$EVAL_LOG\`"
  echo "- export_dir: \`$EXPORT_DIR\`"
  echo "- metric_dir: \`$METRIC_DIR\`"
} >> "$SUMMARY"

echo "Wrote $SUMMARY"
exit 0
