#!/usr/bin/env bash
set +e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

LOG_DIR="experiments/ref_gs_limitation_analysis/sanity_logs"
mkdir -p "$LOG_DIR"
ROUND_NAME="${ROUND_NAME:-round3}"
SUMMARY="$LOG_DIR/component_sanity_${ROUND_NAME}_summary.md"
TRAIN_LOG="$LOG_DIR/component_sanity_${ROUND_NAME}_train.log"
EXPORT_LOG="$LOG_DIR/component_sanity_${ROUND_NAME}_export.log"
EVAL_LOG="$LOG_DIR/component_sanity_${ROUND_NAME}_eval.log"
MESH_LOG="$LOG_DIR/component_sanity_${ROUND_NAME}_mesh.log"

RUN_TRAIN="${RUN_TRAIN:-0}"
RUN_EXPORT="${RUN_EXPORT:-1}"
RUN_EVAL="${RUN_EVAL:-1}"
RUN_MESH="${RUN_MESH:-0}"
MESH_DRY_RUN="${MESH_DRY_RUN:-1}"
STRICT="${STRICT:-0}"
SANITY_ITER="${SANITY_ITER:-2}"
SANITY_SCRIPT="${SANITY_SCRIPT:-train.py}"
SANITY_EXTRA="${SANITY_EXTRA:-}"
SCENE_PATH="${SCENE_PATH:-${SANITY_SCENE:-/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball}}"
MODEL_PATH="${MODEL_PATH:-output/ref_gs_limitation_sanity/ball_iter${SANITY_ITER}}"
EXPORT_DIR="${EXPORT_DIR:-experiments/ref_gs_limitation_analysis/exports/component_sanity_round3_ball}"
METRIC_DIR="${METRIC_DIR:-experiments/ref_gs_limitation_analysis/metrics/component_sanity_round3_ball_pbr_eval}"
MESH_PATH="${MESH_PATH:-experiments/ref_gs_limitation_analysis/meshes/component_sanity_ball/mesh.ply}"
RENDER_FUNC="${RENDER_FUNC:-auto}"

: > "$TRAIN_LOG"
: > "$EXPORT_LOG"
: > "$EVAL_LOG"
: > "$MESH_LOG"

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
  echo "# Component Sanity ${ROUND_NAME} Summary"
  echo
  echo "- env_check_exit: $ENV_STATUS"
  echo "- activate_exit: $ACTIVATE_STATUS"
  echo "- python: \`$(command -v python || true)\`"
  echo "- python_version: \`$(python --version 2>&1 || true)\`"
  echo "- RUN_TRAIN: $RUN_TRAIN"
  echo "- RUN_EXPORT: $RUN_EXPORT"
  echo "- RUN_EVAL: $RUN_EVAL"
  echo "- RUN_MESH: $RUN_MESH"
  echo "- STRICT: $STRICT"
  echo "- SANITY_SCRIPT: \`$SANITY_SCRIPT\`"
  echo "- SANITY_ITER: $SANITY_ITER"
  echo "- SANITY_EXTRA: \`$SANITY_EXTRA\`"
  echo "- SCENE_PATH: \`$SCENE_PATH\`"
  echo "- MODEL_PATH: \`$MODEL_PATH\`"
  echo "- RENDER_FUNC: \`$RENDER_FUNC\`"
} > "$SUMMARY"

if [ "$RUN_TRAIN" = "1" ]; then
  echo "Running ${SANITY_ITER}-iteration training sanity with ${SANITY_SCRIPT}..."
  mkdir -p "$(dirname "$MODEL_PATH")"
  # shellcheck disable=SC2086
  python "$SANITY_SCRIPT" \
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
    $SANITY_EXTRA \
    > "$TRAIN_LOG" 2>&1
  TRAIN_STATUS=$?
else
  echo "RUN_TRAIN is not 1; skipping training." | tee "$TRAIN_LOG" >/dev/null
  TRAIN_STATUS=99
fi

CHECKPOINT="$MODEL_PATH/chkpnt${SANITY_ITER}.pth"
EXPORT_STATUS=99
EVAL_STATUS=99
MESH_STATUS=99

if [ "$RUN_EXPORT" = "1" ]; then
  if [ -f "$CHECKPOINT" ]; then
    python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
      --source_path "$SCENE_PATH" \
      --model_path "$MODEL_PATH" \
      --checkpoint "$CHECKPOINT" \
      --split test \
      --max_views 1 \
      --return_components \
      --render_func "$RENDER_FUNC" \
      --out_dir "$EXPORT_DIR" \
      >> "$EXPORT_LOG" 2>&1
    EXPORT_STATUS=$?
  else
    python experiments/ref_gs_limitation_analysis/export_pbr_views.py --dry-run \
      --source_path "$SCENE_PATH" \
      --model_path "$MODEL_PATH" \
      --checkpoint "$CHECKPOINT" \
      --split test \
      --max_views 1 \
      --return_components \
      --render_func "$RENDER_FUNC" \
      --out_dir "$EXPORT_DIR" \
      >> "$EXPORT_LOG" 2>&1
    EXPORT_STATUS=$?
  fi
