#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <pred_rgb.png> <gt_rgb.png> <output_dir> [reflective_mask.png]" >&2
  exit 2
fi

PRED_RGB="$1"
GT_RGB="$2"
OUTPUT_DIR="$3"
REFLECTIVE_MASK="${4:-}"

CMD=(conda run -n ref_gs python eval_reflective_assets.py
  --pred_rgb "$PRED_RGB"
  --gt_rgb "$GT_RGB"
  --output_dir "$OUTPUT_DIR")

if [[ -n "$REFLECTIVE_MASK" ]]; then
  CMD+=(--reflective_mask "$REFLECTIVE_MASK")
else
  CMD+=(--auto_reflective_mask)
fi

"${CMD[@]}"
