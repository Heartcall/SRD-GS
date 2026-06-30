# Milestone 15: Branch-raster Smoke Runner

Status: bounded runtime smoke GO; paper-scale and quality-superiority claims still blocked

## Goal

Milestone 14 added the feature-flagged branch-map raster feature path. Milestone 15 adds a bounded one-scene runtime entry that can verify that path without launching the broad paper-scale matrix.

## Added Runner

`scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` defaults to dry-run and writes the full command chain for:

- `train.py` with `--eval`, `--enable_srd_gs`, `--srd_rasterize_branch_maps`, and `--srd_use_branch_gate`
- `extract_surface_mesh.py` in `surface` mode
- `export_pbr_textures.py` in `specular_free` mode
- `render_eval_pairs.py` on the `test` split with reflective-mask export
- `eval_reflective_assets.py` with `--source_path` and `--pred_geometry`, so accepted scene GT meshes such as `ball_gt_mesh.ply` are discovered through the raw-coordinate protocol

The runner also sets `LD_LIBRARY_PATH` so `conda`'s `libstdc++` is used before the system library. This is required for the local `open3d -> PIL/libLerc` import path.

Default bounded command:

```bash
scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_branch_raster_smoke \
  --scene_name ball \
  --iterations 20 \
  --max_mesh_views 8 \
  --depth_trunc 10.0 \
  --max_texture_views 4 \
  --max_eval_views 2
```

Runtime command adds:

```bash
--execute
```

## Claim Boundary

## Runtime Evidence

Executed bounded smoke:

```text
output root: outputs/srd_gs_branch_raster_smoke_m15_depth10
scene: Shiny Blender Synthetic ball
variant: full_srd_gs_branch_raster
iterations: 10
mesh max views: 4
depth_trunc: 10.0
eval split: test
eval max views: 2
geometry sample count: 1000
```

Key artifacts:

- `outputs/srd_gs_branch_raster_smoke_m15_depth10/models/ball/full_srd_gs_branch_raster/point_cloud/iteration_10/point_cloud.ply`
- `outputs/srd_gs_branch_raster_smoke_m15_depth10/results/ball/full_srd_gs_branch_raster/mesh_surface.ply`
- `outputs/srd_gs_branch_raster_smoke_m15_depth10/results/ball/full_srd_gs_branch_raster/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_branch_raster_smoke_m15_depth10/results/ball/full_srd_gs_branch_raster/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_branch_raster_smoke_m15_depth10/results/ball/full_srd_gs_branch_raster/eval_with_gt_mesh/metrics.csv`

Verified branch-map policy in the refreshed render manifest:

```text
policy: raster_feature_chunks
gate_applied: true
branch_gate_map.rasterized: true
branch_gate_map.backward_to_gaussian: true
specular_weight_map.rasterized: true
transport_feature_map.rasterized: true
```

Smoke metrics:

```text
PSNR: 4.3260
SSIM: -0.2662
Refl-PSNR: 2.9511
Refl-SSIM: -0.2267
Chamfer distance: 0.482526
F-score: 0.0
Normal MAE: 87.3388
Highlight leakage score from baking report: 0.0011636
```

## Fixes From Runtime Debugging

- Initial CUDA smoke failed because the installed diff-surfel rasterizer backward returned gradients for the fixed base feature width instead of the attempted 11-channel packed input.
- `gaussian_renderer.render()` now rasterizes branch/specular/transport maps through multiple base-width feature chunks, preserving backward compatibility with the installed CUDA extension.
- Initial mesh extraction failed because the default `depth_trunc=3.0` produced an empty mesh for the scene scale; the runner now defaults to `depth_trunc=10.0`.
- Initial `open3d` import failed through system `libstdc++`; the runner now prioritizes the conda environment library path.
- `render_eval_pairs.py` now records the renderer-returned `srd_branch_map_policy`, so manifests distinguish fallback maps from the chunked raster path.

## Claim Boundary

This runner only executes a bounded engineering smoke. It does not support paper-scale quality claims by itself. Geometry metrics remain raw-coordinate primary, and no ICP or similarity alignment is introduced.

Branch-raster paper claims remain blocked until the runtime smoke confirms:

- behavior is stable beyond a 10-iteration single-scene smoke
- branch diagnostics remain non-fallback on longer checkpoints
- accepted GT mesh metrics are meaningful across more than one scene
- material metrics include actual GT material references or a stronger material-evaluation protocol
