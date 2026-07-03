# Milestone 42: Accepted-GT depth/material protocol audit

Status: read-only GT-protocol audit GO; depth/material GT still missing; paper-scale still blocked

## Objective

Implement one bounded remaining contract after M41: audit whether accepted GT depth/material artifacts exist for the current M32/M41 `ball` evidence chain. This milestone inventories source-side depth/albedo/roughness candidates and result-side prediction artifacts, then classifies future metric-readiness without computing metrics.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M42 classifies accepted-GT depth/material protocol readiness for existing `ball` artifacts.
- Allowed claim: prediction artifacts are present for `depth_error`, `albedo_error`, and `roughness_error`.
- Allowed claim: no accepted GT candidates were found for depth, albedo, or roughness under the audited `ball` source path.
- Disallowed claim: depth/albedo/roughness metric values were computed.
- Disallowed claim: accepted GT semantic correctness is established.
- Disallowed claim: GT PBR material accuracy is validated.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.

## Implementation

- Added `scripts/srd_gs/audit_gt_depth_material_protocol_m42.py`.
- Added `tests/test_gt_depth_material_protocol.py`.
- The script consumes:
  - source path `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
  - M32 result root `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300`
  - M32 `eval_with_gt_mesh/metrics.csv`
- The script writes:
  - `gt_depth_material_protocol.csv`
  - `gt_depth_material_candidates.csv`
  - `gt_depth_material_protocol.json`
  - `gt_depth_material_protocol.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/audit_gt_depth_material_protocol_m42.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --result_root outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --output_dir outputs/srd_gs_gt_depth_material_protocol_m42
```

## Outputs

- `outputs/srd_gs_gt_depth_material_protocol_m42/gt_depth_material_protocol.csv`
- `outputs/srd_gs_gt_depth_material_protocol_m42/gt_depth_material_candidates.csv`
- `outputs/srd_gs_gt_depth_material_protocol_m42/gt_depth_material_protocol.json`
- `outputs/srd_gs_gt_depth_material_protocol_m42/gt_depth_material_protocol.md`

## Key Results

| Metric | Status | GT candidates | Prediction artifact |
| --- | --- | ---: | --- |
| `geometry/depth_error` | `blocked_missing_accepted_gt` | 0 | true |
| `texture_material/albedo_error` | `blocked_missing_accepted_gt` | 0 | true |
| `texture_material/roughness_error` | `blocked_missing_accepted_gt` | 0 | true |

Summary:

- Ready contracts: 0
- Blocked contracts: 3
- GT candidates inventoried: 0
- Metrics computed: false

## Interpretation

M42 confirms that the prediction side is not the current blocker for depth/albedo/roughness metrics in the M32 `ball` chain: prediction depth, albedo, and roughness artifacts exist. The blocker is source-side accepted GT depth/material artifacts. The audited source path contains normal/alpha-style files, but no depth/albedo/roughness candidates matching the accepted protocol patterns.

This means depth/material metric values remain unavailable and must not be inferred from existing prediction or diagnostic outputs.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If candidate inventory is treated as metric computation, it fails.
- If prediction artifacts are treated as GT, it fails.
- If GT PBR material accuracy, SRD-GS superiority, rendering recovery, or paper-scale claims are upgraded, it fails.
- If missing accepted GT artifacts, F-score zero, high LPIPS/Refl-LPIPS, or missing runtime logs are ignored, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_gt_depth_material_protocol` failed before `audit_gt_depth_material_protocol_m42.py` existed.
- Focused TDD GREEN: `python -m unittest tests.test_gt_depth_material_protocol` passed, 1 test.
- M42 audit command passed and wrote four output artifacts under `outputs/srd_gs_gt_depth_material_protocol_m42`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 43 should remain bounded. A reasonable next step is runtime-cost logging contract plumbing, since accepted GT depth/material metrics remain blocked by missing source artifacts. Do not launch broad paper-scale experiments.
