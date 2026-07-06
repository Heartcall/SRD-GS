#!/usr/bin/env bash
set +e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${ENV_CHECK_LOG_DIR:-$ROOT_DIR/experiments/ref_gs_limitation_analysis/sanity_logs}"
LOG_FILE="${ENV_CHECK_LOG_FILE:-$LOG_DIR/env_check.txt}"
mkdir -p "$LOG_DIR"

{
  echo "# Ref-GS limitation env check"
  date
  echo
  echo "## conda activation"
} > "$LOG_FILE"

for candidate in \
  "$HOME/miniconda3/etc/profile.d/conda.sh" \
  "$HOME/anaconda3/etc/profile.d/conda.sh" \
  "/opt/conda/etc/profile.d/conda.sh"
do
  if [ -f "$candidate" ]; then
    # shellcheck source=/dev/null
    source "$candidate"
    echo "sourced $candidate" >> "$LOG_FILE"
    break
  fi
done

conda activate ref_gs >> "$LOG_FILE" 2>&1
echo "conda_activate_exit=$?" >> "$LOG_FILE"

run_logged() {
  echo >> "$LOG_FILE"
  echo "## $*" >> "$LOG_FILE"
  "$@" >> "$LOG_FILE" 2>&1
  echo "exit=$?" >> "$LOG_FILE"
}

cd "$ROOT_DIR" || {
  echo "failed to cd $ROOT_DIR" >> "$LOG_FILE"
  exit 0
}

run_logged pwd
run_logged git status --short
run_logged git rev-parse HEAD
run_logged conda info --envs
run_logged which python
run_logged python --version
run_logged nvidia-smi

{
  echo
  echo "## pip list | head -80"
  pip list 2>&1 | head -80
  echo "pipeline_exit=${PIPESTATUS[*]}"
} >> "$LOG_FILE"

echo "Wrote $LOG_FILE"
