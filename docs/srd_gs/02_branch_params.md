# SRD-GS Branch Parameters

## Scope

本文件记录 Milestone 2。当前阶段只实现 SRD-GS 最小 branch-aware 参数和 CLI flags；默认关闭 `enable_srd_gs` 时，Ref-GS renderer 和 training path 仍读取原始 `get_albedo`、`get_roughness`、`get_language_feature` 等接口。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## CLI Flags Added

Added in `arguments/__init__.py::ModelParams`:

- `--enable_srd_gs`, default `False`
- `--srd_stage`, default `0`
- `--srd_reflection_warmup`, default `3000`
- `--srd_detach_specular_geometry`, default `False`
- `--srd_use_branch_gate`, default `False`
- `--srd_reflection_dim`, default `4`
- `--srd_transport_dim`, default `4`

These defaults are baseline-safe: no SRD renderer/loss path is forced on by Milestone 2.

## Gaussian Parameters Added

Added in `scene/gaussian_model.py::GaussianModel`:

- `_surface_albedo`
- `_surface_roughness`
- `_reflection_feature`
- `_specular_weight`
- `_branch_gate`
- `_transport_feature`

Initialization behavior:

- `_surface_albedo` copies `_albedo`.
- `_surface_roughness` copies `_roughness`.
- `_reflection_feature` uses small random initialization with scale `1e-4`.
- `_transport_feature` uses small random initialization with scale `1e-4`.
- `_specular_weight` initializes to sigmoid value `0.05`.
- `_branch_gate` initializes to sigmoid value `0.05`, interpreted as low initial reflection contribution for future renderer use.

## Accessors Added

- `get_surface_albedo`
- `get_surface_roughness`
- `get_reflection_feature`
- `get_specular_weight`
- `get_branch_gate`
- `get_transport_feature`

Baseline compatibility rule:

- `get_surface_albedo` returns `get_albedo` when `enable_srd_gs=False`.
- `get_surface_roughness` returns `get_roughness` when `enable_srd_gs=False`.

## Optimizer Groups Added

Added in `GaussianModel.training_setup()`:

- `surface_albedo`
- `surface_roughness`
- `reflection_feature`
- `specular_weight`
- `branch_gate`
- `transport_feature`

The groups reuse existing learning-rate fields:

- surface albedo: `albedo_lr`
- surface roughness: `roughness_lr`
- reflection feature: `feature_lr`
- transport feature: `feature_lr`
- specular weight: `mask_lr`
- branch gate: `mask_lr`

## PLY Save / Load Compatibility

`save_ply()` now writes the SRD attributes in addition to original Ref-GS attributes.

`load_ply()` now supports both:

- old Ref-GS PLY files without SRD attributes;
- new SRD-GS PLY files with SRD attributes.

Fallback behavior for old PLY files:

- missing `surface_albedo_*` falls back to loaded `_albedo`;
- missing `surface_roughness_*` falls back to loaded `_roughness`;
- missing `reflection_feature_*` falls back to zeros with `srd_reflection_dim`;
- missing `transport_feature_*` falls back to zeros with `srd_transport_dim`;
- missing `specular_weight_*` falls back to sigmoid value `0.05`;
- missing `branch_gate_*` falls back to sigmoid value `0.05`.

## Densification / Pruning Compatibility

The new SRD tensors are included in:

- `GaussianModel.prune_points()`
- `GaussianModel.densification_postfix()`
- `GaussianModel.densify_and_split()`
- `GaussianModel.densify_and_clone()`

This keeps SRD tensor lengths synchronized with the Gaussian count during baseline densification.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_srd_gaussian_model_static
conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py
conda run -n ref_gs python -m unittest discover -s tests
```

## Tests Passed

- `tests.test_srd_gaussian_model_static`: passed
- `py_compile` for `arguments/__init__.py` and `scene/gaussian_model.py`: passed
- full unittest discovery: passed, 8 tests

## Tests Failed

None after implementation.

## Needs Runtime Verification

- Real `GaussianModel.create_from_pcd()` with CUDA `distCUDA2`.
- New SRD PLY save/load round trip on a trained checkpoint.
- Old Ref-GS checkpoint load under the new fallback path.
- Training with densification enabled after new optimizer groups are present.
- Resume behavior through `capture()` / `restore()`; these were not expanded in Milestone 2.

## Not Implemented in Milestone 2

- Renderer separation buffers.
- SRD losses.
- Staged training logic.
- Surface-only mesh extraction.
- Texture baking or PBR material export.
