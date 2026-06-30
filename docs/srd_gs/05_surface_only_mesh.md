# SRD-GS Surface-only Mesh Extraction

## Scope

本文件记录 Milestone 5。当前阶段实现 surface-only mesh extraction 的代码路径和静态/单元测试，使 SRD-GS 可以从 `surface branch` 的 depth/alpha/normal/rgb buffer 进入 TSDF fusion。未运行真实场景的 mesh extraction，未验证 mesh 质量指标，未进入 texture/material baking。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Modified

- `gaussian_renderer/__init__.py`
- `utils/mesh_utils.py`

## Files Added

- `extract_surface_mesh.py`
- `tests/test_surface_only_mesh_contract.py`
- `docs/srd_gs/05_surface_only_mesh.md`

## Renderer Surface Aliases

Added in `gaussian_renderer/__init__.py::render()` when `pc.enable_srd_gs=True`:

- `surface_alpha`: alias of `render_alpha`
- `surface_depth`: alias of `surf_depth`
- `surface_normal`: alias of `surf_normal`

Existing SRD buffers from Milestone 3 remain available, including `surface_rgb`, `specular_rgb`, `branch_gate_map`, `roughness_map`, `reflection_dir`, `specular_weight_map`, and `transport_feature_map`.

## GaussianExtractor Interface

Modified `utils/mesh_utils.py::GaussianExtractor.__init__()`:

```python
def __init__(self, gaussians, render, pipe, bg_color=None, surface_only=True, mesh_mode="surface")
```

Supported `mesh_mode` values:

- `surface`: use SRD surface buffers for reconstruction and TSDF fusion.
- `unified`: use Ref-GS unified rendering buffers.
- `all_branch`: keep SRD rendering enabled, but use unified/all-branch reconstruction buffers as a negative ablation path.

The default is `surface_only=True` and `mesh_mode="surface"` because SRD-GS should extract geometry from the branch intended to represent surface geometry, not from view-dependent reflection residuals.

## Buffer Selection Policy

Added `utils/mesh_utils.py::GaussianExtractor._select_reconstruction_buffers(render_pkg)`.

In `surface` mode:

- RGB: `render_pkg.get('surface_rgb', render_pkg.get('render', render_pkg.get('pbr_rgb')))`
- Alpha: `render_pkg.get('surface_alpha', render_pkg.get('rend_alpha'))`
- Depth: `render_pkg.get('surface_depth', render_pkg.get('surf_depth'))`
- Normal: `render_pkg.get('surface_normal', render_pkg.get('surf_normal', render_pkg.get('rend_normal')))`
- Depth normal: `render_pkg.get('surface_normal', render_pkg.get('surf_normal'))`

In `unified` or `all_branch` mode:

- RGB: `render_pkg.get('render', render_pkg.get('pbr_rgb'))`
- Alpha: `render_pkg.get('rend_alpha')`
- Depth: `render_pkg.get('surf_depth')`
- Normal: `render_pkg.get('rend_normal')`
- Depth normal: `render_pkg.get('surf_normal')`

If required mesh buffers are missing, the extractor raises `KeyError` instead of silently producing invalid geometry.

## Surface-only TSDF Masking

Modified `utils/mesh_utils.py::GaussianExtractor.extract_mesh_bounded()`:

```python
depth = self.depthmaps[i].clone()
alpha = self.alphamaps[i]
if self.surface_only or self.mesh_mode == "surface":
    depth[(alpha < 0.5)] = 0
```

This masks low-confidence surface pixels before TSDF integration. The original dataset mask gate via `gt_alpha_mask` remains unchanged.

## Diagnostics

Modified `utils/mesh_utils.py::GaussianExtractor.clean()`, `reconstruction()`, and `export_image()` to store/export:

- `surface_depth_*.tiff`
- `surface_normal_*.png`
- `surface_alpha_*.png`
- `specular_rgb_*.png`
- `branch_gate_map_*.png`

These diagnostics are intended to check whether surface-only reconstruction excludes reflection residuals before using the resulting mesh for geometry claims.

## Extraction Script

Added `extract_surface_mesh.py`.

Important arguments:

- `--model_path`: inherited from `ModelParams`.
- `--iteration`: checkpoint iteration, default `-1`.
- `--mesh_mode`: one of `surface`, `unified`, `all_branch`.
- `--voxel_size`: TSDF voxel size.
- `--sdf_trunc`: TSDF truncation distance.
- `--depth_trunc`: maximum fused depth.
- `--output_path`: optional output mesh path.
- `--post_process`: enable connected-component filtering.
- `--cluster_to_keep`: post-process cluster threshold.
- `--export_diagnostics`: export diagnostic images.

Mode behavior:

- `surface`: sets `dataset.enable_srd_gs=True`, uses `surface_only=True`, and writes `mesh_surface_iter*.ply` by default.
- `unified`: keeps default unified mesh behavior through the new script.
- `all_branch`: sets `dataset.enable_srd_gs=True` but uses unified/all-branch buffers, serving as a negative ablation against surface-only extraction.

The script raises `RuntimeError` if the extracted mesh has zero vertices.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_surface_only_mesh_contract
conda run -n ref_gs python -m py_compile utils/mesh_utils.py gaussian_renderer/__init__.py extract_surface_mesh.py
conda run -n ref_gs python -m unittest discover -s tests
```

## Tests Passed

- `tests.test_surface_only_mesh_contract`: passed
- full unittest discovery: passed, 25 tests
- py_compile for changed mesh/renderer/script files: passed

## Tests Failed

None after implementation.

## Needs Runtime Verification

- Real `extract_surface_mesh.py` run on a trained SRD-GS checkpoint.
- Non-empty mesh validation on `surface`, `unified`, and `all_branch` modes.
- Diagnostic image inspection for `surface_depth`, `surface_normal`, `surface_alpha`, `specular_rgb`, and `branch_gate_map`.
- Whether `surface` mode reduces floating Gaussians or reflective-region mesh artifacts compared with `all_branch`.
- Whether `depth_trunc`, `voxel_size`, and `sdf_trunc` need scene-specific values for Ref-NeRF/Glossy objects.

## Not Implemented in Milestone 5

- Texture baking.
- PBR material export.
- Mesh/normal/Chamfer quantitative evaluation.
- Reflective-region mask protocol.
- Runtime extraction on actual checkpoints.
- Any scientific claim that SRD-GS improves mesh quality.
