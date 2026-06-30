# Implementation Plan

## Target Repository
`external_repos/Ref-GS` cloned from `https://github.com/YoujiaZhang/Ref-GS.git`, commit `bf843b7`.

Runtime validation: Needs Verification. No training or CUDA extension build was run in this task.

## Environment Setup
From Literature / README:
```bash
conda create -n ref_gs python=3.7.16
conda activate ref_gs
pip install -r requirements.txt
pip install submodules/diff-surfel-rasterization-real
pip install submodules/diff-surfel-rasterization
pip install submodules/diff-surfel-2dgs
pip install submodules/simple-knn
git clone https://github.com/NVlabs/nvdiffrast
pip install .
```

Needs Verification:
- CUDA extension compilation;
- `nvdiffrast` install;
- missing `utils/render_utils.py` required by `utils/mesh_utils.py`.

## Files to Inspect
- `README.md`
- `arguments/__init__.py`
- `scene/gaussian_model.py`
- `gaussian_renderer/__init__.py`
- `train.py`
- `train-NeRF.py`
- `train-NeRO.py`
- `train-real.py`
- `utils/loss_utils.py`
- `utils/mesh_utils.py`
- `scene/dataset_readers.py`
- `scene/cameras.py`
- `utils/camera_utils.py`
- submodule rasterizer bindings under `submodules/diff-surfel-*`

## Files to Modify
| file path | class name | function name | variable name | current behavior | proposed modification | risk | test method |
|---|---|---|---|---|---|---|---|
| `scene/gaussian_model.py` | `GaussianModel` | `__init__` | `_albedo`, `_roughness`, `_language_feature` | one Gaussian set stores surface and reflection inputs | add branch-aware parameters: `_surface_albedo`, `_surface_roughness`, `_reflection_feature`, `_specular_weight`, `_branch_gate` | parameter count confound | unit check tensor shapes and optimizer groups |
| `scene/gaussian_model.py` | `GaussianModel` | `training_setup` | optimizer groups | all parameters train together | add stage-controlled LR/freeze groups for surface/reflection | branch freeze bugs | optimizer group name test |
| `scene/gaussian_model.py` | `GaussianModel` | `save_ply/load_ply` | PLY attributes | saves albedo/roughness/mask/features | save/load branch attributes and material fields | incompatible checkpoints | round-trip save/load test |
| `gaussian_renderer/__init__.py` | none | `render` | `pbr_rgb`, `spec_light`, `diff_light` | returns final RGB and geometry buffers | return separated `surface_rgb`, `diffuse_rgb`, `specular_rgb`, `reflection_dir`, `branch_gate_map`, `transport_feature_map` | memory overhead | static output-key test and one mini render |
| `gaussian_renderer/__init__.py` | none | `render_real` | `ref_w`, `out_w` | real-scene env split by sphere | integrate branch gate and surface/reflection outputs | interaction with env scope | render key compatibility test |
| `train.py` | none | `training` | `loss_pbr`, `normal_loss` | photometric + alpha + normal | add staged losses and detach options | PSNR drop or instability | one-scene smoke train 100-500 iterations |
| `utils/loss_utils.py` | none | new functions | `L_sep`, `L_ref`, `L_mat`, `L_tex` | not implemented | implement differentiable branch/material/transport losses | bad masks/correspondence | synthetic tensor unit tests |
| `utils/mesh_utils.py` | `GaussianExtractor` | `reconstruction` | `rgb`, `depth`, `normal` | uses unified render output | add `surface_only=True`; use surface branch buffers | missing renderer keys | extraction smoke after mini checkpoint |
| new `utils/reflection_transport.py` | none | correspondence helpers | surface projections | not implemented | backproject/project/sample maps, confidence masks | correspondence errors | geometric identity tests |
| new `utils/texture_baking.py` | none | bake functions | UV texels | not implemented | robust specular-free material baking | UV seams/no GT | synthetic UV toy test |
| new `eval_reflective_assets.py` | none | metrics | metrics table | not implemented | Refl-NVS, Chamfer, normal MAE, leakage, relighting | dataset GT unavailable | run on exported toy data |

## New Modules to Add
- `utils/specular_mask.py`: photometric variance and residual-based reflective/specular masks.
- `utils/reflection_transport.py`: surface correspondence, reflection direction, feature sampling and visibility confidence.
- `utils/texture_baking.py`: UV projection and robust texel aggregation.
- `extract_surface_mesh.py`: surface-only mesh extraction wrapper.
- `export_pbr_textures.py`: PBR map export.
- `eval_reflective_assets.py`: metrics and CSV writer.
- `scripts/make_failure_panels.py`: visual panels for paper figures.

## Training Configuration
Potential initial config:
```text
--stage_a_until_iter 3000
--stage_b_until_iter 15000
--detach_specular_geometry_until 7000
--lambda_sep 0.02
--lambda_ref 0.01
--lambda_mat 0.01
--lambda_tex 0.01
--surface_only_mesh true
```

Needs Verification: weights are starting points only; tune on one scene with geometry/material diagnostics before full runs.

## Evaluation Scripts
Required outputs:
- `render_metrics.csv`: PSNR / SSIM / LPIPS global and reflective-region.
- `geometry_metrics.csv`: Chamfer / F-score / normal MAE / depth error global and reflective-region.
- `material_metrics.csv`: albedo error, roughness error, highlight leakage, material consistency.
- `relighting_metrics.csv`: relighting PSNR / LPIPS where GT exists.
- `failure_case_panels/`: render, normal, mesh, albedo, roughness, specular residual.

## Implementation Milestones
1. Static branch refactor with no behavior change.
2. Renderer returns separated buffers.
3. Geometry warm-up and branch freezing works on a tiny scene.
4. Add branch separation and residual sparsity.
5. Add material/transport consistency.
6. Surface-only mesh extraction.
7. Specular-free UV/PBR baking.
8. Unified evaluation and ablation runner.

## Unit Tests / Sanity Checks
- `python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py`
- tensor shape test for new branch attributes.
- save/load round-trip test with synthetic small tensors.
- renderer output-key compatibility test.
- loss finite-gradient test on synthetic tensors.
- mesh extractor import test after `utils.render_utils` repair.
- toy texture baking test on a plane with synthetic moving highlight.

## Runtime Validation Status
Needs Verification: no runtime validation was performed in this task. The plan is static and code-grounded.
