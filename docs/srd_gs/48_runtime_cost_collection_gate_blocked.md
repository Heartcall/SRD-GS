# Milestone 48: Runtime-cost collection gate-blocked attempt

Status: bounded runtime-cost collection attempt blocked by immediate prelaunch gate; runtime collection not launched; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded follow-up after M47: rerun the launch gate immediately before collection, and launch exactly one short runtime-cost collection only if that gate is still GO.

This milestone did not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments because the immediate prelaunch gate returned NO-GO.

## Claim Boundary

- Allowed claim: M48 adds a bounded runtime-cost collector/parser that can consume the fresh M46 package after a M47-style GO gate.
- Allowed claim: the actual M48 prelaunch gate was NO-GO due to `training_gpu_busy`, so collection was correctly blocked.
- Allowed claim: no runtime-cost metric values were generated in this run.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/collect_runtime_cost_m48.py`.
- Added `tests/test_runtime_cost_collection_m48.py`.
- The collector consumes:
  - M46 fresh wrapper plan `outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv`
  - immediate prelaunch gate JSON `outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate/runtime_cost_launch_gate.json`
  - M46 fresh result root `outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300`
- The collector writes:
  - `runtime_cost_metrics.csv`
  - `runtime_cost_summary.csv`
  - `runtime_cost_metrics.json`
  - `runtime_cost_metrics.md`

If the launch gate is GO, the collector runs one train command and one render command from the M46 command artifacts and writes `runtime_cost/train_timing.json`, `runtime_cost/gpu_memory_trace.csv`, and `runtime_cost/render_timing.json`. In the actual M48 run, the gate was NO-GO, so those runtime logs were intentionally not created.

## Commands

Immediate prelaunch gate:

```bash
conda run -n ref_gs python scripts/srd_gs/preflight_runtime_cost_launch_m47.py \
  --fresh_plan_csv outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv \
  --collection_preflight_json outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.json \
  --result_root outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M48_prelaunch_runtime_cost_gate \
  --output_dir outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate \
  --training_gpu_index 2 \
  --max_gpu_utilization_percent 50 \
  --workspace_path . \
  --min_workspace_free_gb 25
```

No-launch summary:

```bash
conda run -n ref_gs python scripts/srd_gs/collect_runtime_cost_m48.py \
  --fresh_plan_csv outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv \
  --launch_gate_json outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate/runtime_cost_launch_gate.json \
  --result_root outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M48_runtime_cost_collection_blocked_by_prelaunch_gate \
  --output_dir outputs/srd_gs_runtime_cost_collection_m48 \
  --training_gpu_index 2
```

## Outputs

- `outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate/runtime_cost_launch_gate.csv`
- `outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate/runtime_cost_launch_gate.json`
- `outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate/runtime_cost_launch_gate.md`
- `outputs/srd_gs_runtime_cost_collection_m48/runtime_cost_metrics.csv`
- `outputs/srd_gs_runtime_cost_collection_m48/runtime_cost_summary.csv`
- `outputs/srd_gs_runtime_cost_collection_m48/runtime_cost_metrics.json`
- `outputs/srd_gs_runtime_cost_collection_m48/runtime_cost_metrics.md`

## Key Results

| Gate / Metric | Value |
| --- | ---: |
| Prelaunch runtime GO | false |
| Prelaunch blocker | `training_gpu_busy` |
| Training GPU index | 2 |
| Training GPU memory used MB | 21575 |
| Training GPU utilization percent | 98 |
| Workspace free GB | 59.14317321777344 |
| Process match count | 0 |
| Runtime launched | false |
| Training launched | false |
| Rendering launched | false |
| Metrics computed | false |
| Paper-scale gate | NO-GO |

Metric table:

| Metric | Status | Value | Unit | Failure condition |
| --- | --- | ---: | --- | --- |
| `runtime/training_time` | failed |  | seconds | `train_command_failed_or_not_run` |
| `runtime/peak_memory` | not_available |  | MB | `gpu_memory_trace_missing_training_gpu` |
| `runtime/render_fps` | failed |  | frames_per_second | `render_command_failed_or_manifest_missing` |

## Interpretation

M48 added the bounded collector/parser needed for runtime-cost measurement, but the actual collection was correctly blocked because GPU 2 was above the utilization threshold at the immediate prelaunch gate.

This is a blocked engineering milestone, not runtime-cost evidence. It preserves the M47/M48 safety contract: do not launch train/render when the launch gate is NO-GO.

## Failure Conditions

- If this milestone launches train/render while `runtime_go=false`, it fails.
- If this milestone launches mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If blocked/no-launch rows are treated as runtime-cost values, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_m48` failed before `collect_runtime_cost_m48.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_m48` passed, 1 test.
- M48 prelaunch gate command passed and wrote three gate artifacts under `outputs/srd_gs_runtime_cost_collection_m48/prelaunch_gate`, with `runtime_go=false`.
- M48 no-launch collector command passed and wrote four summary artifacts under `outputs/srd_gs_runtime_cost_collection_m48`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 49 should remain bounded. Rerun the M47/M48 prelaunch gate when training GPU utilization is below threshold, then launch the same single short runtime-cost collection only if `runtime_go=true`. Do not launch broad paper-scale experiments.
