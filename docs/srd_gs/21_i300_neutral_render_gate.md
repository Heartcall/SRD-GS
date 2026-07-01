# Milestone 21: Neutral Render-gate 300-iteration Control

Status: neutral render-gate control GO; rendering quality still NO-GO; paper-scale still NO-GO

## Goal

Milestone 20 showed that a same-budget 300-iteration Stage-A control had nearly the same PSNR/Refl-PSNR degradation as the accelerated Stage B/C pilot. Milestone 21 tests whether rendered branch-gate activation itself caused that degradation by keeping rendered gate modulation neutral through the 300-iteration checkpoint while retaining branch-raster diagnostics.

## Implementation

Added:

- `configs/srd_gs/full_srd_gs_branch_raster_render_gate_neutral_i300.yaml`

The config keeps diagnostic branch-gate scheduling active:

```text
srd_branch_gate_start_iter = 10
srd_branch_gate_ramp_iters = 20
```

It keeps rendered branch-gate modulation neutral through the checkpoint:

```text
srd_render_gate_start_iter = 100000
srd_render_gate_ramp_iters = 0
```

It intentionally does not set `--srd_reflection_warmup 100` or manual `--srd_stage`, so the 300-iteration training run remains in Stage A.

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_neutral_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_i300_neutral_gate_m21 \
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

- `outputs/srd_gs_i300_neutral_gate_m21/results/ball/full_srd_gs_branch_raster_render_gate_neutral_i300/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_i300_neutral_gate_m21/results/ball/full_srd_gs_branch_raster_render_gate_neutral_i300/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_i300_neutral_gate_m21/results/ball/full_srd_gs_branch_raster_render_gate_neutral_i300/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_i300_neutral_gate_m21/tables/ball_i300_neutral_gate_metric_summary.csv`

Manifest evidence:

```text
policy: raster_feature_chunks
gate_applied: false
branch_gate_weight: 1.0
render_gate_weight: 0.0
branch/specular/transport maps rasterized: true
branch/specular/transport backward_to_gaussian: true
```

Mesh artifact check:

```text
mesh_surface.ply size: 119185444 bytes
```

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay, 30 iter | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M20 Stage-A control, render gate on, 300 iter | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 |
| M21 Stage-A control, render gate neutral, 300 iter | 2.9205 | 1.5409 | 0.300529 | 0.001 | 75.9167 | 0.003792 |

## Interpretation

Supported:

- The neutral render-gate control completed train, surface mesh extraction, specular-free texture export, test-split render pairs, and accepted-GT mesh evaluation.
- The manifest proves branch-raster diagnostics stayed active while rendered gate modulation stayed neutral.
- Chamfer, F-score, and baking highlight leakage improve over M20 in this bounded single-scene control.

Not supported:

- Rendering-quality recovery: PSNR/Refl-PSNR remain essentially at the M20 degraded level and far below M18.
- Normal MAE improvement over M20: Normal MAE worsens slightly versus M20.
- Material/PBR quality: GT albedo/roughness are still unavailable.
- Paper-scale superiority: this is one scene, one control variant, two test render views, and 300 iterations.

## Failure Conditions Observed

- No runtime failure, empty mesh, fallback branch policy, or missing metrics occurred.
- Quality failures remain: rendering fidelity is low and material metrics remain unavailable.

## Next Step

Rendered gate activation is not the sole cause of the 300-iteration rendering drop. Before expanding scenes, run an artifact-level diagnosis comparing M18/M20/M21 render pairs and diagnostic maps to determine whether the drop comes from checkpoint-length training dynamics, specular-weight behavior, branch diagnostics, or evaluation-mask effects. This should be a read-only analysis milestone over existing outputs before launching another training run.
