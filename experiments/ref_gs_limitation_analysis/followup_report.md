# Ref-GS Limitation Pipeline Follow-Up Report

Date: 2026-07-05

## What Changed

New files:

- `env_check.sh`
- `export_pbr_views.py`
- `evaluate_pbr.py`
- `evaluate_geometry.py`
- `check_env_sphere_coverage.py`
- `run_component_sanity.sh`
- `followup_report.md`

Updated files:

- `README.md`
- `limitation_report.md`
- `make_experiment_matrix.py`
- regenerated `experiment_matrix.json`
- regenerated `experiment_matrix.csv`
- regenerated `experiment_matrix.md`

Generated validation outputs:

- `sanity_logs/env_check.txt`
- `sanity_logs/component_sanity_summary.md`
- `sanity_logs/component_sanity_train.log`
- `sanity_logs/component_sanity_export.log`
- `sanity_logs/component_sanity_eval.log`
- `exports/dryrun_ball/manifest.json`
- `exports/component_sanity_ball/manifest.json`
- `exports/component_sanity_ball/views/00000_r_0/{gt,pbr_rgb,alpha,normal,depth}.png`
- `metrics/dryrun_ball_pbr_eval/*`
- `metrics/dryrun_geometry/*`
- `metrics/gardenspheres_env_coverage/*`
- `metrics/gardenspheres_env_default_coverage/*`
- `metrics/component_sanity_ball_pbr_eval/*`

## What Ran

Environment:

```bash
bash experiments/ref_gs_limitation_analysis/env_check.sh
```

Dry-run exporter:

```bash
python experiments/ref_gs_limitation_analysis/export_pbr_views.py --dry-run \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path "output/ref_gs_limitation_sanity/ball_iter2" \
  --split test \
  --max_views 1 \
  --out_dir "experiments/ref_gs_limitation_analysis/exports/dryrun_ball"
```

PBR evaluator on dry-run export:

```bash
python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/dryrun_ball \
  --out experiments/ref_gs_limitation_analysis/metrics/dryrun_ball_pbr_eval
```

Geometry dry-run:

```bash
python experiments/ref_gs_limitation_analysis/evaluate_geometry.py --dry-run \
  --pred missing_pred.ply \
  --gt "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender/eval_pts.ply" \
  --out experiments/ref_gs_limitation_analysis/metrics/dryrun_geometry
```

Environment sphere coverage:

```bash
python experiments/ref_gs_limitation_analysis/check_env_sphere_coverage.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  --center 0 0 0 \
  --radius 1.0 \
  --xyz_axis 0 1 2 \
  --out experiments/ref_gs_limitation_analysis/metrics/gardenspheres_env_coverage
```

Default component sanity:

```bash
bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
```

2-iteration component sanity:

```bash
RUN_TRAIN=1 SANITY_ITER=2 bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
```

The first 2-iteration attempt failed inside the restricted shell with `RuntimeError: No CUDA GPUs are available`. The same bounded command succeeded with host-level CUDA visibility.

## Environment Status

From `sanity_logs/env_check.txt`:

- `pwd`: `/home/liuly/Surface_Reconstruction/Glossy/SRD-GS-ref`
- git HEAD: `7d58e22730d7df665141ede1fd0b9b6cd39bf016`
- active conda env: `ref_gs`
- Python: `/home/liuly/anaconda3/envs/ref_gs/bin/python`, `Python 3.7.12`
- `nvidia-smi`: succeeded in the refreshed host-visible env check; GPUs 0, 4, and 5 were busy, GPUs 1, 2, 3, and 6 had available memory, GPU 7 was in prohibited compute mode.
- pip head includes `diff-surfel-2dgs`, `diff-surfel-rasterization`, `diff-surfel-rasterization-real`, `lpips`, `nvdiffrast`, `open3d`, `torch`, and `torchvision`

## Sanity Results

- env check: succeeded and recorded host-visible GPU status.
- export dry-run: succeeded; source exists, model path absent, no checkpoint supplied.
- PBR eval on dry-run: succeeded with `NA` metrics and no crash.
- geometry dry-run: succeeded; GT exists and pred is intentionally missing.
- env sphere coverage: succeeded. `center=0,0,0 radius=1.0` covers 0/136151 points; train.sh default covers 24546/136151 points.
- component sanity default: succeeded in dry mode.
- component sanity `RUN_TRAIN=1 SANITY_ITER=2`: succeeded with host-level CUDA. It generated `chkpnt2.pth`, exported one test view, and evaluated `pbr_rgb` vs `gt`.

The 2-iteration PBR metrics are entrypoint smoke evidence only:

- `pbr_rgb` valid views: 1/1
- MAE: 0.3772422969341278
- PSNR: 7.12458595995151
- SSIM: 0.5685837268829346
- LPIPS: 0.89443039894104

These are not quality claims because the model trained for only two iterations.

## Implemented Validation Capability

