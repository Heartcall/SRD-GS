# Milestone 19: Bounded Stage B/C Render-gate-delay Pilot

Status: Stage B/C runtime GO; quality mixed; paper-scale still NO-GO

## Goal

Milestone 18 verified that render-gate delay can decouple diagnostic branch-map rasterization from rendered specular modulation at a 30-iteration `ball` budget. Milestone 19 tests whether the same control can survive a bounded Stage B/C activation run before any broad experiment.

This is not a default long-warmup paper run. It is a single-scene pilot with an explicitly shortened SRD warmup so that Stage B/C losses execute within 300 iterations.

## Implementation

Added:

- `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_stagebc.yaml`

The config keeps branch-raster diagnostics and render-gate delay, while setting:

```text
srd_reflection_warmup = 100
srd_branch_gate_start_iter = 10
srd_branch_gate_ramp_iters = 20
srd_render_gate_start_iter = 200
srd_render_gate_ramp_iters = 100
```

At 300 iterations this covers:

- Stage A through iteration 100.
- Stage B after iteration 100.
- Stage C after iteration 200.
- Render gate reaches `1.0` at the final checkpoint.

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_stagebc.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_stagebc_m19_i300 \
  --scene_name ball \
  --iterations 300 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000 \
  --execute
```

Training progress showed `stage_a`, `stage_b`, and `stage_c`; Stage C logs included non-zero `tex` loss.

Key artifacts:

- `outputs/srd_gs_stagebc_m19_i300/results/ball/full_srd_gs_branch_raster_render_gate_delay_stagebc/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_stagebc_m19_i300/results/ball/full_srd_gs_branch_raster_render_gate_delay_stagebc/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_stagebc_m19_i300/results/ball/full_srd_gs_branch_raster_render_gate_delay_stagebc/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_stagebc_m19_i300/tables/ball_stagebc_metric_summary.csv`

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
mesh_surface.ply size: 118965832 bytes
```

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay, 30 iter | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |
| M19 Stage B/C pilot, 300 iter | 2.9393 | 1.5355 | 0.316800 | 0.000 | 75.8534 | 0.005147 |

## Interpretation

Supported:

- Stage B/C training executes in the branch-raster render-gate-delay path.
- The train -> surface mesh -> specular-free texture -> test-split render pairs -> accepted-GT mesh eval chain completes.
- Branch/specular/transport diagnostics remain non-fallback `raster_feature_chunks`.
- Geometry metrics improve over M18 on Chamfer and Normal MAE in this single-scene pilot.

Not supported:

- Rendering-quality improvement: PSNR and Refl-PSNR degrade substantially versus M18.
- F-score improvement: F-score remains `0.0`.
- Material/PBR quality: GT albedo/roughness are still unavailable, and image-space baking leakage increases versus M18.
- Paper-scale superiority: this is one scene, one accelerated schedule, two test render views, and 300 iterations.

## Failure Conditions Observed

- No runtime failure, empty mesh, fallback branch policy, or missing metrics occurred.
- Quality failure remains: render fidelity is worse, and F-score is still zero.

## Next Step

Before expanding scenes, compare the M19 accelerated Stage B/C variant against a same-budget render-gate-delay control without accelerated Stage B/C. This isolates whether the PSNR drop comes from the longer 300-iteration checkpoint, the shortened Stage B/C schedule, or rendered gate activation.
