# Milestone 11: Claim-bearing Metric Chain Repair

## Status

Status: partial GO for single-scene claim-bearing metric-chain repair; broad paper-scale experiments remain blocked.

Current evidence:

- Ref-GS baseline and SRD-GS both produce non-null PSNR, SSIM, Refl-PSNR, and Refl-SSIM on the existing one-scene 20-iteration `ball` smoke checkpoint.
- With explicit `--accept_dataset_points3d_as_gt`, both variants produce non-null Chamfer, F-score, and normal MAE against `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball/points3d.ply`.
- This does not support a claim that SRD-GS is better than Ref-GS.
- The `points3d.ply` reference is treated as a dataset geometry candidate that still needs manual dataset/protocol verification before paper-scale claims.

## Changed Files

- `gaussian_renderer/__init__.py`
- `configs/srd_gs/full_srd_gs.yaml`
- `eval_reflective_assets.py`
- `utils/geometry_eval_utils.py`
- `docs/srd_gs/implementation_log.md`
- `docs/srd_gs/todo.md`

## New Files

- `render_eval_pairs.py`
- `utils/geometry_eval_utils.py`
- `scripts/srd_gs/run_eval_one_scene.sh`
- `tests/test_render_eval_pairs_static.py`
- `tests/test_eval_pair_metric_chain.py`
- `tests/test_geometry_eval_utils.py`
- `tests/test_srd_branch_map_fallback_policy.py`
- `docs/srd_gs/11_claim_metric_chain_repair.md`

## Tests Run

Commands run during this milestone:

```bash
conda run -n ref_gs python -m unittest tests.test_srd_branch_map_fallback_policy tests.test_render_eval_pairs_static tests.test_eval_pair_metric_chain tests.test_geometry_eval_utils
conda run -n ref_gs python -m py_compile render_eval_pairs.py eval_reflective_assets.py utils/metric_utils.py utils/geometry_eval_utils.py gaussian_renderer/__init__.py
bash scripts/srd_gs/run_eval_one_scene.sh --model_path outputs/srd_gs_smoke/models/ball/refgs_baseline --variant refgs_baseline --iteration 20 --split train --max_views 2 --execute
bash scripts/srd_gs/run_eval_one_scene.sh --model_path outputs/srd_gs_smoke/models/ball/full_srd_gs --variant full_srd_gs --iteration 20 --split train --max_views 2 --enable_srd_gs --execute
conda run -n ref_gs python eval_reflective_assets.py --eval_pairs_dir outputs/srd_gs_metric_chain/ball/refgs_baseline/render_eval_pairs --pred_geometry outputs/srd_gs_smoke/results/ball/refgs_baseline/mesh_unified.ply --gt_geometry_path /data/liuly/dataset/3DGS/Shiny\ Blender\ Synthetic/ball/points3d.ply --accept_dataset_points3d_as_gt --geometry_sample_count 1000 --fscore_threshold 0.01 --output_dir outputs/srd_gs_metric_chain/ball/refgs_baseline/eval_with_candidate_gt
conda run -n ref_gs python eval_reflective_assets.py --eval_pairs_dir outputs/srd_gs_metric_chain/ball/full_srd_gs/render_eval_pairs --pred_geometry outputs/srd_gs_smoke/results/ball/full_srd_gs/mesh_surface.ply --gt_geometry_path /data/liuly/dataset/3DGS/Shiny\ Blender\ Synthetic/ball/points3d.ply --accept_dataset_points3d_as_gt --geometry_sample_count 1000 --fscore_threshold 0.01 --output_dir outputs/srd_gs_metric_chain/ball/full_srd_gs/eval_with_candidate_gt
```

Final verification:

```bash
conda run -n ref_gs python -m py_compile render_eval_pairs.py eval_reflective_assets.py utils/metric_utils.py utils/geometry_eval_utils.py gaussian_renderer/__init__.py
conda run -n ref_gs python -m unittest discover -s tests
bash -n scripts/srd_gs/run_eval_one_scene.sh
git diff --check
```

Result:

