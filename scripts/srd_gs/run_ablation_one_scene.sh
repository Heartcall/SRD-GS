#!/usr/bin/env bash
set -euo pipefail

CONFIG_GLOB="configs/srd_gs/*.yaml"
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config_glob) CONFIG_GLOB="$2"; shift 2 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

for CONFIG in $CONFIG_GLOB; do
  scripts/srd_gs/run_one_scene.sh --config "$CONFIG" "${ARGS[@]}"
done
