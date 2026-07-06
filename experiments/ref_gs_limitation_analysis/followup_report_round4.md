# Ref-GS Limitation Pipeline Follow-Up Report Round4

Date: 2026-07-06

## 1. What changed

Modified files:

- `experiments/ref_gs_limitation_analysis/README.md`
- `experiments/ref_gs_limitation_analysis/export_mesh.py`
- `experiments/ref_gs_limitation_analysis/run_component_sanity.sh`
- `experiments/ref_gs_limitation_analysis/run_timing_probe.sh`
- `experiments/ref_gs_limitation_analysis/test_round3_pipeline.py`

Generated round4 artifacts:

- `output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth`
- `experiments/ref_gs_limitation_analysis/sanity_logs/component_sanity_round4_train.log`
- `experiments/ref_gs_limitation_analysis/sanity_logs/component_sanity_round4_train_summary.md`
- `experiments/ref_gs_limitation_analysis/exports/round4_ball_components/manifest.json`
- `experiments/ref_gs_limitation_analysis/metrics/round4_ball_pbr_eval/`
- `experiments/ref_gs_limitation_analysis/meshes/round4_ball_sanity/mesh_manifest.json`
- `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary.json`
- `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round4_dryrun.json`

Strict/audit changes:

- `export_mesh.py --strict` returns nonzero when non-dry-run mesh export status is not `ok`.
- `run_timing_probe.sh --strict` returns nonzero when the underlying non-dry-run training command fails.
- `run_component_sanity.sh` supports `STRICT=1` and `ROUND_NAME=...`.
- timing summaries now include `peak_gpu_memory_reason`.

## 2. What I verified

- checkpoint existed before round4: no.
- reran 2-iteration training: yes. Restricted-shell attempt failed with `No CUDA GPUs are available`; host-visible rerun completed with `train_exit=0`.
- checkpoint after training: `output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth`, size about 102M.
- real component export: yes, after a restricted-shell CUDA failure, the host-visible run completed and wrote `exports/round4_ball_components/manifest.json`.
- real PBR/component eval: yes, wrote `metrics/round4_ball_pbr_eval/{per_view_metrics.csv,summary_metrics.json,summary_metrics.md,missing_buffers.md}`.
- real mesh export: attempted twice. Both restricted and host-visible attempts wrote `status=NA` with the same `GLIBCXX_3.4.29` runtime-library reason.
- timing dry-run: yes, saved as `metrics/timing_probe/timing_summary_round4_dryrun.json`.
- timing short-run: yes, 2 iterations, host-visible run completed with `exit_code=0`.
- strict mode: added and covered by unit tests.

## 3. Component export result

Manifest: `experiments/ref_gs_limitation_analysis/exports/round4_ball_components/manifest.json`

- dry_run: `false`
- errors: `[]`
- exported_keys: `albedo`, `alpha`, `depth`, `diffuse`, `features`, `gt`, `normal`, `pbr_rgb`, `render`, `roughness`, `spec`, `specular`
- missing_keys: `out_w`, `ref_w`
- render exists: yes
- pbr_rgb exists: yes
- diffuse/specular/albedo/roughness exist: yes
- features saved as npz: yes, `views/00000_r_0/features.npz`

Per-buffer summary for `r_0`:

| Buffer | Exported | Shape | Dtype | Min | Max |
| --- | --- | --- | --- | --- | --- |
| gt | yes | `[3, 800, 800]` | `torch.float32` | 0.05882352963089943 | 1.0 |
| pbr_rgb | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.6799494624137878 |
| render | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.41602808237075806 |
| diffuse | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.445560097694397 |
| specular | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.5399485230445862 |
| spec | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.5399485230445862 |
| albedo | yes | `[3, 800, 800]` | `torch.float32` | 0.0 | 0.16706643998622894 |
| roughness | yes | `[1, 800, 800]` | `torch.float32` | 0.0 | 0.4176660478115082 |
| normal | yes | `[3, 800, 800]` | `torch.float32` | -0.9969955682754517 | 0.9999973177909851 |
| depth | yes | `[1, 800, 800]` | `torch.float32` | 0.0 | 4.65906286239624 |
| alpha | yes | `[1, 800, 800]` | `torch.float32` | 0.0 | 0.835331916809082 |
| features | yes | `[4, 800, 800]` | `torch.float32` | 0.0 | 0.0 |
| ref_w | no | `NA` | `NA` | `NA` | `NA` |
| out_w | no | `NA` | `NA` | `NA` | `NA` |

`ref_w/out_w` are missing because this was the synthetic `render_func=ref` path, not `render_real`.

## 4. PBR eval result

Summary: `experiments/ref_gs_limitation_analysis/metrics/round4_ball_pbr_eval/summary_metrics.json`