- py_compile: passed.
- unittest discover: passed, 46 tests.
- shell syntax check: passed.
- git diff whitespace check: passed.
- required M11 artifact existence checks: passed.
- prohibited process scan: no matching train/render/eval/export process found.

## Passed

- New M11 unit tests passed during focused verification.
- `render_eval_pairs.py` exported eval pairs for both variants from existing 20-iteration checkpoints.
- `eval_reflective_assets.py` consumed the pair directory and wrote non-null RGB/reflective metrics.
- Geometry utility loaded candidate `points3d.ply` and predicted meshes when explicit acceptance was provided.

## Failed

- Initial `test` split render failed because the loaded checkpoint config has `eval=False`; test cameras are empty. The smoke was rerun on the `train` split with `max_views=2`.
- Initial sandboxed CUDA render failed with `No CUDA GPUs are available`; the bounded single-scene commands were rerun outside the sandbox.
- Geometry metrics are not automatically enabled from dataset candidate files; this is intentional to avoid silently promoting dataset assets to accepted GT.

## Renderer Branch-map Diagnosis

Question: `branch_gate_map` 是否来自真实 rasterization？

- Answer: No.
- Evidence: `gaussian_renderer/__init__.py` does not concatenate `pc.get_branch_gate` into `language_feature_precomp`; current code comments explicitly mark `rasterizer_extra_channels_unsupported`.
- Manifest status: `branch_gate_map.rasterized=false`, `backward_to_gaussian=false`.

Question: `specular_weight_map` 是否来自真实 rasterization？

- Answer: No.
- Evidence: current feature-channel rasterization only receives `surface_roughness + reflection_feature`; `specular_weight` is not passed to the rasterizer.
- Manifest status: `specular_weight_map.rasterized=false`, `backward_to_gaussian=false`.

Question: `transport_feature_map` 是否来自真实 rasterization？

- Answer: No.
- Evidence: `transport_feature` is not passed to the rasterizer.
- Manifest status: `transport_feature_map.rasterized=false`, `backward_to_gaussian=false`.

Question: these maps 是否可反传到对应 Gaussian 参数？

- Answer: No for branch gate, specular weight, and transport feature under the current fallback.
- Current trainable SRD Gaussian parameters still exist in `scene/gaussian_model.py`, but these rendered maps do not form a rasterized differentiable path to those specific parameters.

Question: `--srd_use_branch_gate` in `full_srd_gs.yaml` 是否会因为 fallback 导致 specular contribution 异常压低？

- Before Milestone 11: yes. Missing branch-gate channels fell back to zero when `use_branch_gate=True`, suppressing specular contribution.
- After Milestone 11: the fallback is neutral. `branch_gate_map` falls back to 1.0 and `gate_applied=false`, so missing branch maps do not suppress specular.
- `configs/srd_gs/full_srd_gs.yaml` no longer enables `--srd_use_branch_gate`; it records `branch_gate_policy: fallback_neutral_gate_until_rasterizer_backward_support`.

## Chosen Fallback/Fix Policy

Chosen policy: Option C.

Reason:

- Option A requires extending and rebuilding the CUDA rasterizer ABI and backward implementation.
- Option B requires a second differentiable rasterization pass and still needs runtime validation.
- Option C is the safest immediate repair before metric-chain work: disable branch-gate use in the full config and make runtime fallback neutral rather than specular-suppressing.

Policy:

```text
branch_gate_map: fallback value 1.0, not rasterized, no backward to Gaussian branch_gate
specular_weight_map: fallback value 1.0, not rasterized, no backward to Gaussian specular_weight
transport_feature_map: fallback value 0.0, not rasterized, no backward to Gaussian transport_feature
```

Status: Needs Runtime Verification for any future claim that branch maps are physically valid or train the intended Gaussian branch parameters.

## Render Eval Artifact Schema

`render_eval_pairs.py` writes:

```text
render_eval_pairs/
├── pred_rgb/
├── gt_rgb/
├── diffuse_rgb/
├── specular_rgb/
├── surface_depth/
├── surface_normal/
├── roughness_map/
├── branch_gate_map/
├── reflective_mask/
├── reflective_mask.png
└── render_eval_manifest.json
```

Manifest rules:

