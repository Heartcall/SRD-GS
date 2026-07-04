# Milestone 43: Runtime-cost logging contract

Status: read-only runtime-cost contract GO; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded remaining contract after M42: define runtime-cost logging paths and readiness for `training_time`, `peak_memory`, and `render_fps`. This milestone reads existing M32 command artifacts and source metrics, then writes a contract for future bounded runtime-cost collection.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: runtime-cost logging contract paths can be defined for a future bounded run.
- Allowed claim: existing M32 command files are sufficient to instrument a future runtime-cost collection pass.
- Allowed claim: runtime-cost metric values remain unavailable in M43.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/define_runtime_cost_logging_m43.py`.
- Added `tests/test_runtime_cost_logging_contract.py`.
- The script consumes:
  - M32 result root `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300`
  - M32 `eval_with_gt_mesh/metrics.csv`
- The script writes:
  - `runtime_cost_logging_contract.csv`
  - `runtime_cost_logging_contract.json`
  - `runtime_cost_logging_contract.md`
  - `runtime_cost_manifest_template.json`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/define_runtime_cost_logging_m43.py \
  --result_root outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --output_dir outputs/srd_gs_runtime_cost_logging_m43
```

## Outputs

- `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_logging_contract.csv`
- `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_logging_contract.json`
- `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_logging_contract.md`
- `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_manifest_template.json`

## Key Results

| Metric | Status | Source command | Required log |
| --- | --- | --- | --- |
| `runtime/training_time` | `contract_defined_needs_future_runtime` | true | `runtime_cost/train_timing.json` |
| `runtime/peak_memory` | `contract_defined_needs_future_runtime` | true | `runtime_cost/gpu_memory_trace.csv` |
| `runtime/render_fps` | `contract_defined_needs_future_runtime` | true | `runtime_cost/render_timing.json` |

Summary:

- Contract count: 3
- Instrumentable contracts: 3
- Logs currently available: 0
- Metrics computed: false

## Interpretation

M43 reduces the runtime-cost blocker from an unspecified missing-metric state into explicit future log paths and source command requirements. Existing M32 command files are sufficient to instrument a future bounded runtime-cost collection pass, but no runtime-cost logs have been collected yet.

The runtime metrics remain unavailable and must not be treated as runtime efficiency evidence.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If contract definition is treated as runtime-cost measurement, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_runtime_cost_logging_contract` failed before `define_runtime_cost_logging_m43.py` existed.
- Focused TDD GREEN: `python -m unittest tests.test_runtime_cost_logging_contract` passed, 1 test.
- M43 contract command passed and wrote four output artifacts under `outputs/srd_gs_runtime_cost_logging_m43`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 44 should remain bounded. A reasonable next step is dry-run wrapper validation for runtime-cost logging, or one short bounded runtime-cost collection only after preflight gates pass. Do not launch broad paper-scale experiments.
