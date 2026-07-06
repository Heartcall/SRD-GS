# Ref-GS Limitation Pipeline Follow-Up Report Round3

Date: 2026-07-06

## 1. What changed

Modified core code:

- `gaussian_renderer/__init__.py`

Modified experiment helpers:

- `experiments/ref_gs_limitation_analysis/export_pbr_views.py`
- `experiments/ref_gs_limitation_analysis/evaluate_pbr.py`
- `experiments/ref_gs_limitation_analysis/evaluate_geometry.py`
- `experiments/ref_gs_limitation_analysis/run_component_sanity.sh`
- `experiments/ref_gs_limitation_analysis/make_experiment_matrix.py`
- regenerated `experiment_matrix.{json,csv,md}`
- `experiments/ref_gs_limitation_analysis/README.md`

New files:

- `experiments/ref_gs_limitation_analysis/export_mesh.py`
- `experiments/ref_gs_limitation_analysis/run_timing_probe.sh`
- `experiments/ref_gs_limitation_analysis/ablation_implementation_notes.md`
- `experiments/ref_gs_limitation_analysis/test_round3_pipeline.py`
- round3 dry-run artifacts under `exports/`, `metrics/`, `meshes/`, and `sanity_logs/`

## 2. Renderer/component export changes

Changed renderer functions:

- `render(..., return_components=False)`
- `render_nerf(..., return_components=False)`
- `render_real(..., return_components=False)`

Default training behavior is unchanged because all existing training calls omit
`return_components`, so the default remains `False`.

Additional keys when `return_components=True`:

- `render`
- `diffuse`
- `specular`
- `spec`
- `albedo`
- `roughness`
- `features`

Existing keys remain unchanged:

- `pbr_rgb`
- `rend_alpha`
- `rend_normal`
- `rend_dist`
- `surf_depth`
- `surf_normal`
- `viewspace_points`
- `visibility_filter`
- `radii`
- `ref_w` / `out_w` for `render_real`

Known remaining component gaps:

- `ref_w` and `out_w` are real-scene components only; they are missing for `ref` and `nerf`.
- `features` is high-dimensional and should be consumed from `.npz`, not forced into RGB metrics.
- no-Sph-Mip and no-factorization are not implemented as CLI flags.

Supported component-export render functions:

- `ref`: synthetic Ref-GS path.
- `nerf`: `train-NeRF.py` path.
- `real`: real-scene env-sphere path with `ref_w/out_w`.
- `auto`: resolves by source path.

## 3. What I ran

All commands below were run from `/home/liuly/Surface_Reconstruction/Glossy/SRD-GS-ref`.

```bash
bash experiments/ref_gs_limitation_analysis/env_check.sh
# exit 0
```

`experiments/ref_gs_limitation_analysis/sanity_logs/env_check_round3.txt`
was also regenerated with the requested `pwd`, `git status --short`,
`git rev-parse HEAD`, conda, Python, `nvidia-smi`, and `pip list | head -100`
checks. The wrapper command exited 0 and recorded per-command failures inline.

```bash
python -m unittest experiments.ref_gs_limitation_analysis.test_round3_pipeline
# exit 0
```

```bash
python -m py_compile \
  experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  experiments/ref_gs_limitation_analysis/evaluate_geometry.py \
  experiments/ref_gs_limitation_analysis/check_env_sphere_coverage.py \
  experiments/ref_gs_limitation_analysis/export_mesh.py
# exit 0
```

```bash
python -m py_compile gaussian_renderer/__init__.py
# exit 0
```

```bash
bash -n \
  experiments/ref_gs_limitation_analysis/run_timing_probe.sh \
  experiments/ref_gs_limitation_analysis/run_component_sanity.sh \
  experiments/ref_gs_limitation_analysis/env_check.sh
# exit 0
```

```bash
python experiments/ref_gs_limitation_analysis/export_pbr_views.py --dry-run \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path "output/ref_gs_limitation_sanity/ball_iter2" \
  --checkpoint "output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth" \
  --split test \
  --max_views 1 \
  --return_components \
  --render_func ref \
  --out_dir "experiments/ref_gs_limitation_analysis/exports/round3_dryrun_ball_components"
# exit 0
```

