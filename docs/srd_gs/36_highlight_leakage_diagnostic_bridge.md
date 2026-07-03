# Milestone 36: Highlight-leakage export diagnostic bridge

Status: read-only export-diagnostic bridge GO; GT material accuracy still blocked; paper-scale still blocked

## Objective

Implement the M35-recommended bounded bridge for `texture_material/highlight_leakage_score`. This milestone reads existing M32 eval/material and texture-export artifacts, surfaces texture-export highlight leakage as a separate eval/material export diagnostic, and preserves the original unavailable GT-style material metric row.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: existing texture-export highlight-leakage artifacts can be surfaced in an eval/material summary as `texture_material_export_diagnostic/highlight_leakage_score`.
- Allowed claim: the source eval row `texture_material/highlight_leakage_score` remains unavailable and visible with its original reason.
- Allowed claim: M36 reduces one reporting/plumbing blocker by adding a separate export diagnostic row.
- Disallowed claim: GT PBR material accuracy is validated.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.
- Disallowed claim: unavailable GT/dependency/runtime metrics are solved.

## Implementation

- Added `scripts/srd_gs/bridge_highlight_leakage_diagnostic_m36.py`.
- Added `tests/test_highlight_leakage_diagnostic_bridge.py`.
- The script consumes:
  - M32 `eval_with_gt_mesh/metrics.csv`
  - M32 `eval_with_gt_mesh/metrics.json`
  - M32 `eval_with_gt_mesh/failure_case_panels/failure_summary.md`
  - M35 `eval_material_artifact_plan.json`
  - M32 `pbr_textures_specular_free/baking_report.json`
  - M32 `pbr_textures_specular_free/highlight_leakage_mask.png`
- The script writes:
  - `highlight_leakage_diagnostic_summary.csv`
  - `highlight_leakage_diagnostic_summary.json`
  - `highlight_leakage_diagnostic_summary.md`
  - `eval_material_augmented_metrics.csv`
  - `eval_material_augmented_metrics.json`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/bridge_highlight_leakage_diagnostic_m36.py \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --metrics_json outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json \
  --failure_summary outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md \
  --m35_plan outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_plan.json \
  --texture_dir outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/pbr_textures_specular_free \
  --output_dir outputs/srd_gs_highlight_leakage_bridge_m36
```

## Outputs

- `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.csv`
- `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.json`
- `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.md`
- `outputs/srd_gs_highlight_leakage_bridge_m36/eval_material_augmented_metrics.csv`
- `outputs/srd_gs_highlight_leakage_bridge_m36/eval_material_augmented_metrics.json`

## Key Metrics

| Metric | Value |
| --- | ---: |
| Source unavailable metric count | 10 |
| Bridged export diagnostics | 1 |
| Remaining metric blockers | 9 |
| `texture_material_export_diagnostic/highlight_leakage_score` | 0.000975149334408 |

## Interpretation

M36 completes the one immediate plumbing action identified by M35. The highlight-leakage score is now visible in a separate export-diagnostic namespace and the original eval/material unavailable row is not overwritten. This makes the artifact chain easier to summarize without weakening the material-accuracy boundary.

The remaining metric blockers are still real: LPIPS/refl-LPIPS need dependency gating or installation, depth/albedo/roughness need accepted GT artifacts, material consistency needs a material-view manifest, and runtime metrics need timing/memory/FPS logs.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, or evaluation, it fails.
- If `texture_material_export_diagnostic/highlight_leakage_score` is treated as GT PBR material accuracy, it fails.
- If the original unavailable `texture_material/highlight_leakage_score` row is overwritten or hidden, it fails.
- If missing GT/dependency/runtime-log metrics are marked solved, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_highlight_leakage_diagnostic_bridge` failed before `bridge_highlight_leakage_diagnostic_m36.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_highlight_leakage_diagnostic_bridge` passed, 1 test.
- M36 bridge command passed and wrote five output artifacts under `outputs/srd_gs_highlight_leakage_bridge_m36`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 37 should remain bounded and choose one next unavailable-metric contract: LPIPS dependency gating, accepted GT material/depth artifact protocol, material-view manifest definition, or runtime-cost logging. Do not launch broad paper-scale experiments.
