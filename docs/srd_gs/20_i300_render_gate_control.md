# Milestone 20: Same-budget Render-gate-delay Control

Status: same-budget control GO; rendering quality still NO-GO; paper-scale still NO-GO

## Goal

Milestone 19 showed that a 300-iteration accelerated Stage B/C pilot completed the full metric chain and improved geometry metrics over M18, but PSNR/Refl-PSNR degraded. Milestone 20 tests a same-budget 300-iteration control without accelerated Stage B/C to isolate whether the M19 rendering drop is caused by the shortened Stage B/C schedule or by another factor such as the longer checkpoint or rendered gate activation.

## Implementation

Added:

- `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_i300_control.yaml`

The config keeps the M19 branch-gate and render-gate timing:

```text
srd_branch_gate_start_iter = 10
srd_branch_gate_ramp_iters = 20
srd_render_gate_start_iter = 200
srd_render_gate_ramp_iters = 100
```

It intentionally does not set `--srd_reflection_warmup 100` or any manual `--srd_stage`, so with the default warmup the 300-iteration training run remains in Stage A.

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_i300_control.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_i300_control_m20 \
  --scene_name ball \
  --iterations 300 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000 \
  --execute
```

Training progress stayed in `stage_a` through iteration 300.

Key artifacts:

- `outputs/srd_gs_i300_control_m20/results/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_i300_control_m20/results/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_i300_control_m20/results/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_i300_control_m20/tables/ball_i300_control_metric_summary.csv`

Manifest evidence:

```text
policy: raster_feature_chunks
gate_applied: true
branch_gate_weight: 1.0
render_gate_weight: 1.0
branch/specular/transport maps rasterized: true
branch/specular/transport backward_to_gaussian: true
```

Mesh artifact check:

```text
mesh_surface.ply size: 118403176 bytes
```

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay, 30 iter | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M19 Stage B/C pilot, 300 iter | 2.9393 | 1.5355 | 0.316800 | 0.000 | 75.8534 | 0.005147 |
| M20 Stage-A control, 300 iter | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 |

## Interpretation

Supported:

- The same-budget control completed train, surface mesh extraction, specular-free texture export, test-split render pairs, and accepted-GT mesh evaluation.
- The control stayed in Stage A, while matching M19's final branch/render gate state.
- M20 slightly improves Chamfer and Normal MAE versus M19 and has nearly identical PSNR/Refl-PSNR.
- This suggests the M19 rendering drop is not explained by the accelerated Stage B/C schedule alone.

Not supported:

- Rendering-quality recovery: M20 PSNR/Refl-PSNR remain far below M18.
- F-score improvement: F-score remains `0.0`.
- Material/PBR quality: GT albedo/roughness are still unavailable, and baking leakage is higher than M18/M19.
- Paper-scale superiority: this is one scene, one control variant, two test render views, and 300 iterations.

## Failure Conditions Observed

- No runtime failure, empty mesh, fallback branch policy, or missing metrics occurred.
- Quality failures remain: rendering fidelity is low, F-score is zero, and baking leakage increased.

## Next Step

Before any multi-scene expansion, test whether keeping rendered branch-gate modulation neutral at the 300-iteration checkpoint recovers PSNR/Refl-PSNR. A bounded `ball` control should keep branch-raster diagnostics active and train for 300 iterations, but set `srd_render_gate_start_iter` beyond 300 so `render_gate_weight=0.0` at evaluation.
