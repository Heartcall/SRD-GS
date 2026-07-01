# Milestone 26: Partial opacity LR control

Status: runtime GO; opacity-drift downweight control GO; mixed rendering-geometry tradeoff; paper-scale still blocked

## Objective

Test one bounded single-scene partial opacity LR control after Milestone 25 showed that fully freezing opacity partially recovers rendering but worsens Chamfer versus M20/M21/M24. M26 keeps the M24 reflection/specular freeze, uses neutral rendered-gate modulation, and sets `--srd_opacity_lr_scale 0.25`.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: quarter opacity LR controls activated-opacity drift much more than M20/M21/M24 in the bounded `ball` 300-iteration SRD branch-raster path.
- Allowed claim: the train -> mesh -> texture -> render_eval_pairs -> accepted-GT eval chain still executes with the partial opacity control.
- Allowed claim: M26 improves Chamfer and Normal MAE versus M25 while retaining better PSNR/Refl-PSNR than M20/M21/M24.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: the rendering regression is fully fixed.
- Disallowed claim: geometry quality is stable or improved across all metrics.
- Disallowed claim: material/PBR quality is validated.
- Disallowed claim: results generalize beyond this one scene and one short checkpoint.

## Implementation

- Added `configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml`.
- Added tests for config discovery and dry-run command isolation.
- No additional training code was required because M25 added the baseline-compatible `--srd_opacity_lr_scale` optimizer control.

## Commands

Dry-run:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_opacity_quarter_m26_i300_dryrun \
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
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_opacity_quarter_m26_i300 \
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

- `outputs/srd_gs_opacity_quarter_m26_i300/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/mesh_surface.ply`
- `outputs/srd_gs_opacity_quarter_m26_i300/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_opacity_quarter_m26_i300/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_opacity_quarter_m26_i300/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_opacity_quarter_m26_i300/tables/ball_opacity_quarter_metric_summary.csv`
- `outputs/srd_gs_opacity_quarter_m26_i300/checkpoint_drift/parameter_deltas.csv`
- `outputs/srd_gs_opacity_quarter_m26_i300/render_regression/case_summary.csv`

## Metrics

| Variant | Iter | Render gate | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 30 | 0.0 | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M20 render gate on | 300 | 1.0 | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 |
| M21 render gate neutral | 300 | 0.0 | 2.9205 | 1.5409 | 0.300529 | 0.001 | 75.9167 | 0.003792 |
| M24 reflection/specular freeze | 300 | 0.0 | 2.8750 | 1.7308 | 0.286904 | 0.000 | 74.6085 | 0.00000037 |
| M25 opacity freeze | 300 | 0.0 | 3.6522 | 2.3203 | 0.397042 | 0.000 | 73.8319 | 0.000229 |
| M26 quarter opacity LR | 300 | 0.0 | 3.1155 | 1.9098 | 0.327672 | 0.000 | 68.5402 | 0.00000763 |

Pairwise deltas versus M18:

| Variant | PSNR delta | Refl-PSNR delta | Chamfer delta | F-score delta | Normal MAE delta | Leakage delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M25 opacity freeze | -0.4320 | -0.4527 | -0.031518 | 0.000 | -12.5805 | -0.001478 |
| M26 quarter opacity LR | -0.9687 | -0.8632 | -0.100889 | 0.000 | -17.8722 | -0.001699 |

Checkpoint deltas versus M18:

| Variant | Gaussian count delta | Opacity mean delta | Scale mean delta | Reflection feature abs delta | Specular weight mean delta | Branch gate mean delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M25 opacity freeze | 0 | -0.072880 | +0.005825 | -0.010269 | +0.000001 | 0.000000 |
| M26 quarter opacity LR | 0 | +0.007478 | +0.002446 | -0.010269 | +0.000001 | 0.000000 |

## Interpretation

M26 gives a different point on the opacity-control tradeoff curve. It keeps activated opacity close to M18 while allowing partial opacity updates. Compared with M25, M26 improves Chamfer and Normal MAE and lowers baking leakage, but it gives up part of M25's PSNR/Refl-PSNR recovery.

M26 remains below M18 in PSNR/Refl-PSNR, F-score remains zero, and Chamfer is still worse than M20/M21/M24. This does not close the paper-scale gate.

## Failure Conditions

- If opacity scale flags leak into render/texture/eval commands, the milestone fails. Dry-run command files show they do not leak.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. This milestone only adds an opt-in config.
- If rendering recovery is claimed as complete, the milestone fails. Full rendering recovery remains NO-GO.
- If geometry superiority is claimed from M26, the milestone fails. Chamfer remains worse than M20/M21/M24 and F-score remains zero.
- If multi-scene conclusions are drawn from this run, the milestone fails. Paper-scale remains NO-GO.

## Verification

- Focused TDD suite: `python -m unittest tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract` passed, 12 tests.
- Dry-run command contract passed for `outputs/srd_gs_opacity_quarter_m26_i300_dryrun`.
- Runtime chain passed under `outputs/srd_gs_opacity_quarter_m26_i300` after host-visible CUDA approval.
- Summary collection wrote 17 rows to `outputs/srd_gs_opacity_quarter_m26_i300/tables/ball_opacity_quarter_metric_summary.csv`.
- Checkpoint drift and render-regression diagnosis passed under `outputs/srd_gs_opacity_quarter_m26_i300/`.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 78 tests.
- `conda run -n ref_gs python -m py_compile tests/test_branch_raster_smoke_runner.py tests/test_ablation_system_contract.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M26 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.

## Recommended Next Milestone

Milestone 27 should be a bounded single-scene opacity-control synthesis or at most one additional opacity scale if needed. Recommended first step is to summarize M25/M26 into an opacity tradeoff table and define whether an intermediate scale such as `0.125` is justified. Do not launch broad paper-scale experiments until the rendering/geometry tradeoff and F-score blocker are resolved.
