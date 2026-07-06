# Milestone 46: Fresh-root runtime-cost collection package

Status: bounded fresh-root runtime-cost package GO; collection launch still deferred to runtime gates; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded follow-up after M45: clone the approved runtime-cost train/render command artifacts into a fresh M46 output root, then rerun the existing M45 collection preflight against immutable M32 outputs.

This milestone removes the existing-output target blocker identified in M45. It does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M46 clones runtime-cost command/log targets into a fresh output root.
- Allowed claim: the cloned M46 package passes the existing-output preflight with zero overwrite blockers.
- Allowed claim: no runtime-cost logs or metric values were generated in M46.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/prepare_runtime_cost_collection_m46.py`.
- Added `tests/test_runtime_cost_collection_package_m46.py`.
- The script consumes:
  - M44 `outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.csv`
  - source M32 result/model roots
  - target M46 result/model roots
  - immutable root `outputs/srd_gs_instrumented_runtime_m32_i30`
- The script writes:
  - a fresh wrapper plan under `outputs/srd_gs_runtime_cost_collection_m46/package`
  - cloned train/render command files under `outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300`
  - a nested M45 preflight report under `outputs/srd_gs_runtime_cost_collection_m46/package/preflight`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/prepare_runtime_cost_collection_m46.py \
  --wrapper_plan_csv outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.csv \
  --source_result_root outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --source_model_root outputs/srd_gs_instrumented_runtime_m32_i30/models/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --target_result_root outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --target_model_root outputs/srd_gs_runtime_cost_collection_m46/models/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --immutable_root outputs/srd_gs_instrumented_runtime_m32_i30 \
  --output_dir outputs/srd_gs_runtime_cost_collection_m46/package
```

## Outputs

- `outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.csv`
- `outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.json`
- `outputs/srd_gs_runtime_cost_collection_m46/package/fresh_runtime_cost_wrapper_plan.md`
- `outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.csv`
- `outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.json`
- `outputs/srd_gs_runtime_cost_collection_m46/package/preflight/runtime_cost_collection_preflight.md`
- `outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/train_command.txt`
- `outputs/srd_gs_runtime_cost_collection_m46/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs_command.txt`

## Key Results

| Metric | Status | Safe to launch by overwrite preflight | Required log available |
| --- | --- | --- | --- |
| `runtime/training_time` | `fresh_root_plan_ready` | true | false |
| `runtime/peak_memory` | `fresh_root_plan_ready` | true | false |
| `runtime/render_fps` | `fresh_root_plan_ready` | true | false |

Summary:

- Fresh wrapper entries: 3
- Cloned command files: 2
- Existing-output overwrite blockers: 0
- Preflight safe collection entries: 3
- Existing runtime-cost logs: 0
- Metrics computed: false
- Runtime launched: false

## Interpretation

M46 removes the M45 overwrite blocker by rewriting the train/render command and runtime-cost log targets from the M32 output root into a fresh M46 output root. The existing M45 preflight now reports that the fresh package does not point into immutable M32 artifacts.

This is not runtime-cost measurement. No runtime logs exist yet, and runtime launch remains deferred until CUDA, storage, and prohibited-process gates are checked immediately before collection.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If cloned commands still target M32 outputs, it fails.
- If fresh-root package readiness is treated as runtime-cost measurement, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_package_m46` failed before `prepare_runtime_cost_collection_m46.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_package_m46` passed, 1 test.
- M46 package command passed and wrote the fresh wrapper plan, cloned command files, and nested preflight artifacts under `outputs/srd_gs_runtime_cost_collection_m46`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 47 should remain bounded. Run CUDA/storage/process preflight for the fresh M46 package, then launch at most one short runtime-cost collection only if every gate passes. Do not launch broad paper-scale experiments.
