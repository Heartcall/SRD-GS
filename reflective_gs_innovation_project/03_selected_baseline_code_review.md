# Selected Baseline Code Review

## Repository
`external_repos/Ref-GS`, remote `https://github.com/YoujiaZhang/Ref-GS.git`, commit `bf843b7 Update README.md`.

## Paper
`Ref-GS: Directional Factorization for 2D Gaussian Splatting`

## Why Selected
From Literature: Ref-GS is directly about reflective 2DGS and has public code. From Code Inspection: the code already includes surface-like 2DGS rasterizers, directional encoding, roughness, albedo, and a mesh extraction utility, making it an implementable anchor.

## Code Structure
- `README.md`: setup, dataset, training, mesh extraction note.
- `arguments/__init__.py`: CLI/model/optimization parameters.
- `scene/gaussian_model.py`: `SphMipEncoding`, `GaussianModel`, Gaussian attributes, optimizer, save/load/densification.
- `gaussian_renderer/__init__.py`: `render`, `render_nerf`, `render_real`.
- `train.py`, `train-NeRF.py`, `train-NeRO.py`, `train-real.py`: dataset-specific training loops.
- `utils/loss_utils.py`: L1, SSIM, BCE, entropy, TV.
- `utils/mesh_utils.py`: `GaussianExtractor`, TSDF and unbounded mesh extraction utilities.
- `scene/dataset_readers.py`, `scene/cameras.py`, `utils/camera_utils.py`: camera/data loading.

## Training Pipeline
From Code Inspection:
- `train.py::training()` creates `GaussianModel`, `Scene`, optimizer, samples one training camera per iteration, calls `render()`, computes RGB reconstruction loss, optional alpha BCE for first 3000 iterations, normal-depth consistency, densification and optimizer step (`external_repos/Ref-GS/train.py:27-132`).
- Main image loss: `loss_pbr = (1 - lambda_dssim) * L1 + lambda_dssim * (1 - SSIM)` on final `pbr_rgb` (`train.py:82-85`).
- Normal loss: `normal_error = 1 - (rend_normal * surf_normal).sum(dim=0)` (`train.py:96-102`).
- `train-real.py` additionally uses `ref_w` / `out_w` masks from `render_real()` for real-scene background/environment split (`external_repos/Ref-GS/train-real.py:84-110`).

## Dataset / Scene Loading
From Code Inspection:
- `Scene.__init__()` loads COLMAP if `sparse` exists, Blender if `transforms_train.json` exists (`external_repos/Ref-GS/scene/__init__.py:42-48`).
- `dataset_readers.readCamerasFromTransforms()` supports Blender transforms, optional alpha masks, and GlossyReal focal fields (`external_repos/Ref-GS/scene/dataset_readers.py:197-264`).
- `camera_utils.loadCam()` computes per-pixel `rays_d` and stores it in `Camera` (`external_repos/Ref-GS/utils/camera_utils.py:53-96`).

## Gaussian Representation
From Code Inspection:
- `GaussianModel` stores base GS parameters `_xyz`, `_features_dc`, `_features_rest`, `_scaling`, `_rotation`, `_opacity` (`scene/gaussian_model.py:97-106`).
- It adds `_albedo`, `_roughness`, `_mask`, `_language_feature` at initialization (`scene/gaussian_model.py:253-256`).
- It creates `SphMipEncoding` as `dir_encoding` and `light_mlp` for directional specular prediction (`scene/gaussian_model.py:124-137`).
- Optimizer groups include `albedo`, `roughness`, `mask`, `feature`, `light_mlp`, and `dir_encoding` (`scene/gaussian_model.py:263-280`).

Current limitation found from code: there is no separate `G_surface` and `G_reflection`; all appearance/material/directional attributes are attached to the same Gaussian set.

## Rendering Pipeline
From Code Inspection:
- `render()` rasterizes `gs_albedo` and `input_ts = [roughness, feature]` through `GaussianRasterizer` (`gaussian_renderer/__init__.py:84-100`).
- It reads `rend_alpha`, `rend_normal`, expected/median depth and `rend_dist` from `allmap` (`gaussian_renderer/__init__.py:102-117`).
- It computes `surf_normal = depth_to_normal(viewpoint_camera, surf_depth)` (`gaussian_renderer/__init__.py:117-121`).
- It computes reflected direction `wo = reflect(-viewdirs, normals)` (`gaussian_renderer/__init__.py:125-127`).
- It uses roughness as spherical Mip level, queries `pc.dir_encoding`, combines directional feature with per-pixel feature map, predicts `spec_light`, sets `diff_light = albedo_map`, and outputs `pbr_rgb = linear2srgb(spec_light + diff_light)` (`gaussian_renderer/__init__.py:151-174`).

## Loss Computation
From Code Inspection:
- Implemented losses are generic L1/SSIM/BCE/entropy/TV in `utils/loss_utils.py`.
- `train.py` applies photometric loss on final `pbr_rgb`, alpha BCE early, and normal-depth consistency (`train.py:82-102`).
- Not implemented in baseline: explicit branch separation loss, specular residual sparsity, reflection transport consistency, albedo consistency across views, texture de-specularization loss, mesh-aware loss.

## Reflection / Material Modeling
From Code Inspection:
- Reflection direction is represented through `wo` and `SphMipEncoding`.
- Roughness is a scalar per Gaussian and is rasterized to `roughness_map`.
- `albedo_map` is used as diffuse term, but there is no code-level guarantee that it is specular-free.
- `light_mlp` predicts `spec_light` from directional encoding and feature map.
- not implemented in baseline: explicit near-field local reflection Gaussians for selected repo; explicit BRDF parameters such as metallic/F0; physically valid environment visibility; reflection-source correspondence loss.

