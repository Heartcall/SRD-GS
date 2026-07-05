# Ref-GS Limitation Analysis Report

Date: 2026-07-05

Repository: `/home/liuly/Surface_Reconstruction/Glossy/SRD-GS-ref`

Dataset root: `/data/liuly/dataset/3DGS`

## 1. What I Inspected

- [Paper/README] `README.md`; arXiv/HTML paper `Ref-GS: Directional Factorization for 2D Gaussian Splatting` (`arXiv:2412.00905`).
- [Code] Training entrypoints: `train.py`, `train-real.py`, `train-NeRF.py`, `train-NeRO.py`, `train.sh`.
- [Code] Configuration: `arguments/__init__.py`.
- [Code] Model and directional representation: `scene/gaussian_model.py`, especially `SphMipEncoding`, `GaussianModel`, per-Gaussian albedo/roughness/mask/feature parameters, and saved `light_mlp.pt` / `dir_encoding.pt`.
- [Code] Renderer: `gaussian_renderer/__init__.py`, especially `render`, `render_nerf`, and `render_real`.
- [Code] Data loading and cameras: `scene/__init__.py`, `scene/dataset_readers.py`, `scene/cameras.py`, `utils/camera_utils.py`.
- [Code] Losses/utilities: `utils/loss_utils.py`, `utils/color_utils.py`, `utils/point_utils.py`.
- [Code] Mesh support: `utils/mesh_utils.py`.
- [Dataset] `/data/liuly/dataset/3DGS` scanned by `dataset_inventory.py`.

## 2. Repository Understanding

[Paper/README] Ref-GS claims to use deferred Gaussian splatting, directional factorization, and a spherical Mip-grid to reduce orientation/view ambiguity, recover high-frequency view-dependent effects, and maintain accurate geometry. The paper evaluates PSNR/SSIM/LPIPS, normal MAE, ablations for deferred shading, Sph-Mip, mipmap, and directional factorization, and reports Shiny Blender, Shiny Real, Glossy Synthetic, NeRF Synthetic, and other real scenes.

[Code] The core implementation matches the claim structure at a high level:

- `GaussianModel` adds per-Gaussian albedo, roughness, mask, and a 4D learned feature vector.
- `SphMipEncoding` stores a learnable spherical feature grid and queries it via `nvdiffrast.torch.texture`.
- `render` first rasterizes albedo/roughness/features/normals/depth to buffers, computes a reflected direction from view rays and rendered normals, queries Sph-Mip with roughness as level, combines directional feature and spatial feature by an outer product, and decodes specular color with `light_mlp`.
- `render_real` adds a manual environment sphere via `env_scope_center`, `env_scope_radius`, and `xyz_axis`, then blends reflective and outside regions with `ref_w` / `out_w`.
- `train.py`, `train-NeRF.py`, and `train-NeRO.py` optimize PBR RGB against images plus normal consistency. `train-real.py` warms up with SH RGB before enabling the PBR/reflection branch after `init_until_iter`.

[Code] Important differences from a complete paper reproduction pipeline:

- There is no standalone `render.py`, `eval.py`, or mesh extraction CLI in this checkout.
- `training_report` exists but is not called in `train.py`, `train-NeRF.py`, or `train-NeRO.py`; in `train-real.py` it is explicitly commented out.
- The report function evaluates `render_pkg["render"]`, while the training objective for the reflective model uses `render_pkg["pbr_rgb"]`.
- Component buffers are written to hard-coded `result/` only every 500 iterations during render calls.
- Mesh extraction exists as a utility class, but there is no stock command to export/evaluate meshes against GT.
- `train.py` and `train-real.py` hard-code `CUDA_VISIBLE_DEVICES` internally, which can conflict with external scheduling.

## 3. Dataset Inventory Summary

[Dataset] The scanner found:

- 106 scene candidates.
- Layout counts: 30 `blender_transforms`, 68 `colmap_direct`, 2 `image_or_auxiliary`, 6 `unknown`.
- Dataset counts: DTU 15, GlossySynthetic 8, GlossySyntheticConverted 8, NeRF Synthetic 8, Shiny Blender Real 3, Shiny Blender Synthetic 6, glossy 10, llff_colmap_LDR 42, priors 6.
- 93 scenes are stock-loader compatible.
- 47 scenes have mesh or `eval_pts` style files.
- 13 scenes have depth-like files.

[Dataset] Good sanity/evaluation candidates from the real filesystem:

