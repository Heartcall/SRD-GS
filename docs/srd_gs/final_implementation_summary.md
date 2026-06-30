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
- Current limitation: SRD extra branch maps use fallback slicing/default behavior because the current rasterizer feature-channel backward path does not support all added channels.

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

1. Test-split render/GT export requires checkpoints trained or regenerated with `eval=True`; existing smoke metric-chain outputs used the train split because their checkpoint config had `eval=False`.
2. Accepted GT mesh geometry is now available for Shiny Blender Synthetic `ball` through `ball_gt_mesh.ply`, and the metric chain runs against it. The current accepted-GT metrics are still from 20-iteration smoke artifacts and are not paper-scale evidence.
3. SRD branch-map rasterization is currently a fallback path, not a full multi-channel rasterizer implementation.
4. Current texture/material baking is image-space only; UV atlas or mesh-bound material baking is not implemented.
5. Ablation configs exist, but paper-scale ablation runs have not been executed.
6. The current runtime smoke is only 20 iterations on one scene.

## Recommended Next Engineering Tasks

1. Regenerate one-scene Ref-GS and SRD-GS checkpoints with `eval=True` before test-split render metrics are used.
2. Expand the accepted GT mesh protocol scene-by-scene; keep raw-coordinate metrics primary and reject generated `points3d.ply` by default.
3. Decide whether to extend the rasterizer ABI for SRD extra channels or add a separate branch-map rasterization pass.
4. Run one longer single-scene experiment before expanding to the full dry-run matrix.
5. Only after the validation gates pass, launch multi-scene ablations from `configs/srd_gs/*.yaml`.

## Verification Status

Fresh verification in Milestone 13:

- `conda run -n ref_gs python -m unittest tests.test_dataset_split_and_gt_protocol tests.test_geometry_eval_utils tests.test_single_scene_validation_gate tests.test_srd_branch_map_fallback_policy`: passed, 12 tests.
- `conda run -n ref_gs python scripts/srd_gs/inspect_single_scene_validation.py --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' --eval --enable_srd_gs --output_dir outputs/srd_gs_validation/ball_gt_mesh`: passed.
- `conda run -n ref_gs python eval_reflective_assets.py ... --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' ... --output_dir outputs/srd_gs_metric_chain/ball/refgs_baseline/eval_with_gt_mesh`: passed.
- `conda run -n ref_gs python eval_reflective_assets.py ... --source_path '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' ... --output_dir outputs/srd_gs_metric_chain/ball/full_srd_gs/eval_with_gt_mesh`: passed.