| Limitation | Previous status | New capability | Remaining gap |
| ---------- | --------------- | -------------- | ------------- |
| L1 PBR/evaluation gap | dry-run plan only | checkpoint export and PBR-vs-GT evaluator work on a 2-iteration checkpoint | stock renderer still does not return albedo/roughness/spec or `render` on the `render` path |
| L2 Geometry sensitivity | metric plan only | PLY Chamfer/F-score evaluator with safe dry-run | predicted mesh export CLI still missing |
| L3 Real-scene env sphere | plan only | point-cloud coverage and perturbation table implemented and run | needs full runs over env sphere perturbations for NVS impact |
| L4 Sph-Mip/factorization | plan only | PBR export/eval can measure outcomes after ablations | no no-Sph-Mip/no-factorization flags yet |
| L5 Non-reflective overhead | plan only | same PBR/export metrics can evaluate NeRF Synthetic checkpoints | baseline and timing harness still needed |

## Experiments Now Directly Runnable

- E1 can run after any checkpoint with `export_pbr_views.py` and `evaluate_pbr.py`.
- E2 can evaluate any predicted PLY against GT/eval point PLY with `evaluate_geometry.py`.
- E4 can run pre-training env sphere coverage with `check_env_sphere_coverage.py`.

Still requiring implementation:

- Mesh extraction CLI for E2 if no predicted PLY exists.
- Renderer-returned albedo/roughness/spec buffers for full component evaluation.
- No-Sph-Mip/no-mipmap/no-factorization/no-deferred ablation flags for E3.
- Runtime/memory/timing harness and external baseline alignment for E5.

## Next Commands

### E1 PBR Evaluation

```bash
mkdir -p experiments/ref_gs_limitation_analysis/logs
python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --eval --run_dim 256 --albedo_bias 0 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e1_ball_full \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e1_ball_full_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path output/ref_gs_limitation/e1_ball_full \
  --checkpoint output/ref_gs_limitation/e1_ball_full/chkpnt31000.pth \
  --split test --max_views 200 \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full \
  --out experiments/ref_gs_limitation_analysis/metrics/e1_ball_full_pbr_eval
```

### E2 Geometry Sensitivity

```bash
python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --eval --run_dim 256 --albedo_bias 0 --depth_ratio 0 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e2_toaster_depth0 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e2_toaster_depth0_train.log

python experiments/ref_gs_limitation_analysis/evaluate_geometry.py \
  --pred output/ref_gs_limitation/e2_toaster_depth0/mesh_iter31000.ply \
  --gt "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster/toaster_gt_mesh.ply" \
  --out experiments/ref_gs_limitation_analysis/metrics/e2_toaster_depth0_geometry \
  --num_samples 200000 \
  --thresholds 0.001 0.002 0.005 0.01
```

### E3 Sph-Mip / Factorization Ablation

```bash
python train-NeRO.py \
  -s "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender" \
  --eval --run_dim 64 --albedo_bias 2 --albedo_lr 0.0005 \
  --init_until_iter 3000 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e3_bell_rundim64 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e3_bell_rundim64_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender" \
  --model_path output/ref_gs_limitation/e3_bell_rundim64 \
  --checkpoint output/ref_gs_limitation/e3_bell_rundim64/chkpnt31000.pth \
  --split test --max_views 16 \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64 \
  --out experiments/ref_gs_limitation_analysis/metrics/e3_bell_rundim64_pbr_eval
```

### E4 Real-Scene Env Sphere Sensitivity

```bash
python experiments/ref_gs_limitation_analysis/check_env_sphere_coverage.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  --center -0.2270 1.9700 1.7740 \
  --radius 0.974 \
  --xyz_axis 2 1 0 \
  --out experiments/ref_gs_limitation_analysis/metrics/e4_garden_default_coverage

python train-real.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  -r 6 --eval --run_dim 256 --albedo_bias 2 --albedo_lr 0.0005 \
  --env_scope_center -0.2270 1.9700 1.7740 \
  --env_scope_radius 0.974 \
  --init_until_iter 700 \
  --xyz_axis 2.0 1.0 0.0 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e4_garden_default \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e4_garden_default_train.log
```

### E5 Non-Reflective Overhead

```bash
python train-NeRF.py \
  -s "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --eval --run_dim 64 --albedo_bias 0 --gsrgb_loss \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e5_materials_rundim64 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e5_materials_rundim64_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --model_path output/ref_gs_limitation/e5_materials_rundim64 \
  --checkpoint output/ref_gs_limitation/e5_materials_rundim64/chkpnt31000.pth \
  --render_func nerf \
  --split test --max_views 200 \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64 \
  --out experiments/ref_gs_limitation_analysis/metrics/e5_materials_rundim64_pbr_eval
```

## Caveats

- [Hypothesis] The limitations remain hypotheses until full training and metric comparisons are complete.
- [Code] Two-iteration sanity validates the pipeline only, not method quality.
- [Code] `render` path lacks `render`, albedo, roughness, and specular images as returned tensors; wrapper records these as missing.
- [Code] Geometry evaluation needs predicted PLY files; this pass does not implement mesh extraction.
- [Code] Sph-Mip/factorization ablations still need explicit flags.
- [Dataset] Geometry metrics depend on accepted GT mesh or point cloud.
- [Environment] The first bounded 2-iteration sanity failed in the restricted shell with `No CUDA GPUs are available`; the same command succeeded with host-level CUDA visibility.
