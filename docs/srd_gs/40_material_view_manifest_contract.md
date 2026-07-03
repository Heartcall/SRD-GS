# Milestone 40: Material-view manifest contract

Status: read-only material-view manifest GO; material consistency still not computed; paper-scale still blocked

## Objective

Implement one bounded remaining unavailable-metric contract after M39. This milestone defines a material-view manifest from existing M32 render-eval artifacts so future material-consistency computation has an explicit input contract.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: existing M32 render-eval artifacts can define a material-view manifest with two complete material views.
- Allowed claim: the missing material-view-manifest contract is reduced for the existing M32 `ball` artifact set.
- Allowed claim: the source `texture_material/material_consistency` metric remains uncomputed and source metrics are not overwritten.
- Disallowed claim: material consistency is measured.
- Disallowed claim: GT PBR material accuracy is validated.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/build_material_view_manifest_m40.py`.
- Added `tests/test_material_view_manifest_contract.py`.
- The script consumes:
  - M32 `render_eval_pairs/render_eval_manifest.json`
  - M32 `render_eval_pairs/*`
  - M32 `eval_with_gt_mesh/metrics.csv`
- The script writes:
  - `material_view_manifest.json`
  - `material_view_manifest.csv`
  - `material_view_contract_summary.json`
  - `material_view_contract_report.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/build_material_view_manifest_m40.py \
  --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --eval_pairs_dir outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --output_dir outputs/srd_gs_material_view_manifest_m40
```

## Outputs

- `outputs/srd_gs_material_view_manifest_m40/material_view_manifest.json`
- `outputs/srd_gs_material_view_manifest_m40/material_view_manifest.csv`
- `outputs/srd_gs_material_view_manifest_m40/material_view_contract_summary.json`
- `outputs/srd_gs_material_view_manifest_m40/material_view_contract_report.md`

## Key Results

| Field | Value |
| --- | --- |
| Contract status | `ready_for_future_material_consistency_compute` |
| Complete material views | `2` |
| Total manifest frames | `2` |
| Source material-consistency reason | `need_at_least_two_material_views` |
| Material consistency computed | `false` |
| Source metrics overwritten | `false` |

## Interpretation

M40 turns the prior missing material-view-manifest blocker into a concrete manifest for the existing two-frame M32 `ball` artifact set. Both views have the required `diffuse_rgb` and `roughness_map` artifacts, plus optional normal/RGB/specular/gate artifacts.

This does not compute material consistency and does not validate PBR material accuracy. The remaining blocker is now the metric computation itself, plus accepted GT depth/material artifacts and runtime-cost logs.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If material-view readiness is treated as material-consistency metric evidence, it fails.
- If source M32 metrics are overwritten, it fails.
- If GT PBR material accuracy, SRD-GS superiority, rendering recovery, or paper-scale claims are upgraded, it fails.
- If F-score zero, high LPIPS/Refl-LPIPS, missing GT artifacts, or missing runtime logs are ignored, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_material_view_manifest_contract` failed before `build_material_view_manifest_m40.py` existed.
- Focused TDD GREEN: `python -m unittest tests.test_material_view_manifest_contract` passed, 1 test.
- M40 manifest command passed and wrote four output artifacts under `outputs/srd_gs_material_view_manifest_m40`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 41 should remain bounded. A reasonable next step is a read-only/dry-run-first material-consistency diagnostic computation from the M40 manifest, while keeping it separate from GT PBR material accuracy. Accepted GT depth/material protocol or runtime-cost logging are still valid alternatives. Do not launch broad paper-scale experiments.
