# Milestone 25: Opacity freeze control

Status: runtime GO; opacity-drift control GO; rendering partial recovery GO; full recovery and paper-scale still blocked

## Objective

Test one bounded single-scene opacity-drift control after Milestone 24 showed that reflection/specular freezing controls its target but does not recover rendering. M25 freezes opacity updates on top of the M24 reflection/specular freeze while keeping the neutral rendered-gate 300-iteration `ball` setup.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: optimizer-level opacity freezing can control activated-opacity drift in the bounded `ball` 300-iteration SRD branch-raster path.
- Allowed claim: the train -> mesh -> texture -> render_eval_pairs -> accepted-GT eval chain still executes with the opacity freeze control.
- Allowed claim: the bounded M25 control partially recovers PSNR/Refl-PSNR versus M20/M21/M24.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: the rendering regression is fully fixed.
- Disallowed claim: geometry quality is stable or improved across metrics.
- Disallowed claim: material/PBR quality is validated.
- Disallowed claim: results generalize beyond this one scene and one short checkpoint.

## Implementation

- Added `--srd_opacity_lr_scale` to `OptimizationParams`, defaulting to `1.0`.
- Applied the scale only to the existing opacity optimizer group in `scene/gaussian_model.py`.
- Added `configs/srd_gs/full_srd_gs_branch_raster_opacity_freeze_i300.yaml`.
- Added tests for neutral defaults, optimizer-group targeting, dry-run command isolation, and config discovery.

## Commands

Dry-run:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_freeze_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_opacity_freeze_m25_i300_dryrun \
  --scene_name ball \
  --iterations 300 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000
```

Runtime:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_freeze_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_opacity_freeze_m25_i300 \
  --scene_name ball \
  --iterations 300 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000 \
  --execute
```

The first sandbox runtime attempt failed with `RuntimeError: No CUDA GPUs are available`. The same bounded command succeeded in the approved host-visible CUDA context.

## Outputs

- `outputs/srd_gs_opacity_freeze_m25_i300/results/ball/full_srd_gs_branch_raster_opacity_freeze_i300/mesh_surface.ply`
- `outputs/srd_gs_opacity_freeze_m25_i300/results/ball/full_srd_gs_branch_raster_opacity_freeze_i300/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_opacity_freeze_m25_i300/results/ball/full_srd_gs_branch_raster_opacity_freeze_i300/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_opacity_freeze_m25_i300/results/ball/full_srd_gs_branch_raster_opacity_freeze_i300/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_opacity_freeze_m25_i300/tables/ball_opacity_freeze_metric_summary.csv`
- `outputs/srd_gs_opacity_freeze_m25_i300/checkpoint_drift/parameter_deltas.csv`
- `outputs/srd_gs_opacity_freeze_m25_i300/render_regression/case_summary.csv`

## Metrics

| Variant | Iter | Render gate | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 30 | 0.0 | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M20 render gate on | 300 | 1.0 | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 |
| M21 render gate neutral | 300 | 0.0 | 2.9205 | 1.5409 | 0.300529 | 0.001 | 75.9167 | 0.003792 |
| M24 reflection/specular freeze | 300 | 0.0 | 2.8750 | 1.7308 | 0.286904 | 0.000 | 74.6085 | 0.00000037 |
| M25 opacity/reflection/specular freeze | 300 | 0.0 | 3.6522 | 2.3203 | 0.397042 | 0.000 | 73.8319 | 0.000229 |

Pairwise deltas versus M18:

| Variant | PSNR delta | Refl-PSNR delta | Chamfer delta | F-score delta | Normal MAE delta | Leakage delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M20 render gate on | -1.1448 | -1.2319 | -0.117444 | 0.000 | -10.9810 | +0.004881 |
| M21 render gate neutral | -1.1637 | -1.2321 | -0.128032 | +0.001 | -10.4958 | +0.002085 |
| M24 reflection/specular freeze | -1.2092 | -1.0422 | -0.141657 | 0.000 | -11.8039 | -0.001707 |
| M25 opacity/reflection/specular freeze | -0.4320 | -0.4527 | -0.031518 | 0.000 | -12.5805 | -0.001478 |

Checkpoint deltas versus M18:

| Variant | Gaussian count delta | Opacity mean delta | Scale mean delta | Reflection feature abs delta | Specular weight mean delta | Branch gate mean delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M20 render gate on | 0 | +0.143890 | +0.000985 | +0.043091 | +0.000445 | -0.001356 |
| M21 render gate neutral | 0 | +0.143303 | +0.000986 | +0.043523 | +0.000382 | 0.000000 |
| M24 reflection/specular freeze | 0 | +0.166588 | +0.000988 | -0.010269 | +0.000001 | 0.000000 |
| M25 opacity/reflection/specular freeze | 0 | -0.072880 | +0.005825 | -0.010269 | +0.000001 | 0.000000 |

## Interpretation

The opacity freeze hit its intended target: activated opacity no longer drifts upward and instead stays near the initialized value. PSNR and Refl-PSNR recover substantially compared with M20/M21/M24, which supports opacity dynamics as a contributor to the 300-iteration rendering regression.

The result is still not a full recovery. M25 remains below M18 in PSNR and Refl-PSNR, F-score remains zero, and Chamfer worsens relative to M20/M21/M24. The next control should test a partial opacity update or delayed/ramped opacity LR, not a broad experiment.

## Failure Conditions

- If opacity freeze flags leak into render/texture/eval commands, the milestone fails. Dry-run command files show they do not leak.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. Defaults remain neutral at `1.0`, and SRD flags are opt-in.
- If rendering recovery is claimed as complete, the milestone fails. Full rendering recovery remains NO-GO.
- If geometry superiority is claimed from M25, the milestone fails. Chamfer worsens versus M20/M21/M24 and F-score remains zero.
- If multi-scene conclusions are drawn from this run, the milestone fails. Paper-scale remains NO-GO.

## Verification

- Focused TDD suite: `python -m unittest tests.test_srd_gaussian_model_static tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract` passed, 18 tests.
- Dry-run command contract passed for `outputs/srd_gs_opacity_freeze_m25_i300_dryrun`.
- Runtime chain passed under `outputs/srd_gs_opacity_freeze_m25_i300` after host-visible CUDA approval.
- Summary collection wrote 17 rows to `outputs/srd_gs_opacity_freeze_m25_i300/tables/ball_opacity_freeze_metric_summary.csv`.
- Checkpoint drift and render-regression diagnosis passed under `outputs/srd_gs_opacity_freeze_m25_i300/`.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 77 tests.
- `conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py tests/test_srd_gaussian_model_static.py tests/test_branch_raster_smoke_runner.py tests/test_ablation_system_contract.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M25 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.

## Recommended Next Milestone

Milestone 26 should be one bounded opacity schedule/downweight control for `ball`, dry-run first. A conservative target is partial opacity LR or delayed/ramped opacity updates while preserving the M24 reflection/specular freeze and neutral rendered gate. Do not launch broad paper-scale experiments until rendering recovery and geometry tradeoffs are resolved.