```bash
test -f output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth
# exit 1
```

The real 1-view component export and real PBR eval were not run because the
checkpoint file does not exist in the current workspace.

```bash
python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/round3_dryrun_ball_components \
  --out experiments/ref_gs_limitation_analysis/metrics/round3_dryrun_ball_pbr_eval \
  --skip-lpips
# exit 0
```

```bash
python experiments/ref_gs_limitation_analysis/export_mesh.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --model_path "output/ref_gs_limitation_sanity/toaster_iter2" \
  --checkpoint "output/ref_gs_limitation_sanity/toaster_iter2/chkpnt2.pth" \
  --split test \
  --max_views 3 \
  --depth_ratio 1.0 \
  --out_mesh experiments/ref_gs_limitation_analysis/meshes/toaster_sanity/mesh.ply \
  --dry-run
# exit 0
```

```bash
bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh \
  --script train-NeRF.py \
  --scene "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --model output/ref_gs_limitation_timing/materials_iter10 \
  --iterations 10 \
  --dry-run
# exit 0
```

```bash
bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
# exit 0
```

## 4. Smoke results

- env check: exit 0. `conda activate ref_gs` succeeded. `nvidia-smi` failed in the restricted shell with exit 9 and the failure text is recorded in `sanity_logs/env_check_round3.txt`.
- syntax check: exit 0 for Python scripts and shell scripts.
- component export dry-run: exit 0. Source exists, model path exists, checkpoint does not exist.
- component export real smoke: not run; `output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth` is absent.
- exported keys from round3 dry-run: none, because dry-run does not load model/render.
- missing keys from round3 dry-run: `gt`, `pbr_rgb`, `render`, `diffuse`, `specular`, `spec`, `albedo`, `roughness`, `normal`, `depth`, `alpha`, `ref_w`, `out_w`, `features`.
- PBR eval on dry-run manifest: exit 0 with `NA` metrics.
- render-vs-pbr gap: `NA`; reason is no valid RGB views in dry-run output.
- mesh export dry-run: exit 0; wrote `meshes/toaster_sanity/mesh_manifest.json` with `status=dry_run`.
- timing dry-run: exit 0; wrote `metrics/timing_probe/timing_summary.{json,md}` with no training launched.
- generalized sanity default: exit 0; default mode skipped training, dry-ran export/eval, and wrote `sanity_logs/component_sanity_round3_summary.md`.

## 5. Updated validation status

| Limitation | Previous status | Round3 status | Remaining gap |
| ---------- | --------------- | ------------- | ------------- |
| L1 PBR/component evaluation | `pbr_rgb` export/eval only; `render` and components mostly missing | Renderer supports optional component returns; exporter/evaluator support `render` vs `pbr_rgb` and per-buffer manifest | Needs a current checkpoint to run real component smoke in this workspace |
| L2 Geometry sensitivity | evaluator existed but no mesh export entry | `export_mesh.py` wraps `GaussianExtractor` and TSDF with safe dry-run; evaluator writes Chamfer-L1/L2, F-score, and pair summary | Needs checkpoint plus accepted GT mesh/eval points for real geometry metrics |
| L3 Real-scene env sensitivity | env sphere coverage checker existed | `render_real` component export can expose `ref_w/out_w`; generalized runner supports `train-real.py` | Needs full real-scene perturbation runs; no new training run was launched |
| L4 Sph-Mip/factorization ablation | no no-Sph-Mip/no-factorization flag | documented config-only ablations and implementation points in `ablation_implementation_notes.md` | no-Sph-Mip and no-factorization still require code implementation |
| L5 Non-reflective overhead | no timing/memory harness | `run_timing_probe.sh` records command, wall time, best-effort GPU memory, checkpoint size, log path, exit code | Needs short or full controlled runs and baseline alignment |

## 6. Commands for next full experiments

### E1 full PBR/component evaluation

