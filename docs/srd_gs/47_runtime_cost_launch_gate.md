# Milestone 47: Runtime-cost launch gate

Status: bounded runtime-cost launch gate GO; runtime collection still not launched; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded follow-up after M46: run CUDA, GPU-utilization, workspace-storage, process, and overwrite-safety gates for the fresh M46 runtime-cost package.

This milestone checks whether the fresh package is safe to launch. It does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M47 checks launch readiness for the fresh M46 runtime-cost package.
- Allowed claim: the fresh package passes CUDA/storage/process/overwrite gates in the current environment.
- Allowed claim: no runtime-cost logs or metric values were generated in M47.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/preflight_runtime_cost_launch_m47.py`.
- Added `tests/test_runtime_cost_launch_gate_m47.py`.
- The script consumes:
  - M46 fresh wrapper plan `outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv`
  - M46 nested collection preflight `outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.json`
  - M46 result root `outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300`
- The script writes:
  - `runtime_cost_launch_gate.csv`
  - `runtime_cost_launch_gate.json`
  - `runtime_cost_launch_gate.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/preflight_runtime_cost_launch_m47.py \
  --fresh_plan_csv outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv \
  --collection_preflight_json outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.json \
  --result_root outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M47_runtime_cost_launch_gate \
  --output_dir outputs/srd_gs_runtime_cost_launch_gate_m47 \
  --training_gpu_index 2 \
  --max_gpu_utilization_percent 50 \
  --workspace_path . \
  --min_workspace_free_gb 25
```

## Outputs

- `outputs/srd_gs_runtime_cost_launch_gate_m47/runtime_cost_launch_gate.csv`
- `outputs/srd_gs_runtime_cost_launch_gate_m47/runtime_cost_launch_gate.json`
- `outputs/srd_gs_runtime_cost_launch_gate_m47/runtime_cost_launch_gate.md`

## Key Results

| Gate | Value |
| --- | ---: |
| Runtime GO | true |
| Fresh wrapper entries | 3 |
| Runtime-cost logs | 0 |
| Collection preflight safe | true |
| Overwrite blockers | 0 |
| Torch CUDA available | true |
| Torch device count | 8 |
| Torch training GPU visible | true |
| Training GPU index | 2 |
| Training GPU memory used MB | 22559 |
| Training GPU utilization percent | 0 |
| Workspace free GB | 59.49984359741211 |
| Process match count | 0 |
| Blocker count | 0 |

Summary:

- Runtime GO: true
- Metrics computed: false
- Runtime launched: false
- Paper-scale gate: NO-GO

## Interpretation

M47 confirms that the fresh M46 package is currently launch-ready by the bounded runtime gate: it passes overwrite-safety, CUDA visibility, training GPU utilization, workspace storage, and prohibited-process checks.

This is not runtime-cost measurement. No runtime logs exist yet, and no runtime efficiency claim is supported. The next bounded milestone may launch exactly one short runtime-cost collection and parse only the resulting runtime logs.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If runtime GO is treated as runtime-cost measurement, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_launch_gate_m47` failed before `preflight_runtime_cost_launch_m47.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_launch_gate_m47` passed, 1 test.
- M47 launch-gate command passed and wrote three output artifacts under `outputs/srd_gs_runtime_cost_launch_gate_m47`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 48 should remain bounded. If the fresh M46 package still passes this gate immediately before launch, launch exactly one short runtime-cost collection and parse only the resulting runtime logs. Do not launch broad paper-scale experiments.
