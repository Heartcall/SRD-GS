# SRD-GS Specular-free Texture / Material Baking

## Scope

本文件记录 Milestone 6。当前阶段实现 SRD-GS 的最小 specular-free image-space material baking 路径，用于导出不直接使用 final `pbr_rgb` 的 albedo/material proxy maps。未实现 UV atlas、mesh-vertex color baking、真实 checkpoint runtime 导出或材质质量评估。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Added

- `utils/texture_baking.py`
- `export_pbr_textures.py`
- `tests/test_texture_baking_weights.py`
- `docs/srd_gs/06_texture_baking.md`

## Baking Outputs

`utils/texture_baking.py::save_baking_outputs()` writes:

- `albedo.png`
- `roughness.png`
- `normal.png`
- `specular_weight.png`
- `highlight_leakage_mask.png`
- `baking_report.json`

The current output type is `image_space_material_maps`, not UV texture maps.

## Weight Design

Implemented in `utils/texture_baking.py::compute_baking_weights()`:

```text
weight =
  alpha_confidence
  * visibility_confidence
  * view_angle_weight
  * specular_residual_downweight
  * branch_gate_downweight
  * reprojection_confidence
```

Inputs:

- `alpha`: surface alpha or rendered alpha, CHW/HWC/HW tensor.
- `normal`: surface normal, CHW/HWC tensor.
- `viewdir`: optional view direction map; if missing, a front-facing proxy is used.
- `specular_rgb`: optional specular residual map.
- `branch_gate_map`: optional branch gate map.
- `visibility_confidence`: optional visibility confidence map.
- `reprojection_confidence`: optional reprojection confidence map.

Behavior:

- High `specular_rgb` lowers the baking weight.
- High `branch_gate_map` lowers the baking weight.
- Low alpha lowers the baking weight.
- Grazing/inconsistent view angle lowers the baking weight.

This is a differentiability-safe tensor implementation, but current usage is export-time `torch.no_grad()` rather than training-time optimization.

## Baking Modes

Implemented in `utils/texture_baking.py::bake_image_space_materials()`:

### `specular_free`

- Albedo source: `surface_rgb`, falling back to `diffuse_rgb`.
- It explicitly does not use final `pbr_rgb` as albedo.
- Specular residual and branch gate are used to downweight contaminated observations.

### `direct_rgb`

- Albedo source: final `pbr_rgb`, falling back to `render`.
- This mode is a baseline for comparison only.
- It is expected to retain baked highlight artifacts when final RGB contains view-dependent specular appearance.

## Export Script

Added `export_pbr_textures.py`.

Important arguments:

- `--model_path`: inherited from `ModelParams`.
- `--source_path`: inherited from `ModelParams`.
- `--iteration`: checkpoint iteration, default `-1`.
- `--split`: `train` or `test`.
- `--mode`: `specular_free` or `direct_rgb`.
- `--output_dir`: optional output directory.
- `--max_views`: optional view cap for smoke/runtime testing.

The script sets `dataset.enable_srd_gs=True`, renders the chosen camera split, runs image-space baking, saves PNG maps, and writes `baking_report.json`.

## Report Schema

Implemented in `utils/texture_baking.py::create_baking_report()`:

- `mode`
- `output_type`
- `observation_count`
- `highlight_leakage_score`
- `valid_weight_fraction`
- `outputs`
- `limitations`

`highlight_leakage_score` is a proxy based on rendered `specular_rgb * branch_gate_map * alpha`; it is not a ground-truth material metric.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_texture_baking_weights
conda run -n ref_gs python -m unittest discover -s tests
conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py utils/render_utils.py utils/texture_baking.py extract_surface_mesh.py export_pbr_textures.py
git diff --check
```

## Tests Passed

- High specular residual and branch gate lower baking weight.
- Specular-free albedo uses `surface_rgb` rather than final `pbr_rgb`.
- Output file names and report schema are correct.
- full unittest discovery: passed, 28 tests.
- py_compile for SRD-modified Python files: passed.
- `git diff --check`: passed.

## Tests Failed

Initial RED test failed because `utils.texture_baking` did not exist. No failures after implementation.

## Needs Runtime Verification

- Real `export_pbr_textures.py` run on a trained SRD-GS checkpoint.
- Visual inspection of `albedo.png`, `roughness.png`, `normal.png`, `specular_weight.png`, and `highlight_leakage_mask.png`.
- Compare `--mode specular_free` against `--mode direct_rgb` on reflective objects.
- Verify that image-space maps are sufficient for early diagnostics before implementing UV atlas or vertex baking.
- Confirm renderer memory cost when collecting many views.

## Not Implemented in Milestone 6

- UV atlas baking.
- Mesh-vertex material baking.
- Per-texel visibility-aware reprojection.
- PBR relighting export.
- Quantitative material metrics.
- Runtime export on actual checkpoints.
