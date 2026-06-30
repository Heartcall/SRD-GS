# Baseline Runtime Repair

## Scope

本文件记录 Milestone 1。当前阶段只修复 Ref-GS baseline 的最小 import/runtime 阻断点，并添加静态测试；未实现 SRD-GS representation、renderer decomposition、loss、training schedule、mesh/material export 新逻辑。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Base commit: `bf843b7d9d74941a400defd55f60aaf36694dd24`
- Conda env in plan: `ref-gs`
- Verified conda env used: `ref_gs`

## What Was Checked

- Verified `utils/mesh_utils.py` imports `save_img_f32`, `save_img_u8`, `transform_poses_pca`, and `focus_point_fn` from `utils.render_utils`.
- Verified `utils/render_utils.py` was missing before this milestone.
- Added tests for baseline imports:
  - `scene.gaussian_model`
  - `gaussian_renderer`
  - `utils.loss_utils`
  - `utils.mesh_utils`
- Added a static renderer contract test for expected Ref-GS output tokens:
  - `pbr_rgb`
  - `rend_alpha`
  - `rend_normal`
  - `surf_depth`
  - `surf_normal`
  - `roughness`
  - `spec_light`
  - `diff_light`

## Reproduced Failure

Initial tests failed before repair:

```text
ModuleNotFoundError: No module named 'utils.render_utils'
```

The failure appeared in:

- `tests.test_mesh_utils_import`
- `tests.test_baseline_imports`, subtest `utils.mesh_utils`

## What Was Repaired

Added `utils/render_utils.py` with the minimum functions required by `utils/mesh_utils.py`:

- `save_img_u8(image, path)`
- `save_img_f32(image, path)`
- `focus_point_fn(poses)`
- `transform_poses_pca(poses)`

The repair does not change Ref-GS mesh extraction logic in `utils/mesh_utils.py`.

Added `.gitignore` only for Python cache hygiene:

- `__pycache__/`
- `*.py[cod]`

## Whether `utils/render_utils.py` Was Added

Yes. `utils/render_utils.py` was added.

## Tests Run

```bash
conda run -n ref_gs python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py utils/render_utils.py
conda run -n ref_gs python -m unittest tests.test_mesh_utils_import
conda run -n ref_gs python -m unittest tests.test_baseline_imports
conda run -n ref_gs python -m unittest tests.test_refgs_render_contract_static
```

## Tests Passed

- Static py_compile: passed
- `tests.test_mesh_utils_import`: passed
- `tests.test_baseline_imports`: passed
- `tests.test_refgs_render_contract_static`: passed

## Tests Failed

None after repair.

## Needs Runtime Verification

- `GaussianExtractor.reconstruction` with actual rendered views.
- `GaussianExtractor.extract_mesh_bounded` on a trained model.
- `GaussianExtractor.extract_mesh_unbounded`, especially `transform_poses_pca` compatibility for real camera poses.
- `GaussianExtractor.export_image`, especially float TIFF behavior through `save_img_f32`.
- Full renderer execution with CUDA rasterizers; Milestone 1 only verifies import and static source contract.

## Key Finding

The baseline import path was blocked by a missing helper module rather than a failure in the renderer, Gaussian model, loss utilities, or CUDA extension import. This makes Milestone 2 feasible after a baseline smoke run is scheduled.
