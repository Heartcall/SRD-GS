#!/usr/bin/env bash
set +e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

SCRIPT="train-NeRF.py"
SCENE="/data/liuly/dataset/3DGS/NeRF Synthetic/materials"
MODEL="output/ref_gs_limitation_timing/materials_iter10"
ITERATIONS="10"
DRY_RUN="0"
STRICT="0"
EXTRA_ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --script) SCRIPT="$2"; shift 2 ;;
    --scene) SCENE="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --iterations) ITERATIONS="$2"; shift 2 ;;
    --dry-run) DRY_RUN="1"; shift ;;
    --strict) STRICT="1"; shift ;;
    --extra) EXTRA_ARGS+=("$2"); shift 2 ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

OUT_DIR="${TIMING_OUT_DIR:-experiments/ref_gs_limitation_analysis/metrics/timing_probe}"
LOG_DIR="${TIMING_LOG_DIR:-experiments/ref_gs_limitation_analysis/sanity_logs}"
SUMMARY_BASENAME="${TIMING_SUMMARY_BASENAME:-timing_summary}"
mkdir -p "$OUT_DIR" "$LOG_DIR" "$(dirname "$MODEL")"
SUMMARY_JSON="$OUT_DIR/${SUMMARY_BASENAME}.json"
SUMMARY_MD="$OUT_DIR/${SUMMARY_BASENAME}.md"
LOG_PATH="$LOG_DIR/timing_probe_$(basename "$SCRIPT" .py)_iter${ITERATIONS}.log"

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

COMMAND=(python "$SCRIPT" -s "$SCENE" --eval --iterations "$ITERATIONS" --save_iterations "$ITERATIONS" --checkpoint_iterations "$ITERATIONS" --test_iterations "$ITERATIONS" --model_path "$MODEL")
if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
  COMMAND+=("${EXTRA_ARGS[@]}")
fi

START_TS="$(date +%s)"
EXIT_CODE=99
PEAK_GPU_MEMORY="NA"
GPU_MEMORY_REASON="dry_run"

if [ "$DRY_RUN" = "1" ]; then
  printf 'dry-run command: %q ' "${COMMAND[@]}" > "$LOG_PATH"
  printf '\n' >> "$LOG_PATH"
  EXIT_CODE=0
else
  "${COMMAND[@]}" > "$LOG_PATH" 2>&1 &
  TRAIN_PID=$!
  if nvidia-smi --query-gpu=index --format=csv,noheader >/dev/null 2>&1; then
    PEAK_GPU_MEMORY=0
    GPU_MEMORY_REASON=""
  else
    PEAK_GPU_MEMORY="NA"
    GPU_MEMORY_REASON="nvidia-smi unavailable"
  fi
  while kill -0 "$TRAIN_PID" 2>/dev/null; do
    if [ "$PEAK_GPU_MEMORY" != "NA" ]; then
      SAMPLE="$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits 2>/dev/null | awk -F, -v pid="$TRAIN_PID" '$1 ~ pid {gsub(/ /, "", $2); print $2}' | sort -nr | head -1)"
      if [ -n "$SAMPLE" ] && [ "$SAMPLE" -gt "$PEAK_GPU_MEMORY" ] 2>/dev/null; then
        PEAK_GPU_MEMORY="$SAMPLE"
      fi
    fi
    sleep 1
  done
  wait "$TRAIN_PID"
  EXIT_CODE=$?
fi

END_TS="$(date +%s)"
WALL_CLOCK=$((END_TS - START_TS))
CHECKPOINT="$MODEL/chkpnt${ITERATIONS}.pth"
if [ -f "$CHECKPOINT" ]; then
  CHECKPOINT_SIZE="$(stat -c%s "$CHECKPOINT" 2>/dev/null || echo NA)"
else
  CHECKPOINT_SIZE="NA"
fi

python - "$SUMMARY_JSON" "$SUMMARY_MD" "${SCRIPT}" "${SCENE}" "${MODEL}" "${ITERATIONS}" "${DRY_RUN}" "${ACTIVATE_STATUS}" "${WALL_CLOCK}" "${PEAK_GPU_MEMORY}" "${GPU_MEMORY_REASON}" "${CHECKPOINT}" "${CHECKPOINT_SIZE}" "${LOG_PATH}" "${EXIT_CODE}" "${COMMAND[@]}" <<'PY'
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
script, scene, model, iterations, dry_run, activate_status, wall_clock, peak_gpu, gpu_reason, checkpoint, checkpoint_size, log_path, exit_code = sys.argv[3:16]
command = sys.argv[16:]
payload = {
    "script": script,
    "scene": scene,
    "model": model,
    "iterations": int(iterations),
    "dry_run": dry_run == "1",
    "conda_activate_exit": int(activate_status),
    "command": command,
    "wall_clock_seconds": int(wall_clock),
    "peak_gpu_memory_mb": peak_gpu,
    "peak_gpu_memory_reason": gpu_reason,
    "checkpoint": checkpoint,
    "checkpoint_size_bytes": checkpoint_size,
    "log_path": log_path,
    "exit_code": int(exit_code),
}
summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
lines = [
    "# Timing Probe Summary",
    "",
    f"- script: `{script}`",
    f"- scene: `{scene}`",
    f"- model: `{model}`",
    f"- iterations: `{iterations}`",
    f"- dry_run: `{payload['dry_run']}`",
    f"- exit_code: `{exit_code}`",
    f"- wall_clock_seconds: `{wall_clock}`",
    f"- peak_gpu_memory_mb: `{peak_gpu}`",
    f"- peak_gpu_memory_reason: `{gpu_reason}`",
    f"- checkpoint_size_bytes: `{checkpoint_size}`",
    f"- log_path: `{log_path}`",
    "",
    "## Command",
    "",
    "```bash",
    " ".join(command),
    "```",
]
summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

if [ "$STRICT" = "1" ] && [ "$DRY_RUN" != "1" ] && [ "$EXIT_CODE" -ne 0 ]; then
  exit "$EXIT_CODE"
fi

exit 0