- `Shiny Blender Synthetic/ball`: Blender transforms, 100 train frames, 200 test frames, GT mesh files.
- `Shiny Blender Synthetic/toaster`: Blender transforms and GT mesh, suitable for geometry claim checks.
- `GlossySyntheticConverted/bell_blender`: Blender transforms, 112 train frames, 16 test frames, `eval_pts.ply`, converted format.
- `Shiny Blender Real/gardenspheres`: COLMAP layout, real-scene path used by README/train.sh commands.
- `NeRF Synthetic/materials`: Blender transforms, useful for non-reflective/material-diverse tradeoff checks.

## 4. Self-Discovered Limitations

### Limitation 1: Stock Evaluation Does Not Directly Measure the Main Reflective Output

#### Why this may be a limitation

Ref-GS trains the reflective/PBR output but the release does not provide a standalone render/eval command, and the internal evaluation helper is not wired into training. Where the helper exists, it evaluates `render_pkg["render"]`, not the `pbr_rgb` used for the reflective loss. This makes it easy to report incomplete metrics or miss component-level failures.

#### Evidence

- [Paper/README] The README says testing is via a simple notebook and says mesh extraction adopts 2DGS, but does not provide render/eval CLIs.
- [Paper/README] The paper reports PSNR/SSIM/LPIPS, normal MAE, ablations, and speed comparisons.
- [Code] `train.py` optimizes `render_pkg["pbr_rgb"]` but `training_report` evaluates `render_pkg["render"]`.
- [Code] `training_report` is not called in `train.py`; it is commented out in `train-real.py`.
- [Code] Component buffers are saved to `result/` only at iterations divisible by 500.
- [Hypothesis] A stock run can complete without producing the evidence needed to validate reflection decomposition or the paper's component-level claims.

#### What would confirm it

An experiment output contains checkpoints and perhaps visual buffers, but lacks pbr_rgb PSNR/SSIM/LPIPS, component metrics, or mesh/normal metrics unless an extra exporter/evaluator is added.

#### What would refute it

A stock command or notebook path reproducibly exports pbr_rgb, SH render, specular/diffuse/roughness/depth/normal buffers and computes the relevant metrics without additional implementation.

#### Priority

High.

### Limitation 2: Geometry Recovery May Be Sensitive to Deferred Depth/Normal Choices and TSDF Settings

#### Why this may be a limitation

The paper claims accurate geometry, and the implementation uses 2DGS-style depth/normal buffers plus a self-consistency normal loss. Mesh extraction is available only as a utility and requires depth fusion choices such as `depth_ratio`, `depth_trunc`, voxel size, and mask handling. These settings can affect geometry independently of image metrics.

#### Evidence

- [Paper/README] The paper reports normal MAE and claims faithful geometry recovery.
- [Paper/README] The README says mesh extraction follows 2DGS but gives no command.
- [Code] `render` computes `surf_depth` from expected and median depth using `pipe.depth_ratio`, then derives `surf_normal` from depth.
- [Code] Training normal loss compares rendered normals to depth-derived normals, not to GT normals.
- [Code] `GaussianExtractor.extract_mesh_bounded` uses TSDF integration with user-chosen `voxel_size`, `sdf_trunc`, `depth_trunc`, and optional mask background handling.
- [Dataset] Shiny Blender Synthetic scenes include GT mesh files; GlossySyntheticConverted scenes include `eval_pts.ply`.
- [Hypothesis] NVS quality and geometry quality may decouple under depth/TSDF setting changes.

#### What would confirm it

PSNR/SSIM/LPIPS stay close while normal MAE, Chamfer/F-score, mesh completeness, or visual geometry quality changes substantially across depth/TSDF settings.

#### What would refute it

Raw-coordinate geometry metrics remain stable across reasonable depth/TSDF sweeps and correlate with rendering metrics.

#### Priority

High.

### Limitation 3: Real-Scene Results May Depend on Hand-Specified Environment Spheres and Axis Order

#### Why this may be a limitation

The real-scene renderer separates reflective and outside regions using a manually specified sphere and axis order. `train.sh` provides scene-specific values for Shiny Real. If these values are fragile, the method may require manual tuning for real scenes rather than being robustly automatic.

#### Evidence

- [Paper/README] The paper emphasizes real-world scene performance and high-frequency reflections.
- [Code] `render_real` uses `env_scope_center`, `env_scope_radius`, and `xyz_axis` to produce `ref_w` and `out_w`.
- [Code] `train-real.py` uses `init_until_iter` to delay the reflective branch and then applies PBR/reflection losses.
- [Code] `train.sh` lists scene-specific `env_scope_center`, `env_scope_radius`, `init_until_iter`, and `xyz_axis`.
- [Dataset] Shiny Blender Real contains `gardenspheres`, `sedan`, and `toycar` with COLMAP layouts.
- [Hypothesis] Real-scene performance is sensitive to those manually supplied settings.

