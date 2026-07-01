#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=1
SCENE_PATH="/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball"
OUTPUT_ROOT="outputs/srd_gs_single_scene_comparison"
MODEL_ROOT=""
SCENE_NAME="ball"
ITERATIONS="60"
MAX_MESH_VIEWS="8"
DEPTH_TRUNC="10.0"
MAX_TEXTURE_VIEWS="4"
MAX_EVAL_VIEWS="2"
GEOMETRY_SAMPLE_COUNT="1000"
FSCORE_THRESHOLD="0.01"
CONFIGS=(
  "configs/srd_gs/refgs_baseline.yaml"
  "configs/srd_gs/full_srd_gs.yaml"
  "configs/srd_gs/full_srd_gs_branch_raster.yaml"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene_path) SCENE_PATH="$2"; shift 2 ;;
    --output_root) OUTPUT_ROOT="$2"; shift 2 ;;
    --model_root) MODEL_ROOT="$2"; shift 2 ;;
    --scene_name) SCENE_NAME="$2"; shift 2 ;;
    --iterations) ITERATIONS="$2"; shift 2 ;;
    --max_mesh_views) MAX_MESH_VIEWS="$2"; shift 2 ;;
    --depth_trunc) DEPTH_TRUNC="$2"; shift 2 ;;
    --max_texture_views) MAX_TEXTURE_VIEWS="$2"; shift 2 ;;
    --max_eval_views) MAX_EVAL_VIEWS="$2"; shift 2 ;;
    --geometry_sample_count) GEOMETRY_SAMPLE_COUNT="$2"; shift 2 ;;
    --fscore_threshold) FSCORE_THRESHOLD="$2"; shift 2 ;;
    --execute) DRY_RUN=0; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUTPUT_ROOT/tables"

RUNNER_ARGS=(
  --scene_path "$SCENE_PATH"
  --output_root "$OUTPUT_ROOT"
  --scene_name "$SCENE_NAME"
  --iterations "$ITERATIONS"
  --max_mesh_views "$MAX_MESH_VIEWS"
  --depth_trunc "$DEPTH_TRUNC"
  --max_texture_views "$MAX_TEXTURE_VIEWS"
  --max_eval_views "$MAX_EVAL_VIEWS"
  --geometry_sample_count "$GEOMETRY_SAMPLE_COUNT"
  --fscore_threshold "$FSCORE_THRESHOLD"
)
if [[ -n "$MODEL_ROOT" ]]; then
  RUNNER_ARGS+=(--model_root "$MODEL_ROOT")
fi
if [[ "$DRY_RUN" == "0" ]]; then
  RUNNER_ARGS+=(--execute)
fi

for config_path in "${CONFIGS[@]}"; do
  scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config "$config_path" "${RUNNER_ARGS[@]}"
done

SUMMARY_CMD=(
  python scripts/srd_gs/collect_results.py
  --results_root "$OUTPUT_ROOT/results"
  --output_csv "$OUTPUT_ROOT/tables/${SCENE_NAME}_metric_summary.csv"
)
printf '%q ' "${SUMMARY_CMD[@]}" > "$OUTPUT_ROOT/tables/collect_metric_summary_command.txt"
printf '\n' >> "$OUTPUT_ROOT/tables/collect_metric_summary_command.txt"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN=1"
  echo "Variant commands written under $OUTPUT_ROOT/results/$SCENE_NAME"
  echo "Summary command written to $OUTPUT_ROOT/tables/collect_metric_summary_command.txt"
  exit 0
fi

"${SUMMARY_CMD[@]}"