Scene: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`

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
  --return_components --render_func ref \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e1_ball_full_pbr_eval
```

Implementation needed: no.

### E2 geometry sensitivity sweep

Scene: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster`

```bash
mkdir -p experiments/ref_gs_limitation_analysis/logs

python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --eval --run_dim 256 --albedo_bias 0 --depth_ratio 0 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e2_toaster_depth0 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e2_toaster_depth0_train.log

python experiments/ref_gs_limitation_analysis/export_mesh.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --model_path output/ref_gs_limitation/e2_toaster_depth0 \
  --checkpoint output/ref_gs_limitation/e2_toaster_depth0/chkpnt31000.pth \
  --split test --max_views 200 \
  --depth_ratio 0 \
  --voxel_size 0.004 \
  --sdf_trunc 0.02 \
  --out_mesh experiments/ref_gs_limitation_analysis/meshes/e2_toaster_depth0/mesh.ply

python experiments/ref_gs_limitation_analysis/evaluate_geometry.py \
  --pred experiments/ref_gs_limitation_analysis/meshes/e2_toaster_depth0/mesh.ply \
  --gt "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster/toaster_gt_mesh.ply" \
  --out experiments/ref_gs_limitation_analysis/metrics/e2_toaster_depth0_geometry \
  --num_samples 200000 \
  --thresholds 0.001 0.002 0.005 0.01
```

Implementation needed: no, assuming GT path exists or is replaced by an accepted `eval_pts.ply`.

### E3 capacity/factorization ablation

Scene: `/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender`

```bash
mkdir -p experiments/ref_gs_limitation_analysis/logs

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
  --split test --max_views 64 \
  --return_components --render_func ref \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e3_bell_rundim64_pbr_eval
```

Implementation needed: no for reduced capacity; yes for no-Sph-Mip and no-factorization.

### E4 real-scene env sphere sensitivity

Scene: `/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres`

```bash
mkdir -p experiments/ref_gs_limitation_analysis/logs

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

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  --model_path output/ref_gs_limitation/e4_garden_default \
  --checkpoint output/ref_gs_limitation/e4_garden_default/chkpnt31000.pth \
  --split test --max_views 100 \
  --return_components --render_func real \
  --env_scope_center -0.2270 1.9700 1.7740 \
  --env_scope_radius 0.974 \
  --xyz_axis 2.0 1.0 0.0 \
  --init_until_iter 700 \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e4_garden_default_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e4_garden_default_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e4_garden_default_pbr_eval
```

Implementation needed: no for default/perturbation runs; yes only if adding new env-sphere ablation flags.

### E5 non-reflective timing/quality tradeoff

Scene: `/data/liuly/dataset/3DGS/NeRF Synthetic/materials`

```bash
mkdir -p experiments/ref_gs_limitation_analysis/logs

bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh \
  --script train-NeRF.py \
  --scene "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --model output/ref_gs_limitation/e5_materials_rundim64 \
  --iterations 31000 \
  --extra --run_dim --extra 64 --extra --albedo_bias --extra 0 --extra --gsrgb_loss

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --model_path output/ref_gs_limitation/e5_materials_rundim64 \
  --checkpoint output/ref_gs_limitation/e5_materials_rundim64/chkpnt31000.pth \
  --render_func nerf \
  --split test --max_views 200 \
  --return_components \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e5_materials_rundim64_pbr_eval
```

Implementation needed: no for Ref-GS timing; yes for external 2DGS/3DGS baseline alignment if not already available.

## 7. Caveats

- 2-iteration smoke metrics do not represent rendering or geometry quality.
- No full training was run in round3.
- The current `ball_iter2` checkpoint file is absent, so real component export smoke was not run.
- Mesh GT and material GT are scene-dependent; replace command GT paths with accepted protocol GT before making claims.
- External baselines are not aligned by this round.
- no-Sph-Mip and no-factorization still require implementation.
- Component buffers missing from a render function are reported as missing in manifest/eval output, not inferred.
- Renderer changes are default-off through `return_components=False`, so default training behavior is intended to remain unchanged.