else
  echo "RUN_EXPORT is not 1; skipping export." >> "$EXPORT_LOG"
fi

if [ "$RUN_EVAL" = "1" ]; then
  python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
    --export_dir "$EXPORT_DIR" \
    --out "$METRIC_DIR" \
    >> "$EVAL_LOG" 2>&1
  EVAL_STATUS=$?
  VALID_VIEW_COUNT="$(python - "$METRIC_DIR/summary_metrics.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    print(0)
else:
    summary = json.loads(p.read_text(encoding="utf-8"))
    print(sum(int(v.get("valid_views", 0)) for v in summary.get("targets", {}).values()))
PY
)"
else
  echo "RUN_EVAL is not 1; skipping PBR eval." >> "$EVAL_LOG"
  VALID_VIEW_COUNT=0
fi

if [ "$RUN_MESH" = "1" ]; then
  MESH_ARGS=()
  if [ "$MESH_DRY_RUN" = "1" ] || [ ! -f "$CHECKPOINT" ]; then
    MESH_ARGS+=(--dry-run)
  else
    MESH_ARGS+=(--checkpoint "$CHECKPOINT")
  fi
  python experiments/ref_gs_limitation_analysis/export_mesh.py \
    --source_path "$SCENE_PATH" \
    --model_path "$MODEL_PATH" \
    --split test \
    --max_views 3 \
    --depth_ratio 1.0 \
    --render_func "$RENDER_FUNC" \
    --out_mesh "$MESH_PATH" \
    "${MESH_ARGS[@]}" \
    >> "$MESH_LOG" 2>&1
  MESH_STATUS=$?
  MESH_MANIFEST="$(dirname "$MESH_PATH")/mesh_manifest.json"
  MESH_MANIFEST_STATUS="$(python - "$MESH_MANIFEST" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
if p.exists():
    print(json.loads(p.read_text(encoding="utf-8")).get("status", "missing"))
else:
    print("missing")
PY
)"
else
  echo "RUN_MESH is not 1; skipping mesh export." >> "$MESH_LOG"
  MESH_MANIFEST_STATUS="skipped"
fi

STRICT_STATUS=0
if [ "$STRICT" = "1" ]; then
  if [ "$RUN_TRAIN" = "1" ] && [ "$TRAIN_STATUS" -ne 0 ]; then
    STRICT_STATUS=1
  fi
  if [ "$RUN_TRAIN" = "1" ] && [ ! -f "$CHECKPOINT" ]; then
    STRICT_STATUS=1
  fi
  if [ "$RUN_EXPORT" = "1" ] && [ "$EXPORT_STATUS" -ne 0 ]; then
    STRICT_STATUS=1
  fi
  if [ "$RUN_EVAL" = "1" ] && { [ "$EVAL_STATUS" -ne 0 ] || [ "${VALID_VIEW_COUNT:-0}" -eq 0 ]; }; then
    STRICT_STATUS=1
  fi
  if [ "$RUN_MESH" = "1" ] && { [ "$MESH_STATUS" -ne 0 ] || { [ "$MESH_DRY_RUN" != "1" ] && [ "$MESH_MANIFEST_STATUS" != "ok" ]; }; }; then
    STRICT_STATUS=1
  fi
fi

{
  echo "- train_exit: $TRAIN_STATUS"
  echo "- checkpoint: \`$CHECKPOINT\`"
  echo "- checkpoint_exists: $([ -f "$CHECKPOINT" ] && echo true || echo false)"
  echo "- export_exit: $EXPORT_STATUS"
  echo "- eval_exit: $EVAL_STATUS"
  echo "- eval_valid_view_count: ${VALID_VIEW_COUNT:-0}"
  echo "- mesh_exit: $MESH_STATUS"
  echo "- mesh_manifest_status: ${MESH_MANIFEST_STATUS:-skipped}"
  echo "- strict_exit: $STRICT_STATUS"
  echo "- train_log: \`$TRAIN_LOG\`"
  echo "- export_log: \`$EXPORT_LOG\`"
  echo "- eval_log: \`$EVAL_LOG\`"
  echo "- mesh_log: \`$MESH_LOG\`"
  echo "- export_dir: \`$EXPORT_DIR\`"
  echo "- metric_dir: \`$METRIC_DIR\`"
  echo "- mesh_path: \`$MESH_PATH\`"
} >> "$SUMMARY"

echo "Wrote $SUMMARY"
if [ "$STRICT" = "1" ]; then
  exit "$STRICT_STATUS"
fi
exit 0