| Target | Valid views | MAE | PSNR | SSIM | LPIPS |
| --- | --- | --- | --- | --- | --- |
| pbr_rgb | 1/1 | 0.37779131531715393 | 7.108479502505233 | 0.5674270987510681 | 0.8868467807769775 |
| render | 1/1 | 0.5785410404205322 | 3.3492402341375938 | 0.2216537743806839 | 0.9651843309402466 |
| diffuse | 1/1 | 0.49912571907043457 | 4.358250078533302 | 0.3276011645793915 | 0.9636480212211609 |
| specular | 1/1 | 0.37866657972335815 | 6.945894469603633 | 0.6260547041893005 | 0.8189250826835632 |
| spec | 1/1 | 0.37866657972335815 | 6.945894469603633 | 0.6260547041893005 | 0.8189250826835632 |
| albedo | 1/1 | 0.6693639159202576 | 2.5404830373553726 | 0.18325059115886688 | 0.930651068687439 |

`pbr_rgb_vs_render_gap`:

- status: `ok`
- `pbr_rgb_psnr - render_psnr`: 3.759239268367639
- `pbr_rgb_mae - render_mae`: -0.2007497251033783
- `pbr_rgb_lpips - render_lpips`: -0.07833755016326904

NA values:

- `ref_w` and `out_w` are listed in `missing_buffers.md`, reason: not returned by renderer.

These are 2-iteration smoke metrics only and are not quality evidence.

## 5. Mesh result

Manifest: `experiments/ref_gs_limitation_analysis/meshes/round4_ball_sanity/mesh_manifest.json`

- dry_run: `false`
- status: `NA`
- mesh_exists: absent from manifest, and no mesh success was reported
- num_vertices: absent from manifest
- num_triangles: absent from manifest
- points_exists: absent from manifest
- reason: `/lib/x86_64-linux-gnu/libstdc++.so.6: version GLIBCXX_3.4.29 not found (required by .../libLerc.so.4)`

Interpretation: this was a real mesh export attempt, not dry-run, but it failed before TSDF export due to a runtime-library incompatibility. L2 mesh export is not closed yet.

## 6. Timing result

Dry-run summary:

- path: `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round4_dryrun.json`
- dry_run: `true`
- exit_code: `0`
- peak_gpu_memory_mb: `NA`
- peak_gpu_memory_reason: `dry_run`

Real short-run summary:

- path: `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary.json`
- script: `train-NeRF.py`
- scene: `/data/liuly/dataset/3DGS/NeRF Synthetic/materials`
- model: `output/ref_gs_limitation_timing/materials_iter2_round4`
- iterations: `2`
- dry_run: `false`
- exit_code: `0`
- wall_clock_seconds: `15`
- peak_gpu_memory_mb: `10630`
- checkpoint_size_bytes: `106622668`
- log_path: `experiments/ref_gs_limitation_analysis/sanity_logs/timing_probe_train-NeRF_iter2.log`

## 7. Updated validation status

| Limitation | Round3 status | Round4 status | Remaining gap |
|---|---|---|---|
| L1 PBR/component evaluation | Component exporter/evaluator existed, but no real checkpoint smoke | Minimal true loop closed: 2-iter checkpoint -> component export -> PBR/component eval with `pbr_rgb_vs_render_gap.status=ok` | Full training and quality claims still absent |
| L2 geometry sensitivity | `export_mesh.py` dry-run existed | Real mesh export attempted from checkpoint and failed with logged GLIBCXX reason | Fix runtime-library/Open3D/PIL stack, then rerun mesh export and geometry eval |
| L3 real-scene env sensitivity | coverage and real renderer component path existed | No new real-scene training; synthetic `ref_w/out_w` correctly missing | Real-scene env perturbation runs still needed |
| L4 Sph-Mip/factorization ablation | notes documented config-only vs implementation-required ablations | Strict/audit plumbing improved; no ablation implementation added | no-Sph-Mip and no-factorization still require implementation |
| L5 non-reflective overhead | timing dry-run harness existed | Minimal true timing short-run closed for `train-NeRF.py`, 2 iterations, with wall time/memory/checkpoint size | Full comparable timing and external baselines still absent |

## 8. Commands for next full experiments

### E1 full PBR/component evaluation

- scene: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
- output path: `output/ref_gs_limitation/e1_ball_full`
- iterations: 31000
- log path: `experiments/ref_gs_limitation_analysis/logs/e1_ball_full_train.log`
- implementation needed: no

```bash
python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --eval --run_dim 256 --albedo_bias 0 \
  --iterations 31000 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e1_ball_full \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e1_ball_full_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path output/ref_gs_limitation/e1_ball_full \
  --checkpoint output/ref_gs_limitation/e1_ball_full/chkpnt31000.pth \
  --split test --max_views 200 \
  --return_components --render_func ref --save_npz \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e1_ball_full_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e1_ball_full_pbr_eval
```

