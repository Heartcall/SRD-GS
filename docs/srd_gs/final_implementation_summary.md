# SRD-GS Final Implementation Summary

## Scope

本文件总结当前分支 `srd-gs-dev` 已完成的 SRD-GS 工程落地状态。当前目标是把 `SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping` 在 Ref-GS/SRD-GS 代码仓库中打通为可运行、可测试、可继续扩展的实验管线。

当前结论必须按证据边界解读：

- Engineering pipeline: GO for one-scene 20-iteration smoke.
- Paper-scale quality claim: NO-GO.
- Stable mesh/material improvement claim: NO-GO.

## Implemented Code

### Baseline Runtime Repair

- `utils/render_utils.py` was added to satisfy `utils/mesh_utils.py` imports.
- `save_img_u8()` supports RGB, grayscale, tensor, and numpy image export paths used by mesh and texture scripts.
- Import/runtime tests cover the repaired baseline modules.

### SRD-GS Representation

- `arguments/__init__.py` adds baseline-safe SRD-GS CLI flags.
- `scene/gaussian_model.py` adds SRD branch tensors and optimizer groups for:
  - surface diffuse/material fields;
  - reflection/specular fields;
  - branch gating and transport features.
- PLY save/load and densification/pruning plumbing were extended with backward-compatible defaults.

### Renderer Buffers

- `gaussian_renderer/__init__.py::render()` exposes SRD buffers when `enable_srd_gs=True`:
  - `surface_rgb`
  - `diffuse_rgb`
  - `specular_rgb`
  - `roughness_map`
  - `reflection_dir`
  - `branch_gate_map`
  - `specular_weight_map`
  - `transport_feature_map`
  - `reflection_residual`
  - `surface_depth`
  - `surface_normal`
  - `surface_alpha`
- SRD extra branch maps now use base-width chunked feature raster passes for the installed fixed-width CUDA rasterizer. The fallback config remains available for comparison.

### Losses and Staged Training

- `utils/loss_utils.py` implements SRD losses for branch separation, material consistency, reflection transport consistency, and geometry-related constraints.
- `train.py` adds Stage A/B/C schedule helpers and integrates SRD losses behind `enable_srd_gs`.
- The SRD training path remains gated so the baseline Ref-GS path is preserved.

### Mesh Extraction

- `utils/mesh_utils.py::GaussianExtractor` supports `surface`, `unified`, and `all_branch` mesh modes.
- `extract_surface_mesh.py` adds a CLI for surface-only mesh extraction.
- `surface` mode uses surface depth/normal/alpha buffers and masks low-alpha regions before bounded TSDF fusion.

### Texture / Material Export

- `utils/texture_baking.py` implements image-space material baking with `specular_free` and `direct_rgb` modes.
- `export_pbr_textures.py` exports:
  - `albedo.png`
  - `roughness.png`
  - `normal.png`
  - `specular_weight.png`
  - `highlight_leakage_mask.png`
  - `baking_report.json`
- UV atlas baking and mesh-vertex material baking are not implemented yet.

### Evaluation and Ablations

- `utils/metric_utils.py` implements blocked-safe metric records with explicit unavailable reasons.
- `eval_reflective_assets.py` writes `metrics.json`, `metrics.csv`, qualitative-panel directories, and failure-case directories.
- `configs/srd_gs/*.yaml` defines baseline, full SRD-GS, and ablation variants.
- `scripts/srd_gs/run_one_scene.sh` and `scripts/srd_gs/run_ablation_one_scene.sh` default to dry-run.
- `scripts/srd_gs/collect_results.py`, `make_tables.py`, and `make_failure_panels.py` aggregate available results.
- `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` generates a bounded branch-raster smoke chain with `eval=True`, test-split render-pair export, and accepted-GT mesh evaluation.
- `scripts/srd_gs/run_single_scene_comparison.sh` runs a bounded one-scene comparison across `refgs_baseline`, `full_srd_gs`, and `full_srd_gs_branch_raster`.

## Runtime Smoke Evidence

Milestone 9 ran a bounded engineering smoke:

- Dataset: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
- Variants: `refgs_baseline`, `full_srd_gs`
- Iterations: `20`
- Output root: `outputs/srd_gs_smoke`

Key artifacts:

- `outputs/srd_gs_smoke/ball/smoke_report.md`
- `outputs/srd_gs_smoke/ball/eval/metrics_summary.csv`
- `outputs/srd_gs_smoke/results/ball/refgs_baseline/mesh_unified.ply`
- `outputs/srd_gs_smoke/results/ball/full_srd_gs/mesh_surface.ply`
- `outputs/srd_gs_smoke/results/ball/refgs_baseline/pbr_textures_direct_rgb/baking_report.json`
- `outputs/srd_gs_smoke/results/ball/full_srd_gs/pbr_textures_specular_free/baking_report.json`

Interpretation:

- The smoke verifies that train -> mesh -> texture/material export -> eval scripting can execute on one scene.
- The smoke does not verify paper-scale rendering, geometry, material, or relighting quality.
- Highlight leakage is available only as an export-path diagnostic in the smoke.

## Paper-scale Expansion Package

Milestone 10 generated a dry-run paper-scale package instead of launching broad training:

- `outputs/srd_gs_experiments/experiment_summary.md`
- `outputs/srd_gs_experiments/tables/paper_scale_dry_run_matrix.csv`
- `outputs/srd_gs_experiments/tables/smoke_metrics_summary.csv`
- `outputs/srd_gs_experiments/metrics/smoke_metrics_summary.csv`
- `outputs/srd_gs_experiments/figures/smoke_highlight_leakage.png`
- `outputs/srd_gs_experiments/failure_cases/claim_gate_status.png`
- `outputs/srd_gs_experiments/raw_logs/paper_scale_gate.txt`

The package answers the seven Milestone 10 questions with explicit NO-GO / Needs Verification status where metrics are missing.

## Claim Gate

Current supported claim:

```text
SRD-GS has an implemented and tested engineering path for surface/reflection branch parameters, renderer buffers, SRD losses, surface-only mesh extraction, image-space specular-free material export, blocked-safe evaluation, ablation configuration, and a one-scene smoke loop.
SRD-GS branch/specular/transport maps can run through the installed fixed-width CUDA rasterizer by using base-width chunked feature passes; this reached a bounded 10-iteration `ball` smoke with test-split render pairs and accepted-GT mesh metrics.
The three-variant `ball` comparison at 30 iterations runs end-to-end and records baseline, fallback SRD-GS, and branch-raster SRD-GS metrics in one summary table.
Opt-in branch-gate delay/ramp scheduling is implemented and verified through the same train/render/export/eval chain.
Render-gate delay decouples diagnostic branch-gate rasterization from rendered specular modulation and is verified on a bounded 30-iteration `ball` run.
```

Current unsupported claims:

```text
SRD-GS improves reflective-region normal MAE.
SRD-GS improves reflective-region mesh Chamfer / F-score.
SRD-GS preserves Ref-GS rendering PSNR/SSIM/LPIPS at paper scale.
SRD-GS improves relighting or PBR material accuracy.
SRD-GS has stable multi-scene mesh/material superiority.
```

## Critical Blockers Before Paper Claims

1. Test-split render/GT export requires checkpoints trained or regenerated with `eval=True`; the M16-M18 bounded runs satisfy this on `ball`, while older smoke metric-chain outputs may not.
2. Accepted GT mesh geometry is now available for Shiny Blender Synthetic `ball` through `ball_gt_mesh.ply`, and the metric chain runs against it. The current accepted-GT metrics are still single-scene short-budget evidence, not paper-scale evidence.
3. SRD branch-map rasterization now has an explicit feature-flagged chunked raster path and bounded `ball` smoke evidence. It still needs a longer single-scene run and multi-scene validation before paper-scale claims.
4. Current texture/material baking is image-space only; UV atlas or mesh-bound material baking is not implemented.
5. Ablation configs exist, but paper-scale ablation runs have not been executed.
6. The current comparison evidence is still one scene and a short 30-iteration budget.
7. The tested branch-gate ramp did not improve the immediate branch-raster tradeoff at 30 iterations.
8. Render-gate delay improves PSNR/Refl-PSNR and Chamfer over M16/M17 branch-raster variants at 30 iterations, but F-score remains zero and normal MAE is not improved.

## Recommended Next Engineering Tasks

1. Regenerate one-scene Ref-GS and SRD-GS checkpoints with `eval=True` before test-split render metrics are used.
2. Expand the accepted GT mesh protocol scene-by-scene; keep raw-coordinate metrics primary and reject generated `points3d.ply` by default.
3. Run the render-gate delay control at a longer single-scene budget where Stage B/C losses activate.
4. Re-run the same single-scene comparison after the longer run before expanding to multiple scenes.
5. Only after the validation gates pass, launch multi-scene ablations from `configs/srd_gs/*.yaml`.

## Verification Status

Fresh verification through Milestone 18:

- `conda run -n ref_gs python -m unittest tests.test_srd_branch_raster_features tests.test_srd_gaussian_model_static tests.test_srd_branch_map_fallback_policy tests.test_srd_render_contract_static`: passed, 16 tests.
- `conda run -n ref_gs python -m unittest tests.test_ablation_system_contract`: passed, 3 tests.
- `scripts/srd_gs/run_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster.yaml --source_path /tmp/srd_dummy_scene --output_root /tmp/srd_branch_raster_dryrun --scene_name dummy --iterations 10`: passed as dry-run.
- `python -m unittest tests.test_branch_raster_smoke_runner`: passed, 1 test.
- `conda run -n ref_gs python -m unittest tests.test_render_eval_pairs_static tests.test_srd_branch_raster_features tests.test_srd_render_contract_static`: passed, 12 tests.
- `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_branch_raster_smoke_m15_depth10 --scene_name ball --iterations 10 --max_mesh_views 4 --depth_trunc 10.0 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_single_scene_comparison_runner tests.test_ablation_system_contract`: passed, 4 tests.
- `bash scripts/srd_gs/run_single_scene_comparison.sh --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_single_scene_comparison_m16_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_srd_branch_gate_schedule tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 9 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_branch_gate_ramp_m17_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_srd_branch_gate_schedule tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 12 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_render_gate_delay_m18_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