#### What would confirm it

Small center/radius/axis/warm-up perturbations cause large changes in `ref_w/out_w` coverage, convergence stability, or PSNR/SSIM/LPIPS.

#### What would refute it

Reasonable perturbations produce similar coverage and metrics, or there is an automatic robust setting strategy.

#### Priority

High.

### Limitation 4: Roughness-Aware Sph-Mip and Low-Rank Factorization May Be Capacity-Sensitive

#### Why this may be a limitation

The paper attributes rough-surface and near-field/inter-reflection modeling to Sph-Mip and spatial-directional outer-product factorization. The code uses a compact per-Gaussian feature vector and one spherical grid. This is efficient, but capacity or initialization may matter on scenes with diverse materials or high-frequency reflections.

#### Evidence

- [Paper/README] The paper's ablation states Sph-Mip, mipmap, deferred shading, and directional factorization are important.
- [Code] `GaussianModel` hard-codes `gsfeat_dim = 4`, `sph_dim = 16`, and one `SphMipEncoding` grid; `run_dim` controls the MLP width.
- [Code] CLI supports `run_dim`, `roughness_lr`, `encoding_lr`, `mlp_lr`, and `rand_init`, but no stock no-mipmap/no-factorization toggle.
- [Dataset] GlossySyntheticConverted provides multiple shiny object scenes with `eval_pts.ply`; NeRF Synthetic has `materials`.
- [Hypothesis] Reduced `run_dim`, roughness freezing, or different grid initialization may reveal scenes where the factorization underfits or leaks appearance between diffuse/specular components.

#### What would confirm it

Large quality/component degradation under capacity reduction or roughness freezing, especially on glossy/material-diverse scenes, with stable or smaller degradation on simpler scenes.

#### What would refute it

Metrics and component behavior are stable across reasonable capacity and roughness-learning changes.

#### Priority

Medium.

### Limitation 5: Reflection Modeling May Add Overhead or Tradeoffs on General Non-Reflective Scenes

#### Why this may be a limitation

The paper evaluates NeRF Synthetic and reflective datasets. The implementation always carries albedo, roughness, feature, Sph-Mip, and MLP parameters for Ref-GS variants. On scenes where strong view-dependent effects are not central, those parameters may add cost or introduce avoidable component ambiguity.

#### Evidence

- [Paper/README] The paper includes NeRF Synthetic evaluation and reports speed relative to 3DGS.
- [Code] `GaussianModel.training_setup` always optimizes albedo, roughness, mask, feature, `light_mlp`, and `dir_encoding`.
- [Code] `train-NeRF.py` has optional `--gsrgb_loss`, implying a need to preserve direct GS RGB behavior for NeRF Synthetic.
- [Dataset] `NeRF Synthetic/materials`, `lego`, `chair`, and other scenes exist locally.
- [Hypothesis] Reflection-specific capacity may be unnecessary or harmful for some non-reflective/general scenes.

#### What would confirm it

Higher time/memory or no quality gain relative to direct RGB/baseline settings on non-reflective scenes.

#### What would refute it

The Ref-GS branch consistently improves or preserves quality with acceptable overhead on general scenes.

#### Priority

Medium.

## 5. Experiment Matrix

The current generated matrix is also saved to `experiment_matrix.md`, `experiment_matrix.json`, and `experiment_matrix.csv`.

