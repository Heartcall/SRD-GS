#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=1
CONFIG_PATH="configs/srd_gs/full_srd_gs_branch_raster.yaml"
SCENE_PATH="/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball"
MODEL_ROOT=""
OUTPUT_ROOT="outputs/srd_gs_branch_raster_smoke"
SCENE_NAME="ball"
ITERATIONS="20"
MAX_MESH_VIEWS="8"
DEPTH_TRUNC="10.0"
MAX_TEXTURE_VIEWS="4"
MAX_EVAL_VIEWS="2"
GEOMETRY_SAMPLE_COUNT="1000"
FSCORE_THRESHOLD="0.01"
CONDA_ENV_PREFIX="${CONDA_ENV_PREFIX:-/home/liuly/anaconda3/envs/ref_gs}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH="$2"; shift 2 ;;
    --scene_path) SCENE_PATH="$2"; shift 2 ;;
    --model_root) MODEL_ROOT="$2"; shift 2 ;;
    --output_root) OUTPUT_ROOT="$2"; shift 2 ;;
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

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found: $CONFIG_PATH" >&2
  exit 2
fi

read_config_value() {
  local key="$1"
  grep -E "^${key}:" "$CONFIG_PATH" | head -n 1 | sed -E "s/^${key}:[[:space:]]*//; s/^\"//; s/\"$//" || true
}

VARIANT_NAME="$(read_config_value name)"
TRAIN_ARGS="$(read_config_value train_args)"
TRAIN_ONLY_ARGS="$(read_config_value train_only_args)"
MESH_MODE="$(read_config_value mesh_mode)"
TEXTURE_MODE="$(read_config_value texture_mode)"
EVAL_ENABLED="$(read_config_value eval_enabled)"

if [[ -z "$VARIANT_NAME" || -z "$MESH_MODE" || -z "$TEXTURE_MODE" ]]; then
  echo "Config must define name, mesh_mode, and texture_mode: $CONFIG_PATH" >&2
  exit 2
fi

MODEL_PATH="${MODEL_ROOT:-$OUTPUT_ROOT/models}/${SCENE_NAME}/${VARIANT_NAME}"
RESULT_PATH="$OUTPUT_ROOT/results/${SCENE_NAME}/${VARIANT_NAME}"
PAIR_DIR="$RESULT_PATH/render_eval_pairs"
EVAL_DIR="$RESULT_PATH/eval_with_gt_mesh"
MESH_PATH="$RESULT_PATH/mesh_${MESH_MODE}.ply"
TEXTURE_DIR="$RESULT_PATH/pbr_textures_${TEXTURE_MODE}"

mkdir -p "$RESULT_PATH" "$PAIR_DIR" "$EVAL_DIR"
export LD_LIBRARY_PATH="$CONDA_ENV_PREFIX/lib:${LD_LIBRARY_PATH:-}"

SRD_ARGS=()
if [[ -n "$TRAIN_ARGS" ]]; then
  # shellcheck disable=SC2206
  SRD_ARGS=($TRAIN_ARGS)
fi
TRAIN_ONLY_ARGS_ARRAY=()
if [[ -n "$TRAIN_ONLY_ARGS" ]]; then
  # shellcheck disable=SC2206
  TRAIN_ONLY_ARGS_ARRAY=($TRAIN_ONLY_ARGS)
fi

TRAIN_CMD=(conda run -n ref_gs python train.py -s "$SCENE_PATH" -m "$MODEL_PATH" --iterations "$ITERATIONS")
if [[ "$EVAL_ENABLED" == "true" ]]; then
  TRAIN_CMD+=(--eval)
fi
TRAIN_CMD+=("${SRD_ARGS[@]}")
TRAIN_CMD+=("${TRAIN_ONLY_ARGS_ARRAY[@]}")

MESH_CMD=(
  conda run -n ref_gs python extract_surface_mesh.py
  -s "$SCENE_PATH"
  -m "$MODEL_PATH"
  --iteration "$ITERATIONS"
  --mesh_mode "$MESH_MODE"
  --output_path "$MESH_PATH"
  --depth_trunc "$DEPTH_TRUNC"
)
if [[ "$MAX_MESH_VIEWS" != "0" ]]; then
  MESH_CMD+=(--max_views "$MAX_MESH_VIEWS")
fi

TEXTURE_CMD=(
  conda run -n ref_gs python export_pbr_textures.py
  -s "$SCENE_PATH"
  -m "$MODEL_PATH"
  --iteration "$ITERATIONS"
  --mode "$TEXTURE_MODE"
  --output_dir "$TEXTURE_DIR"
  "${SRD_ARGS[@]}"
)
if [[ "$MAX_TEXTURE_VIEWS" != "0" ]]; then
  TEXTURE_CMD+=(--max_views "$MAX_TEXTURE_VIEWS")
fi

RENDER_CMD=(
  conda run -n ref_gs python render_eval_pairs.py
  -s "$SCENE_PATH"
  -m "$MODEL_PATH"
  --iteration "$ITERATIONS"
  --split test
  --max_views "$MAX_EVAL_VIEWS"
  --output_dir "$PAIR_DIR"
  --auto_reflective_mask
  "${SRD_ARGS[@]}"
)

EVAL_CMD=(
  conda run -n ref_gs python eval_reflective_assets.py
  --eval_pairs_dir "$PAIR_DIR"
  --pred_geometry "$MESH_PATH"
  --source_path "$SCENE_PATH"
  --geometry_sample_count "$GEOMETRY_SAMPLE_COUNT"
  --fscore_threshold "$FSCORE_THRESHOLD"
  --output_dir "$EVAL_DIR"
  --auto_reflective_mask
)

printf '%q ' "${TRAIN_CMD[@]}" > "$RESULT_PATH/train_command.txt"; printf '\n' >> "$RESULT_PATH/train_command.txt"
printf '%q ' "${MESH_CMD[@]}" > "$RESULT_PATH/mesh_command.txt"; printf '\n' >> "$RESULT_PATH/mesh_command.txt"
printf '%q ' "${TEXTURE_CMD[@]}" > "$RESULT_PATH/texture_command.txt"; printf '\n' >> "$RESULT_PATH/texture_command.txt"
printf '%q ' "${RENDER_CMD[@]}" > "$RESULT_PATH/render_eval_pairs_command.txt"; printf '\n' >> "$RESULT_PATH/render_eval_pairs_command.txt"
printf '%q ' "${EVAL_CMD[@]}" > "$RESULT_PATH/eval_gt_mesh_command.txt"; printf '\n' >> "$RESULT_PATH/eval_gt_mesh_command.txt"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN=1"
  echo "Commands written to $RESULT_PATH"
  exit 0
fi

"${TRAIN_CMD[@]}"
"${MESH_CMD[@]}"
"${TEXTURE_CMD[@]}"
"${RENDER_CMD[@]}"
"${EVAL_CMD[@]}"
