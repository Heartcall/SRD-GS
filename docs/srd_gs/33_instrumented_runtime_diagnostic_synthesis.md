# Milestone 33: Instrumented runtime diagnostic synthesis

Status: read-only synthesis GO; M32 diagnostic position clarified; paper-scale still blocked

## Objective

Compare M32's loss progression, failure-summary unavailable metrics, render-eval manifest, and metrics against prior short-budget controls before deciding whether another bounded single-scene control is justified. This milestone does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: M32's runtime artifacts can be read and summarized alongside prior short-budget controls.
- Allowed claim: M32 ranks best in PSNR/Refl-PSNR within this diagnostic table, while ranking worst in Chamfer/Normal MAE and keeping F-score at `0.0`.
- Allowed claim: M32 loss logging is present but short and non-monotonic over three logged rows.
- Allowed claim: M32 still has ten unavailable metrics in the failure summary.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond this one scene, one short checkpoint, and diagnostic comparison.

## Implementation

- Added `scripts/srd_gs/synthesize_instrumented_runtime_m33.py`.
- Added `tests/test_instrumented_runtime_synthesis.py`.
- The script consumes:
  - prior short-budget `case_summary.csv`
  - M32 `metrics.csv`
  - M32 `loss_log.csv`
  - M32 `render_eval_manifest.json`
  - M32 `failure_summary.md`
- The script writes:
  - `m32_metric_comparison.csv`
  - `m32_loss_progression_summary.csv`
  - `m32_unavailable_metrics.csv`
  - `m32_manifest_summary.csv`
  - `m33_synthesis_summary.json`
  - `m33_synthesis_report.md`

## Command

```bash
python scripts/srd_gs/synthesize_instrumented_runtime_m33.py \
  --prior_case_summary outputs/srd_gs_opacity_quarter_m26_i300/render_regression/case_summary.csv \
  --m32_metrics outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --m32_loss_log outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/loss_log.csv \
  --m32_manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --m32_failure_summary outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md \
  --output_dir outputs/srd_gs_m32_diagnostic_synthesis_m33
```

## Outputs

- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_metric_comparison.csv`
- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_loss_progression_summary.csv`
- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_unavailable_metrics.csv`
- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_manifest_summary.csv`
- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json`
- `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_report.md`

## Metric Position

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M20 render gate on | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 |
| M21 render gate neutral | 2.9205 | 1.5409 | 0.300529 | 0.001 | 75.9167 | 0.003792 |
| M24 reflection/specular freeze | 2.8750 | 1.7308 | 0.286904 | 0.000 | 74.6085 | 0.00000037 |
| M25 opacity freeze | 3.6522 | 2.3203 | 0.397042 | 0.000 | 73.8319 | 0.000229 |
| M26 quarter opacity LR | 3.1155 | 1.9098 | 0.327672 | 0.000 | 68.5402 | 0.00000763 |
| M32 instrumented i30 | 4.3425 | 2.9389 | 0.487437 | 0.000 | 87.3323 | n/a |

## Loss / Manifest / Availability

- Loss rows: `3`
- Logged iterations: `10`, `20`, `30`
- Final stage: `stage_a`
- Final total loss: `0.564937`
- Final minus first total loss: `-0.006957`
- Total loss monotonic non-increasing: `False`
- Render-eval frames: `2`
- Branch-map policy: `raster_feature_chunks`
- Branch gate weight: `1.0`
- Render gate weight: `0.0`
- Available render fields: `8`
- Unavailable metric count: `10`

## Interpretation

M32 is diagnostically useful because it finally provides runtime loss and failure-summary artifacts. It does not resolve quality blockers. The improved PSNR/Refl-PSNR is paired with worse Chamfer/Normal MAE, F-score remains zero, total loss is not monotonic over the three logged rows, and ten metrics are still unavailable.

The next bounded decision should choose one diagnostic direction rather than launching broad experiments.

## Failure Conditions

- If the script launches training, rendering, mesh extraction, texture export, or evaluation, the milestone fails. It only reads existing artifacts.
- If M32's PSNR/Refl-PSNR rank is promoted to SRD-GS superiority, the milestone fails.
- If worse Chamfer/Normal MAE, F-score `0.0`, or unavailable metrics are ignored, the milestone fails.
- If multi-scene or paper-scale conclusions are drawn from this synthesis, the milestone fails. Paper-scale remains NO-GO.

## Verification

- Focused TDD RED: `python -m unittest tests.test_instrumented_runtime_synthesis` failed before the script existed.
- Focused TDD GREEN: `python -m unittest tests.test_instrumented_runtime_synthesis` passed, 1 test.
- M33 synthesis command passed and wrote six output artifacts under `outputs/srd_gs_m32_diagnostic_synthesis_m33`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 34 should remain bounded and choose one diagnostic direction: Stage B/C activation, opacity schedule, or eval/material artifact plumbing. Do not launch broad paper-scale experiments.