| ID | Limitation | Dataset/Scene | Compared Settings | Metrics | Commands | Expected Evidence |
| -- | ---------- | ------------- | ----------------- | ------- | -------- | ----------------- |
| E1 | Stock evaluation does not directly measure the main reflective output | `Shiny Blender Synthetic/ball` | stock checkpoint; helper exporter for `pbr_rgb`, `render`, normal/depth/spec/diff (requires implementation) | PSNR/SSIM/LPIPS on `pbr_rgb` and `render`; component availability; normal MAE if GT normal available | `python train.py -s '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball' --eval --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e1_dry --help` | Missing pbr/component metrics confirm release-level evaluation gap. |
| E2 | Geometry recovery sensitivity | `Shiny Blender Synthetic/toaster` | full model; `depth_ratio` sweep; TSDF `depth_trunc/voxel_size` sweep | normal MAE, Chamfer/F-score, mesh completeness, PSNR/SSIM/LPIPS | `python train.py -s '/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster' --eval --depth_ratio 0 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e2_dry --help` | Geometry metrics move more than NVS metrics under depth/TSDF changes. |
| E3 | Sph-Mip/factorization capacity sensitivity | `GlossySyntheticConverted/bell_blender` | `run_dim` 64/256; roughness freeze vs learn; no-mipmap requires implementation | PSNR/SSIM/LPIPS, roughness variance, component leakage proxy, eval_pts metric | `python train-NeRO.py -s '/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender' --eval --run_dim 64 --albedo_bias 2 --albedo_lr 0.0005 --init_until_iter 2 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e3_dry --help` | Reduced capacity or frozen roughness selectively hurts glossy/material-diverse scenes. |
| E4 | Real-scene manual environment sensitivity | `Shiny Blender Real/gardenspheres` | default train.sh setting; center/radius/axis/warm-up perturbations | PSNR/SSIM/LPIPS, `ref_w/out_w` coverage, component artifacts, convergence | `python train-real.py -s '/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres' -r 6 --eval --run_dim 256 --albedo_bias 2 --albedo_lr 0.0005 --env_scope_center -0.2270 1.9700 1.7740 --env_scope_radius 0.974 --init_until_iter 1 --xyz_axis 2.0 1.0 0.0 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e4_dry --help` | Small hand-setting perturbations change coverage or metrics. |
| E5 | General-scene overhead/tradeoff | `NeRF Synthetic/materials` | `train-NeRF.py` with `gsrgb_loss` on/off; `run_dim` 64/256; external 2DGS/3DGS baseline if available | PSNR/SSIM/LPIPS, train time, point count, GPU memory, component leakage | `python train-NeRF.py -s '/data/liuly/dataset/3DGS/NeRF Synthetic/materials' --eval --run_dim 64 --albedo_bias 0 --gsrgb_loss --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e5_dry --help` | Added reflection branch costs time/memory without clear NVS benefit. |

## 6. Implemented Files

- `README.md`
- `limitation_report.md`
- `dataset_inventory.py`
- `make_experiment_matrix.py`
- `run_small_sanity.sh`
- `collect_metrics.py`
- `visualize_outputs.py`
- `configs/.gitkeep`
- Generated: `dataset_inventory.json`, `dataset_inventory.md`, `experiment_matrix.json`, `experiment_matrix.csv`, `experiment_matrix.md`

## 7. Commands to Run Next

Dry-run and path validation:

```bash
python experiments/ref_gs_limitation_analysis/dataset_inventory.py \
  --root /data/liuly/dataset/3DGS \
  --out experiments/ref_gs_limitation_analysis/dataset_inventory.json

python experiments/ref_gs_limitation_analysis/make_experiment_matrix.py --dry-run

bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh
```

Optional 2-iteration sanity:

```bash
RUN_TRAIN=1 bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh
```

Metrics and visualization after experiments:

```bash
python experiments/ref_gs_limitation_analysis/collect_metrics.py \
  --roots output/ref_gs_limitation /tmp/ref_gs_limitation_sanity \
  --out experiments/ref_gs_limitation_analysis/metrics_summary.csv

python experiments/ref_gs_limitation_analysis/visualize_outputs.py \
  --input-dir result \
  --out experiments/ref_gs_limitation_analysis/output_contact_sheet.png
```

## 8. Caveats

- [Hypothesis] No full training, mesh extraction, or metric-bearing experiment has been run in this analysis pass.
- [Hypothesis] The listed limitations are experiment hypotheses unless future outputs confirm them.
- [Code] Stock code lacks first-class ablation flags for no-Sph-Mip, no-mipmap, no-deferred-shading, and no-factorization; those settings require implementation.
- [Code] Stock code lacks standalone pbr render/eval/export scripts; component and geometry claims require additional wrappers.
- [Dataset] GT geometry is available for Shiny Blender Synthetic scenes and `eval_pts` exists for GlossySyntheticConverted scenes, but accepted GT material/roughness/albedo references were not established by this scan.
- [Code] Mesh metrics need an evaluator not present in this checkout.
- [Environment] Restricted-shell `nvidia-smi` failed, but host-level `nvidia-smi` succeeded. Training decisions should use a host-visible CUDA check.
- [Environment] `run_small_sanity.sh` produced a Matplotlib cache warning because the default user config directory is not writable; this is not a Ref-GS failure.
