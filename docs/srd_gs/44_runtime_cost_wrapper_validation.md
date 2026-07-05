# Milestone 44: Runtime-cost wrapper validation

Status: dry-run runtime-cost wrapper validation GO; runtime-cost values still unavailable; paper-scale still blocked

## Objective

Implement one bounded follow-up after M43: validate that the M43 runtime-cost manifest can be converted into a future wrapper plan for `training_time`, `peak_memory`, and `render_fps`.

This milestone reads the M43 contract and manifest template, checks command/log path readiness, and writes a dry-run wrapper plan. It does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M44 validates dry-run wrapper readiness from the M43 runtime-cost manifest.
- Allowed claim: all three runtime-cost entries have existing source command artifacts and can be planned for future bounded collection.
- Allowed claim: no runtime-cost logs or metric values were generated in M44.
- Disallowed claim: runtime efficiency is measured.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/validate_runtime_cost_wrapper_m44.py`.
- Added `tests/test_runtime_cost_wrapper_validation.py`.
- The script consumes:
  - M43 `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_logging_contract.json`
  - M43 `outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_manifest_template.json`
- The script writes:
  - `runtime_cost_wrapper_plan.csv`
  - `runtime_cost_wrapper_plan.json`
  - `runtime_cost_wrapper_plan.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/validate_runtime_cost_wrapper_m44.py \
  --contract_json outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_logging_contract.json \
  --manifest_template outputs/srd_gs_runtime_cost_logging_m43/runtime_cost_manifest_template.json \
  --output_dir outputs/srd_gs_runtime_cost_wrapper_m44
```

## Outputs

- `outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.csv`
- `outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.json`
- `outputs/srd_gs_runtime_cost_wrapper_m44/runtime_cost_wrapper_plan.md`

## Key Results

| Metric | Status | Source command | Required log available |
| --- | --- | --- | --- |
| `runtime/training_time` | `wrapper_plan_ready` | true | false |
| `runtime/peak_memory` | `wrapper_plan_ready` | true | false |
| `runtime/render_fps` | `wrapper_plan_ready` | true | false |

Summary:

- Manifest entries: 3
- Wrapper plans ready: 3
- Blocked wrappers: 0
- Logs currently available: 0
- Metrics computed: false
- Runtime launched: false

## Interpretation

M44 confirms that the M43 manifest is sufficient to produce a dry-run wrapper plan for a future bounded runtime-cost collection pass. The existing train and render-eval-pairs command artifacts are present, but no runtime-cost logs are available yet.

The runtime metrics remain unavailable and must not be treated as runtime efficiency evidence.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If wrapper readiness is treated as runtime-cost measurement, it fails.
- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.
- If missing accepted GT depth/material artifacts, F-score zero, or high LPIPS/Refl-LPIPS are ignored, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_wrapper_validation` failed before `validate_runtime_cost_wrapper_m44.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_runtime_cost_wrapper_validation` passed, 1 test.
- M44 wrapper-validation command passed and wrote three output artifacts under `outputs/srd_gs_runtime_cost_wrapper_m44`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 45 should remain bounded. A reasonable next step is either a runtime-cost parser for existing logs if logs appear, or exactly one short preflight-gated runtime-cost collection before parsing values. Do not launch broad paper-scale experiments.