- `pred_rgb` is rendered `pbr_rgb`.
- `gt_rgb` is camera `original_image[:3]`.
- `diffuse_rgb` and `specular_rgb` are exported only when returned by the renderer.
- `surface_depth`, `surface_normal`, `roughness_map`, and `branch_gate_map` are diagnostic buffers.
- `reflective_mask.png` is saved when auto residual mask is enabled.
- Missing fields keep explicit `not_available_reason`.
- Final RGB is not exported as albedo.

## Metrics That Are Now Non-null

Smoke scope:

- Scene: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
- Existing checkpoints: `outputs/srd_gs_smoke/models/ball/*/point_cloud/iteration_20`
- Split used: `train`
- Views used: `2`

Ref-GS baseline:

```text
PSNR: 5.505481592488225
SSIM: -0.4496866637560112
Refl-PSNR: 5.134208778536395
Refl-SSIM: -0.4397802384736969
Chamfer(candidate GT): 0.29737281799316406
F-score(candidate GT): 0.0
Normal MAE(candidate GT): 90.0
```

SRD-GS:

```text
PSNR: 5.599180974605109
SSIM: -0.45348933767419447
Refl-PSNR: 5.266424581783996
Refl-SSIM: -0.4499297204646594
Chamfer(candidate GT): 0.3062840402126312
F-score(candidate GT): 0.0
Normal MAE(candidate GT): 90.0
```

Interpretation:

- These values prove that the metric chain can produce non-null claim-bearing fields.
- They do not prove SRD-GS is better than Ref-GS.
- The rendering values are from a 20-iteration smoke and are expected to be low-quality.
- Candidate-GT geometry values require dataset/protocol verification before paper-scale use.

## Metrics Still Null and Why

- LPIPS: null; `lpips_not_available`.
- Refl-LPIPS: null; `lpips_not_available`.
- Depth error: null; GT depth is not loaded.
- Highlight leakage score in this eval path: null; texture baking artifacts are not passed to `eval_reflective_assets.py` in the render-pair eval command.
- Albedo error: null; GT albedo is not available.
- Roughness error: null; GT roughness is not available.
- Material consistency: null; at least two material-view maps are required.

## GT Geometry Loading Status

Dataset path:

```text
/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball
```

Detected candidate:

```text
/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball/points3d.ply
```

Detected candidate properties:

```text
vertex_count: 100000
properties: x, y, z, nx, ny, nz, red, green, blue
```

Protocol:

- Coordinate system: dataset raw coordinates.
- Scale policy: no rescale.
- Raw-coordinate evaluation: primary.
- ICP: disabled by default; optional only.
- Sampling count for smoke: 1000.
- F-score threshold for smoke: 0.01.
- Normal MAE requires predicted mesh normals and GT normals; predicted mesh normals are computed from mesh faces when vertex normals are absent.

Acceptance status:

- Default status: `Needs Dataset Verification`.
- Metrics were computed only with explicit `--accept_dataset_points3d_as_gt`.
- Before paper-scale use, a human must confirm that `points3d.ply` is the accepted GT reference for this dataset and metric protocol.

## Whether Broad Paper-scale Experiments Are Now Allowed

Allowed: no.

Reason:

- The metric chain is repaired for one-scene smoke, but SRD branch maps still use fallback rather than true differentiable rasterization.
- Candidate GT geometry requires manual verification before being used as paper-scale ground truth.
- Rendering evaluation used `train` split because current smoke checkpoints were created with `eval=False`; paper-scale evaluation needs proper train/test split export.
- Current evidence is from 20-iteration checkpoints and 2 views only.

## Recommended Next Milestone

Milestone 12 should be a bounded single-scene validation milestone, not broad paper-scale execution:

1. Re-run one scene with `eval=True` or regenerate checkpoints with test cameras available.
2. Decide and document whether `points3d.ply` is accepted GT for Shiny Blender Synthetic `ball`.
3. Add an Option A or Option B implementation plan for true SRD branch-map rasterization.
4. Run one longer single-scene Ref-GS vs SRD-GS comparison after the above gates pass.
5. Only then reconsider multi-scene paper-scale experiments.
