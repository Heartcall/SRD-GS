# Milestone 45: Runtime-cost collection preflight

Status: bounded runtime-cost collection preflight GO; collection launch blocked by existing-output targets; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded follow-up after M44: preflight whether the runtime-cost wrapper plan can be safely launched for `training_time`, `peak_memory`, and `render_fps`.

This milestone reads the M44 wrapper plan, treats the M32 instrumented runtime output root as immutable, and classifies whether collection commands/logs would write into existing artifacts. It does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M45 preflights runtime-cost collection safety from the M44 wrapper plan.
- Allowed claim: the current M44 plan would target existing M32 output artifacts and is therefore not safe to launch as-is.
- Allowed claim: no runtime-cost logs or metric values were generated in M45.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/preflight_runtime_cost_collection_m45.py`.
- Added `tests/test_runtime_cost_collection_preflight.py`.
- The script consumes:
  - M44 `outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.csv`
  - immutable root `outputs/srd_gs_instrumented_runtime_m32_i30`
- The script writes:
  - `runtime_cost_collection_preflight.csv`
  - `runtime_cost_collection_preflight.json`
  - `runtime_cost_collection_preflight.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/preflight_runtime_cost_collection_m45.py \
  --wrapper_plan_csv outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.csv \
  --immutable_root outputs/srd_gs_instrumented_runtime_m32_i30 \
  --output_dir outputs/srd_gs_runtime_cost_collection_preflight_m45
```

## Outputs

- `outputs/srd_gs_runtime_cost_collection_preflight_m45/runtime_cost_collection_preflight.csv`
- `outputs/srd_gs_runtime_cost_collection_preflight_m45/runtime_cost_collection_preflight.json`
- `outputs/srd_gs_runtime_cost_collection_preflight_m45/runtime_cost_collection_preflight.md`

## Key Results

| Metric | Status | Safe to launch | Required log available |
| --- | --- | --- | --- |
| `runtime/training_time` | `blocked_existing_output_target` | false | false |
| `runtime/peak_memory` | `blocked_existing_output_target` | false | false |
| `runtime/render_fps` | `blocked_existing_output_target` | false | false |

Summary:

- Manifest entries: 3
- Safe collection entries: 0
- Existing-output overwrite blockers: 3
- Existing runtime-cost logs: 0
- Metrics computed: false
- Runtime launched: false

## Interpretation

M45 confirms that the M44 runtime-cost wrapper plan is not safe to execute as-is because the planned train/render command artifacts and required runtime-cost log paths point into the existing M32 output root. Launching collection directly from those commands would risk overwriting or mixing with frozen diagnostic artifacts.

Runtime-cost metric values remain unavailable. The next bounded step must clone the approved train/render runtime-cost commands into a fresh output root before any runtime collection is attempted.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If existing M32 output targets are ignored or overwritten, it fails.
- If collection preflight is treated as runtime-cost measurement, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_preflight` failed before `preflight_runtime_cost_collection_m45.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_collection_preflight` passed, 1 test.
- M45 preflight command passed and wrote three output artifacts under `outputs/srd_gs_runtime_cost_collection_preflight_m45`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 46 should remain bounded. Clone the approved train/render runtime-cost commands into a fresh M46 output root, rerun this preflight, and only launch one short collection if all blockers clear. Do not launch broad paper-scale experiments.
