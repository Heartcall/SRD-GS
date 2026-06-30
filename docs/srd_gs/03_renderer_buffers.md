# SRD-GS Renderer Buffers

## Scope

本文件记录 Milestone 3。当前阶段扩展 `gaussian_renderer/__init__.py::render()`，在 `pc.enable_srd_gs=True` 时返回 surface/reflection 分离 buffer；默认 `enable_srd_gs=False` 时保留 Ref-GS 原有输出 key 和训练调用方式。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Modified

- `gaussian_renderer/__init__.py`
- `scene/gaussian_model.py`

`scene/gaussian_model.py` only received minimal flag storage for `srd_detach_specular_geometry` and `srd_use_branch_gate`, so the renderer can consume CLI flags already added in Milestone 2.

## Renderer Behavior

### Baseline Mode

When `pc.enable_srd_gs=False`:

- `render()` keeps the existing Ref-GS path.
- It uses `pc.get_albedo`, `pc.get_roughness`, and `pc.get_language_feature`.
- It returns existing keys including `pbr_rgb`, `rend_alpha`, `rend_normal`, `rend_dist`, `surf_depth`, `surf_normal`, `viewspace_points`, `visibility_filter`, and `radii`.

### SRD-GS Mode

When `pc.enable_srd_gs=True`:

- `render()` uses `pc.get_surface_albedo` and `pc.get_surface_roughness` for the surface branch.
- It uses `pc.get_reflection_feature` for the Ref-GS directional MLP path.
- It rasterizes `branch_gate`, `specular_weight`, and `transport_feature` as additional feature channels.
- It computes `reflection_dir` from `viewdirs` and surface normals.
- If `pc.srd_detach_specular_geometry=True`, normals and reflection directions used by the specular path are detached.
- If `pc.srd_use_branch_gate=False`, the effective branch gate is a full-one map. If it is `True`, the learned `pc.get_branch_gate` map gates specular contribution.

## SRD Output Keys

In SRD-GS mode, `render()` additionally returns:

- `surface_rgb`
- `diffuse_rgb`
- `specular_rgb`
- `roughness_map`
- `reflection_dir`
- `branch_gate_map`
- `specular_weight_map`
- `transport_feature_map`
- `reflection_residual`

Existing baseline keys remain present.

## Composition

The SRD path computes:

```text
specular_rgb = Ref-GS directional specular prediction weighted by specular_weight_map
pbr_rgb = diffuse_rgb + branch_gate_map * specular_rgb
```

Implementation detail: composition is done in the same internal color path as Ref-GS and then converted through `linear2srgb` for output.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_srd_render_contract_static
conda run -n ref_gs python -m unittest discover -s tests
conda run -n ref_gs python -m py_compile gaussian_renderer/__init__.py scene/gaussian_model.py arguments/__init__.py
```

## Tests Passed

- `tests.test_srd_render_contract_static`: passed
- full unittest discovery: passed, 12 tests
- py_compile for renderer/model/arguments: passed

## Tests Failed

None after implementation.

## Needs Runtime Verification

- Actual CUDA render with `enable_srd_gs=True`.
- Tensor shape and memory behavior for additional rasterized channels.
- Visual sanity of `surface_rgb`, `specular_rgb`, `reflection_dir`, and `transport_feature_map`.
- Interaction with `srd_reflection_dim` values different from `pc.gsfeat_dim`; `_match_feature_dim()` pads/truncates for `light_mlp`, but runtime quality remains unverified.
- Whether `srd_use_branch_gate=True` should be used from the start or only after a warmup schedule.

## Not Implemented in Milestone 3

- SRD losses.
- Stage schedule.
- Surface-only mesh extraction.
- Texture baking and PBR export.
- Real render smoke/evaluation.
