# Milestone 32: Instrumented runtime i30

Status: bounded single-scene runtime GO; runtime loss/failure artifacts generated; paper-scale still blocked

## Objective

Restore/verify CUDA visibility for the `ref_gs` runtime, rerun the refined preflight, and launch exactly one single-scene 30-iteration instrumented `ball` run only after `runtime_go=true`.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: the bounded M32 preflight is GO when invoked through the host-visible `conda run -n ref_gs` runtime context.
- Allowed claim: one 30-iteration `ball` instrumented SRD-GS chain completed train, surface mesh extraction, specular-free texture export, render-eval pair generation, accepted-GT mesh evaluation, and summary collection.
- Allowed claim: runtime `loss_log.csv` and `failure_case_panels/failure_summary.md` artifacts now exist for this one short-budget run.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond this one scene, one checkpoint, and short budget.

## Implementation

- Added a preflight regression test for the case where direct env-python probing reports CUDA unavailable while a host-visible `conda run -n ref_gs` probe can see CUDA.
- Updated `scripts/srd_gs/preflight_instrumented_runtime.py` so Torch CUDA probe output is parsed defensively and direct env-python false negatives can fall back to `conda run -n ref_gs`.
- Verified the current tool context difference: plain `python` subprocess probes can still see CUDA as false, while top-level host-visible `conda run -n ref_gs` sees CUDA as true. Therefore the claim-bearing M32 preflight artifact was generated with top-level `conda run -n ref_gs python ...`.

## Commands

Focused TDD:

```bash
conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight
```

Dry-run command package:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_instrumented_runtime_m32_dryrun \
  --scene_name ball \
  --iterations 30 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000
```

Host-visible preflight:

```bash
conda run -n ref_gs python scripts/srd_gs/preflight_instrumented_runtime.py \
  --result_root outputs/srd_gs_instrumented_runtime_m32_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M32_conda_run_preflight_probe \
  --output_dir outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe \
  --training_gpu_index 2 \
  --max_gpu_utilization_percent 50 \
  --workspace_path . \
  --min_workspace_free_gb 25
```

Bounded runtime:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_instrumented_runtime_m32_i30 \
  --scene_name ball \
  --iterations 30 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000 \
  --execute
```

Summary table:

```bash
python scripts/srd_gs/collect_results.py \
  --results_root outputs/srd_gs_instrumented_runtime_m32_i30/results \
  --output_csv outputs/srd_gs_instrumented_runtime_m32_i30/tables/ball_instrumented_i30_metric_summary.csv
```

## Outputs

- `outputs/srd_gs_instrumented_runtime_m32_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/train_command.txt`
- `outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe/instrumented_runtime_preflight.csv`
- `outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe/instrumented_runtime_preflight.json`
- `outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe/instrumented_runtime_preflight.md`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/loss_log.csv`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/mesh_surface.ply`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md`
- `outputs/srd_gs_instrumented_runtime_m32_i30/tables/ball_instrumented_i30_metric_summary.csv`

## Preflight Matrix

| Label | Runtime GO | Contract ready | Torch CUDA | Torch devices | Training GPU visible | GPU util | Workspace free GB | Process matches | Blockers | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| M32 conda-run preflight probe | true | true | true | 8 | true | 0 | 29.98 | 0 | none | `workspace_storage_tight` |

## Runtime Evidence

| Metric | Value |
| --- | ---: |
| loss-log rows | 3 |
| final logged stage | `stage_a` |
| final logged total loss | 0.564937 |
| final logged photometric loss | 0.208746 |
| final logged geometry loss | 0.047309 |
| final logged surface alpha mean | 0.457094 |
| final logged Gaussian count | 100000 |
| render-eval frames | 2 |
| render branch-map policy | `raster_feature_chunks` |
| branch gate weight | 1.0 |
| render gate weight | 0.0 |

## Metrics

| Metric | Value |
| --- | ---: |
| PSNR | 4.342511 |
| SSIM | -0.298195 |
| Refl-PSNR | 2.938904 |
| Refl-SSIM | -0.245972 |
| Chamfer distance | 0.487437 |
| F-score | 0.0 |
| Normal MAE | 87.332283 |
| Texture baking highlight leakage | 0.000975 |

Unavailable metrics remain explicit in `failure_summary.md`: LPIPS/refl-LPIPS, GT depth, eval-level highlight leakage mask, GT albedo, GT roughness, material consistency, training time, peak memory, and render FPS.

## Interpretation

M32 removes the immediate runtime-evidence blocker introduced by M28-M31: the bounded runner can now produce `loss_log.csv` and eval failure-summary artifacts in a real one-scene run. The metrics are still short-budget, single-scene, and not a baseline comparison. F-score remains `0.0`, normal MAE is high, SSIM is negative, and several metrics are unavailable, so quality and paper-scale claims remain blocked.

## Failure Conditions

- If the runtime was launched before a host-visible `runtime_go=true` preflight, the milestone fails.
- If more than one scene or checkpoint was launched, the milestone fails.
- If `--enable_srd_gs=False` behavior changes, the milestone fails.
- If M32 metrics are promoted to SRD-GS superiority or paper-scale conclusions, the milestone fails.
- If unavailable metrics or F-score `0.0` are ignored, the milestone fails.

## Verification

- Focused TDD RED: the direct-env false-negative fallback behavior was absent before implementation.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight` passed, 6 tests.
- M32 dry-run command package passed under `outputs/srd_gs_instrumented_runtime_m32_dryrun`.
- M32 host-visible preflight returned `runtime_go=true`.
- M32 bounded runtime chain completed under `outputs/srd_gs_instrumented_runtime_m32_i30`.
- M32 summary table wrote 17 rows.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 33 should remain bounded and read/diagnostic first: compare M32's loss progression, failure-summary unavailable metrics, render-eval manifest, and metrics against the prior short-budget M18/M20/M21/M24/M25/M26 evidence to decide whether the next controlled run should target Stage B/C activation, opacity schedule, or eval/material artifact plumbing. Do not launch broad paper-scale experiments.
