#!/usr/bin/env bash
set -euo pipefail

SCENE_PATH="/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball"
MODEL_PATH=""
OUTPUT_ROOT="outputs/srd_gs_metric_chain"
VARIANT="variant"
ITERATION=20
SPLIT="test"
MAX_VIEWS=2
ENABLE_SRD=0
EXECUTE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene_path) SCENE_PATH="$2"; shift 2 ;;
    --model_path) MODEL_PATH="$2"; shift 2 ;;
    --output_root) OUTPUT_ROOT="$2"; shift 2 ;;
    --variant) VARIANT="$2"; shift 2 ;;
    --iteration) ITERATION="$2"; shift 2 ;;
    --split) SPLIT="$2"; shift 2 ;;
    --max_views) MAX_VIEWS="$2"; shift 2 ;;
    --enable_srd_gs) ENABLE_SRD=1; shift ;;
    --execute) EXECUTE=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$MODEL_PATH" ]]; then
  echo "--model_path is required" >&2
  exit 2
fi

PAIR_DIR="$OUTPUT_ROOT/ball/$VARIANT/render_eval_pairs"
EVAL_DIR="$OUTPUT_ROOT/ball/$VARIANT/eval"
mkdir -p "$PAIR_DIR" "$EVAL_DIR"

SRD_ARGS=()
if [[ "$ENABLE_SRD" -eq 1 ]]; then
  SRD_ARGS+=(--enable_srd_gs)
fi

RENDER_CMD=(
  conda run -n ref_gs python render_eval_pairs.py
  -s "$SCENE_PATH"
  -m "$MODEL_PATH"
  --iteration "$ITERATION"
  --split "$SPLIT"
  --max_views "$MAX_VIEWS"
  --output_dir "$PAIR_DIR"
  --auto_reflective_mask
  "${SRD_ARGS[@]}"
)

EVAL_CMD=(
  conda run -n ref_gs python eval_reflective_assets.py
  --eval_pairs_dir "$PAIR_DIR"
  --output_dir "$EVAL_DIR"
  --auto_reflective_mask
)

printf '%q ' "${RENDER_CMD[@]}" > "$OUTPUT_ROOT/ball/$VARIANT/render_eval_pairs_command.txt"
printf '\n' >> "$OUTPUT_ROOT/ball/$VARIANT/render_eval_pairs_command.txt"
printf '%q ' "${EVAL_CMD[@]}" > "$OUTPUT_ROOT/ball/$VARIANT/eval_pairs_command.txt"
printf '\n' >> "$OUTPUT_ROOT/ball/$VARIANT/eval_pairs_command.txt"

if [[ "$EXECUTE" -eq 1 ]]; then
  "${RENDER_CMD[@]}"
  "${EVAL_CMD[@]}"
else
  echo "Dry-run only. Add --execute to render/evaluate."
fi
