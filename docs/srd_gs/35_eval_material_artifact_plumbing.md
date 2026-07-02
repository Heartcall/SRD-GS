# Milestone 35: Eval/material artifact plumbing audit

Status: read-only artifact-plumbing GO; one export-diagnostic bridge candidate found; paper-scale still blocked

## Objective

Implement the M34-selected `eval_material_artifact_plumbing` direction as a bounded read-only milestone. This milestone audits existing M32 unavailable metrics, maps them to required artifacts, and classifies whether each metric is blocked by missing GT, missing optional dependency, missing runtime logs, missing material-view contracts, or ready for a future plumbing bridge.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: M35 maps the ten M32 unavailable metrics to concrete artifact requirements and blocker classes.
- Allowed claim: existing texture-export highlight-leakage artifacts are available as a future eval-summary plumbing candidate.
- Allowed claim: the highlight-leakage candidate must remain labeled as an export diagnostic, not a GT PBR material accuracy metric.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, PBR material accuracy, or paper-scale quality is validated.
- Disallowed claim: unavailable GT/dependency/runtime metrics are solved.

## Implementation

- Added `scripts/srd_gs/audit_eval_material_artifacts_m35.py`.
- Added `tests/test_eval_material_artifact_plumbing.py`.
- The script consumes existing M32 artifacts:
  - `eval_with_gt_mesh/metrics.csv`
  - `eval_with_gt_mesh/failure_case_panels/failure_summary.md`
  - `render_eval_pairs/render_eval_manifest.json`
  - `pbr_textures_specular_free/*`
- The script writes:
  - `eval_material_artifact_requirements.csv`
  - `eval_material_artifact_plan.json`
  - `eval_material_artifact_plan.md`

## Command

```bash
python scripts/srd_gs/audit_eval_material_artifacts_m35.py \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --failure_summary outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md \
  --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --result_root outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_dir outputs/srd_gs_eval_material_plumbing_m35
```

## Outputs

- `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_requirements.csv`
- `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_plan.json`
- `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_plan.md`

## Artifact Requirement Summary

| Status | Count | Metrics |
| --- | ---: | --- |
| `plumbing_candidate` | 1 | `texture_material/highlight_leakage_score` |
| `blocked_missing_dependency` | 2 | `rendering/lpips`, `reflective_region/refl_lpips` |
| `blocked_missing_gt` | 3 | `geometry/depth_error`, `texture_material/albedo_error`, `texture_material/roughness_error` |
| `blocked_missing_material_view_manifest` | 1 | `texture_material/material_consistency` |
| `blocked_missing_runtime_log` | 3 | `runtime/training_time`, `runtime/peak_memory`, `runtime/render_fps` |

## Interpretation

M35 reduces the M33/M34 "ten unavailable metrics" blocker into a concrete action map. The only immediate read-only/dry-run-first implementation candidate is an eval-summary bridge for texture export highlight-leakage artifacts:

- `pbr_textures_specular_free/baking_report.json`
- `pbr_textures_specular_free/highlight_leakage_mask.png`

This candidate is not a GT material metric. It can only support a labeled export diagnostic unless accepted GT material artifacts are added later.

LPIPS/refl-LPIPS still need the optional `lpips` dependency or an explicit dependency gate. Depth, albedo, and roughness errors need accepted GT artifacts. Runtime metrics need timing/memory/FPS logs from a future bounded runtime. Material consistency needs a material-view manifest before it can be treated as a metric.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, or evaluation, it fails.
- If export highlight leakage is treated as GT PBR accuracy, it fails.
- If missing GT/dependency/runtime-log metrics are marked solved, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_eval_material_artifact_plumbing` failed before `audit_eval_material_artifacts_m35.py` existed.
- Focused TDD GREEN: `python -m unittest tests.test_eval_material_artifact_plumbing` passed, 1 test.
- M35 audit command passed and wrote the three output artifacts under `outputs/srd_gs_eval_material_plumbing_m35`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 36 should implement a read-only/dry-run-first highlight-leakage export diagnostic bridge from texture baking artifacts into eval/material summaries, keeping it separate from GT material accuracy. Do not launch broad paper-scale experiments.