### E2 geometry sensitivity

- scene: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster`
- output path: `output/ref_gs_limitation/e2_toaster_depth0`
- iterations: 31000
- log path: `experiments/ref_gs_limitation_analysis/logs/e2_toaster_depth0_train.log`
- implementation needed: no, but current mesh runtime-library issue must be fixed first

```bash
python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --eval --run_dim 256 --albedo_bias 0 --depth_ratio 0 \
  --iterations 31000 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e2_toaster_depth0 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e2_toaster_depth0_train.log

python experiments/ref_gs_limitation_analysis/export_mesh.py --strict \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --model_path output/ref_gs_limitation/e2_toaster_depth0 \
  --checkpoint output/ref_gs_limitation/e2_toaster_depth0/chkpnt31000.pth \
  --split test --max_views 200 \
  --depth_ratio 0 --voxel_size 0.004 --sdf_trunc 0.02 \
  --render_func ref \
  --out_mesh experiments/ref_gs_limitation_analysis/meshes/e2_toaster_depth0/mesh.ply

python experiments/ref_gs_limitation_analysis/evaluate_geometry.py \
  --pred experiments/ref_gs_limitation_analysis/meshes/e2_toaster_depth0/mesh.ply \
  --gt "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster/toaster_gt_mesh.ply" \
  --out experiments/ref_gs_limitation_analysis/metrics/e2_toaster_depth0_geometry \
  --num_samples 200000 \
  --thresholds 0.001 0.002 0.005 0.01
```

### E3 Sph-Mip / factorization ablation

- scene: `/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender`
- output path: `output/ref_gs_limitation/e3_bell_rundim64`
- iterations: 31000
- log path: `experiments/ref_gs_limitation_analysis/logs/e3_bell_rundim64_train.log`
- implementation needed: no for reduced-capacity config; yes for no-Sph-Mip/no-factorization

```bash
python train-NeRO.py \
  -s "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender" \
  --eval --run_dim 64 --albedo_bias 2 --albedo_lr 0.0005 \
  --init_until_iter 3000 \
  --iterations 31000 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e3_bell_rundim64 \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e3_bell_rundim64_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender" \
  --model_path output/ref_gs_limitation/e3_bell_rundim64 \
  --checkpoint output/ref_gs_limitation/e3_bell_rundim64/chkpnt31000.pth \
  --split test --max_views 64 \
  --return_components --render_func ref --save_npz \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e3_bell_rundim64_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e3_bell_rundim64_pbr_eval
```

### E4 real-scene env sphere sensitivity

- scene: `/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres`
- output path: `output/ref_gs_limitation/e4_garden_default`
- iterations: 31000
- log path: `experiments/ref_gs_limitation_analysis/logs/e4_garden_default_train.log`
- implementation needed: no for default env settings

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
  --iterations 31000 \
  --checkpoint_iterations 31000 \
  --model_path output/ref_gs_limitation/e4_garden_default \
  2>&1 | tee experiments/ref_gs_limitation_analysis/logs/e4_garden_default_train.log

python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  --model_path output/ref_gs_limitation/e4_garden_default \
  --checkpoint output/ref_gs_limitation/e4_garden_default/chkpnt31000.pth \
  --split test --max_views 100 \
  --return_components --render_func real --save_npz \
  --env_scope_center -0.2270 1.9700 1.7740 \
  --env_scope_radius 0.974 \
  --xyz_axis 2.0 1.0 0.0 \
  --init_until_iter 700 \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e4_garden_default_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e4_garden_default_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e4_garden_default_pbr_eval
```

### E5 non-reflective overhead

- scene: `/data/liuly/dataset/3DGS/NeRF Synthetic/materials`
- output path: `output/ref_gs_limitation/e5_materials_rundim64`
- iterations: 31000
- log path: `experiments/ref_gs_limitation_analysis/sanity_logs/timing_probe_train-NeRF_iter31000.log`
- implementation needed: no for Ref-GS timing; yes for external baseline alignment

```bash
bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh --strict \
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
  --return_components --save_npz \
  --out_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64_components

python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/e5_materials_rundim64_components \
  --out experiments/ref_gs_limitation_analysis/metrics/e5_materials_rundim64_pbr_eval
```

## 9. Caveats

- 2-iteration smoke metrics do not represent quality.
- Full training was not run.
- Material GT and mesh GT are scene/protocol dependent and were not validated here.
- External baselines are not aligned.
- no-Sph-Mip and no-factorization still require implementation.
- GPU memory can be `NA` if `nvidia-smi` is unavailable; round4 real timing did record `10630` MB.
- Mesh export did run as a real attempt but failed due to GLIBCXX/libLerc runtime-library incompatibility.
- PBR/component export/eval did run as a real checkpoint smoke and should be treated only as pipeline evidence.
