#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=1
CONFIG_PATH=""
SOURCE_PATH=""
MODEL_ROOT=""
OUTPUT_ROOT=""
ITERATIONS="31000"
SCENE_NAME="scene"
MAX_MESH_VIEWS="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH="$2"; shift 2 ;;
    --source_path) SOURCE_PATH="$2"; shift 2 ;;
    --model_root) MODEL_ROOT="$2"; shift 2 ;;
    --output_root) OUTPUT_ROOT="$2"; shift 2 ;;
    --iterations) ITERATIONS="$2"; shift 2 ;;
    --scene_name) SCENE_NAME="$2"; shift 2 ;;
    --max_mesh_views) MAX_MESH_VIEWS="$2"; shift 2 ;;
    --execute) DRY_RUN=0; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$CONFIG_PATH" || -z "$SOURCE_PATH" || -z "$OUTPUT_ROOT" ]]; then
  echo "Usage: $0 --config <config.yaml> --source_path <scene> --output_root <root> [--model_root <root>] [--iterations N] [--scene_name name] [--execute]" >&2
  exit 2
fi

read_config_value() {
  local key="$1"
  grep -E "^${key}:" "$CONFIG_PATH" | head -n 1 | sed -E "s/^${key}:[[:space:]]*//; s/^\"//; s/\"$//"
}

VARIANT_NAME="$(read_config_value name)"
TRAIN_ARGS="$(read_config_value train_args)"
MESH_MODE="$(read_config_value mesh_mode)"
TEXTURE_MODE="$(read_config_value texture_mode)"
MODEL_PATH="${MODEL_ROOT:-$OUTPUT_ROOT/models}/${SCENE_NAME}/${VARIANT_NAME}"
RESULT_PATH="$OUTPUT_ROOT/results/${SCENE_NAME}/${VARIANT_NAME}"

mkdir -p "$RESULT_PATH"

TRAIN_CMD=(conda run -n ref_gs python train.py -s "$SOURCE_PATH" -m "$MODEL_PATH" --iterations "$ITERATIONS")
if [[ -n "$TRAIN_ARGS" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=($TRAIN_ARGS)
  TRAIN_CMD+=("${EXTRA_ARGS[@]}")
fi

MESH_CMD=(conda run -n ref_gs python extract_surface_mesh.py -s "$SOURCE_PATH" -m "$MODEL_PATH" --iteration "$ITERATIONS" --mesh_mode "$MESH_MODE" --output_path "$RESULT_PATH/mesh_${MESH_MODE}.ply")
if [[ "$MAX_MESH_VIEWS" != "0" ]]; then
  MESH_CMD+=(--max_views "$MAX_MESH_VIEWS")
fi
TEXTURE_CMD=(conda run -n ref_gs python export_pbr_textures.py -s "$SOURCE_PATH" -m "$MODEL_PATH" --iteration "$ITERATIONS" --mode "$TEXTURE_MODE" --output_dir "$RESULT_PATH/pbr_textures_${TEXTURE_MODE}")
EVAL_CMD=(conda run -n ref_gs python eval_reflective_assets.py --output_dir "$RESULT_PATH/eval")

printf '%q ' "${TRAIN_CMD[@]}" > "$RESULT_PATH/train_command.txt"; printf '\n' >> "$RESULT_PATH/train_command.txt"
printf '%q ' "${MESH_CMD[@]}" > "$RESULT_PATH/mesh_command.txt"; printf '\n' >> "$RESULT_PATH/mesh_command.txt"
printf '%q ' "${TEXTURE_CMD[@]}" > "$RESULT_PATH/texture_command.txt"; printf '\n' >> "$RESULT_PATH/texture_command.txt"
printf '%q ' "${EVAL_CMD[@]}" > "$RESULT_PATH/eval_command.txt"; printf '\n' >> "$RESULT_PATH/eval_command.txt"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN=1"
  echo "Commands written to $RESULT_PATH"
  exit 0
fi

"${TRAIN_CMD[@]}"
"${MESH_CMD[@]}"
"${TEXTURE_CMD[@]}"
"${EVAL_CMD[@]}"
