# Milestone 41: Material-consistency diagnostic

Status: bounded material-consistency diagnostic GO; GT material accuracy still blocked; paper-scale still blocked

## Objective

Implement the M40-recommended bounded material-consistency diagnostic computation from the M40 material-view manifest. This milestone reads existing M32/M40 artifacts, computes an image-space cross-view diagnostic, and writes separate augmented outputs without overwriting source M32 metrics.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: a bounded image-space material-consistency diagnostic can be computed from existing M40 material views.
- Allowed claim: M41 writes the diagnostic separately and preserves source M32 metrics.
- Allowed claim: the diagnostic is scoped to the existing two-frame M32 `ball` artifact set.
- Disallowed claim: GT PBR material accuracy is validated.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.
- Disallowed claim: accepted GT depth/material or runtime-cost blockers are solved.

## Implementation

- Added `scripts/srd_gs/compute_material_consistency_m41.py`.
- Added `tests/test_material_consistency_diagnostic.py`.
- The script consumes:
  - M40 `outputs/srd_gs_material_view_manifest_m40/material_view_manifest.json`
  - M32 `eval_with_gt_mesh/metrics.csv`
- The script writes:
  - `material_consistency_pairwise.csv`
  - `material_consistency_diagnostic.csv`
  - `material_consistency_summary.json`
  - `eval_material_augmented_metrics.csv`
  - `material_consistency_report.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/compute_material_consistency_m41.py \
  --material_view_manifest outputs/srd_gs_material_view_manifest_m40/material_view_manifest.json \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --output_dir outputs/srd_gs_material_consistency_m41
```

## Outputs

- `outputs/srd_gs_material_consistency_m41/material_consistency_pairwise.csv`
- `outputs/srd_gs_material_consistency_m41/material_consistency_diagnostic.csv`
- `outputs/srd_gs_material_consistency_m41/material_consistency_summary.json`
- `outputs/srd_gs_material_consistency_m41/eval_material_augmented_metrics.csv`
- `outputs/srd_gs_material_consistency_m41/material_consistency_report.md`

## Key Metrics

| Metric | Value |
| --- | ---: |
| Material views | 2 |
| Pair count | 1 |
| `texture_material_diagnostic/material_consistency_mae` | 0.0427745468915 |
| `texture_material_diagnostic/diffuse_rgb_mae` | 0.0433174259961 |
| `texture_material_diagnostic/roughness_map_mae` | 0.0422316677868 |
| Source metrics overwritten | false |

## Interpretation

M41 computes a bounded image-space consistency diagnostic over the two complete material views identified in M40. The value is useful for plumbing and diagnostic traceability, but it is not an accepted GT material metric and does not validate PBR material accuracy.

The original `texture_material/material_consistency` source metric remains visible in the augmented output with its original unavailable reason. The new row is namespaced as `texture_material_diagnostic/material_consistency_mae` with claim boundary `not_gt_pbr_material_accuracy`.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If the diagnostic is treated as GT PBR material accuracy, it fails.
- If source M32 metrics are overwritten, it fails.
- If SRD-GS superiority, rendering recovery, geometry superiority, or paper-scale claims are upgraded, it fails.
- If F-score zero, high LPIPS/Refl-LPIPS, missing accepted GT artifacts, or missing runtime logs are ignored, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_material_consistency_diagnostic` failed before `compute_material_consistency_m41.py` existed.
- Focused TDD GREEN: `python -m unittest tests.test_material_consistency_diagnostic` passed, 1 test.
- M41 diagnostic command passed and wrote five output artifacts under `outputs/srd_gs_material_consistency_m41`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 42 should remain bounded and choose the next remaining contract: accepted GT depth/material artifact protocol or runtime-cost logging. Do not launch broad paper-scale experiments.