## Mesh / Texture Output
From Code Inspection:
- README says mesh extraction adopts 2DGS method.
- `utils/mesh_utils.py::GaussianExtractor.reconstruction()` expects `render_pkg['render']`, `rend_alpha`, `rend_normal`, `surf_depth`, `surf_normal` (`utils/mesh_utils.py:90-114`).
- `extract_mesh_bounded()` uses Open3D TSDF fusion from rendered RGB/depth (`utils/mesh_utils.py:130-172`).
- `extract_mesh_unbounded()` supports contracted marching cubes and vertex color assignment (`utils/mesh_utils.py:175-272`).
- not implemented in baseline: explicit script entry point for mesh extraction in repo root; UV unwrapping; albedo/roughness/metallic/normal texture map export; specular-free texture baking.
- Code risk: `utils/mesh_utils.py` imports `utils.render_utils`, but no `utils/render_utils.py` exists in the cloned repository, so this utility path needs repair before runtime use (`utils/mesh_utils.py:17`, `:120`).

## Evaluation Scripts
From Code Inspection:
- Training scripts include a `training_report()` that prints PSNR, but it is not called in the visible main loop and refers to `render_pkg["render"]`, while `render()` for reflective training returns `pbr_rgb` but no `"render"` key (`train.py:181-202`, `gaussian_renderer/__init__.py:182-190`).
- LPIPS implementation exists under `lpipsPyTorch`, but no unified evaluation script was found.
- not implemented in baseline: Chamfer/F-score evaluation, normal MAE, reflective-region metrics, highlight leakage, relighting evaluation.

## Configuration Files
- `arguments/__init__.py` defines `run_dim`, `albedo_bias`, `gsrgb_loss`, `rand_init`, `init_until_iter`, `env_scope_center`, `env_scope_radius`, `alpha_weight`, `xyz_axis` (`arguments/__init__.py:50-73`).
- `OptimizationParams` defines `albedo_lr`, `mask_lr`, `roughness_lr`, `encoding_lr`, `mlp_lr`, `lambda_dssim`, `lambda_dist`, `lambda_normal`, densification settings (`arguments/__init__.py:90-120`).
- `train.sh` contains scene-specific command templates for Shiny Blender Real, refnerf, NeRF Synthetic, and Glossy Synthetic.

## Current Limitations Found from Code
1. Derived Analysis: no `G_surface` / `G_reflection` separation; one Gaussian set stores geometry, diffuse, roughness, feature and specular predictor inputs.
2. Derived Analysis: final photometric loss supervises `pbr_rgb`, so gradients from specular residual can flow into geometry-bearing variables unless explicitly detached or gated.
3. Derived Analysis: `albedo_map` is treated as diffuse light term, but there is no multi-view material consistency or specular-free baking objective.
4. Derived Analysis: mesh extraction uses rendered depth/normal/RGB, not a protected surface-only branch.
5. Derived Analysis: texture/material export is not implemented in baseline.
6. Needs Verification: runtime mesh extraction may fail without adding or restoring `utils/render_utils.py`.

## Modification Points for Proposed Method
| File | Class / Function | Current Variable | Proposed Insertion |
|---|---|---|---|
| `scene/gaussian_model.py` | `GaussianModel.__init__` | `_xyz`, `_opacity`, `_albedo`, `_roughness`, `_language_feature` | add `surface_*` and `reflection_*` branch parameters or a `branch_gate`; add PBR fields `metallic`, `specular_weight`, `transport_feature`. |
| `scene/gaussian_model.py` | `training_setup` | optimizer param groups | add LR groups for reflection branch, transport feature, material maps; allow staged freezing. |
| `gaussian_renderer/__init__.py` | `render` | `pbr_rgb`, `spec_light`, `diff_light`, `surf_depth`, `surf_normal` | return `diffuse_rgb`, `specular_rgb`, `reflection_dir`, `roughness_map`, `transport_feature_map`, `branch_gate_map`; optionally detach geometry path for reflection branch. |
| `train.py` / `train-NeRO.py` / `train-real.py` | `training` | `loss_pbr`, `normal_loss` | add staged losses: geometry-only warmup, separation, material consistency, transport consistency, texture baking preview loss. |
| `utils/loss_utils.py` | new functions | none | add `branch_separation_loss`, `transport_consistency_loss`, `highlight_leakage_loss`, `material_consistency_loss`. |
| `utils/mesh_utils.py` | `GaussianExtractor` | rendered depth/RGB from current render | support `surface_only=True`; extract mesh from surface branch depth/normal only. |
| new `utils/texture_baking.py` | new module | not implemented | bake UV albedo/roughness/normal maps using multi-view robust aggregation and specular weights. |
| new `eval_reflective_assets.py` | new script | not implemented | compute Refl-PSNR/LPIPS, Chamfer/F-score, normal MAE, highlight leakage, relighting metrics. |

## Implementation Risks
- Potential Hypothesis: reflection branch may absorb geometry error unless constrained by surface-only alpha/depth/normal and residual sparsity.
- Potential Hypothesis: surface branch may still bake highlights into albedo without specular mask or robust texel aggregation.
- Needs Verification: actual extension requires successful CUDA extension build and `utils.render_utils` repair.
- Needs Verification: material GT availability differs across datasets; roughness/metallic claims must be bounded.
