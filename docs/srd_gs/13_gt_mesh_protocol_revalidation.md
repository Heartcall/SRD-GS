# Milestone 13: GT Mesh Protocol Revalidation

## Status

Status: partial GO for accepted GT mesh geometry metrics on the existing `ball` smoke artifacts; broad paper-scale experiments remain NO-GO.

This milestone responds to the updated Shiny Blender Synthetic GT files. It does not launch new training. It updates the geometry protocol so explicit per-scene GT mesh files are accepted, while dataset-generated `points3d.ply` remains rejected by default.

## Changed Files

- `utils/geometry_eval_utils.py`
- `utils/srd_branch_policy.py`
- `gaussian_renderer/__init__.py`
- `eval_reflective_assets.py`
- `scripts/srd_gs/inspect_single_scene_validation.py`
- `tests/test_dataset_split_and_gt_protocol.py`
- `tests/test_geometry_eval_utils.py`
- `tests/test_single_scene_validation_gate.py`
- `tests/test_srd_branch_map_fallback_policy.py`
- `docs/srd_gs/12_single_scene_validation_gate.md`
- `docs/srd_gs/implementation_log.md`
- `docs/srd_gs/todo.md`
- `docs/srd_gs/final_implementation_summary.md`

## New Files

- `utils/srd_branch_policy.py`
- `docs/srd_gs/13_gt_mesh_protocol_revalidation.md`

## Output Artifacts

- `outputs/srd_gs_validation/ball_gt_mesh/single_scene_validation_report.json`
- `outputs/srd_gs_validation/ball_gt_mesh/single_scene_validation_report.md`
- `outputs/srd_gs_metric_chain/ball/refgs_baseline/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_metric_chain/ball/refgs_baseline/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_metric_chain/ball/full_srd_gs/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_metric_chain/ball/full_srd_gs/eval_with_gt_mesh/metrics.csv`

## GT Protocol Update

Accepted GT discovery now prefers:

```text
<scene>/<scene>_gt_mesh.ply
```

and falls back to:

```text
../gt/<scene>_gt_mesh.ply
```

For `ball`, the accepted GT path is:

```text
/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball/ball_gt_mesh.ply
```

`points3d.ply` remains classified as dataset-generated and is not accepted as GT without an explicit override.

## Validation Gate Result

For `ball`:

```text
Split gate: GO with eval=True, 100 train frames and 200 test frames.
GT geometry gate: GO, accepted GT mesh found at ball_gt_mesh.ply.
Branch-map gate: NO-GO, SRD branch maps are fallback buffers and not rasterized.
Paper-scale gate: NO-GO, blocker is srd_branch_maps_not_rasterized.
```

## Existing Smoke Metrics with Accepted GT Mesh

Scope:

```text
scene: ball
checkpoints: existing 20-iteration smoke outputs
render split: train, inherited from Milestone 11 metric-chain smoke
GT geometry: ball_gt_mesh.ply
geometry sample count: 1000
raw-coordinate evaluation: true
ICP/similarity alignment: disabled
```

Ref-GS baseline:

```text
PSNR: 5.505481592488225
SSIM: -0.4496866637560112
Refl-PSNR: 5.134208778536395
Refl-SSIM: -0.4397802384736969
Chamfer: 0.414306104183197
F-score: 0.0
Normal MAE: 88.8103256225586
```

SRD-GS:

```text
PSNR: 5.599180974605109
SSIM: -0.45348933767419447
Refl-PSNR: 5.266424581783996
Refl-SSIM: -0.4499297204646594
Chamfer: 0.4354441165924072
F-score: 0.001
Normal MAE: 87.3123779296875
```

Interpretation:

- These metrics prove the accepted-GT geometry metric chain now runs on the updated GT mesh.
- They do not prove SRD-GS is better than Ref-GS.
- The values are from 20-iteration smoke checkpoints and train-split render pairs, so they remain engineering validation rather than paper-scale evidence.

## Runtime/Dependency Fixes

- `utils/srd_branch_policy.py` holds the pure SRD branch-map fallback policy, avoiding a heavy `gaussian_renderer` import in protocol tests and validation scripts.
- ASCII PLY mesh loading now computes vertex normals from faces locally, avoiding `open3d` import for the updated GT mesh path.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_dataset_split_and_gt_protocol tests.test_geometry_eval_utils tests.test_single_scene_validation_gate tests.test_srd_branch_map_fallback_policy
conda run -n ref_gs python scripts/srd_gs/inspect_single_scene_validation.py --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' --eval --enable_srd_gs --output_dir outputs/srd_gs_validation/ball_gt_mesh
conda run -n ref_gs python eval_reflective_assets.py --eval_pairs_dir outputs/srd_gs_metric_chain/ball/refgs_baseline/render_eval_pairs --pred_geometry outputs/srd_gs_smoke/results/ball/refgs_baseline/mesh_unified.ply --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' --geometry_sample_count 1000 --fscore_threshold 0.01 --output_dir outputs/srd_gs_metric_chain/ball/refgs_baseline/eval_with_gt_mesh
conda run -n ref_gs python eval_reflective_assets.py --eval_pairs_dir outputs/srd_gs_metric_chain/ball/full_srd_gs/render_eval_pairs --pred_geometry outputs/srd_gs_smoke/results/ball/full_srd_gs/mesh_surface.ply --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' --geometry_sample_count 1000 --fscore_threshold 0.01 --output_dir outputs/srd_gs_metric_chain/ball/full_srd_gs/eval_with_gt_mesh
```

Result:

- focused tests: passed, 12 tests.
- validation report generation: passed.
- Ref-GS accepted-GT eval: passed.
- SRD-GS accepted-GT eval: passed.

## Needs Runtime Verification

- One-scene checkpoints still need to be regenerated with `eval=True` before test-split render metrics are claim-bearing.
- The accepted GT mesh protocol should be expanded scene-by-scene before multi-scene paper-scale claims.
- True SRD branch-map rasterization remains unimplemented.

## Next Recommended Milestone

Milestone 14 should implement a true SRD branch-map rasterization path or explicitly scope a longer single-scene `eval=True` run while keeping branch-map claims blocked.
