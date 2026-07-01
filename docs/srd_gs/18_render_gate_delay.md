# Milestone 18: Render-gate Delay for Branch-raster SRD-GS

Status: bounded control GO; short-budget rendering/geometry partial GO; paper-scale still NO-GO

## Goal

Milestone 17 showed that delaying/ramping the same branch gate used for diagnostics and rendering did not improve the 30-iteration `ball` tradeoff. Milestone 18 tests a stronger bounded control: keep branch/specular/transport maps rasterized for diagnostics while delaying only the branch-gate multiplication used in rendered specular.

## Implementation

Added:

- `utils/srd_schedule.py::compute_srd_render_gate_weight()`
- `--srd_render_gate_start_iter`
- `--srd_render_gate_ramp_iters`
- `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml`

Defaults are backward-compatible:

```text
srd_render_gate_start_iter = -1
srd_render_gate_ramp_iters = -1
```

Negative values make the rendered gate reuse the diagnostic branch-gate schedule. Existing configs therefore keep their prior behavior.

When explicit render-gate delay is enabled, the renderer keeps two gate maps:

```text
diagnostic_gate = 1 + branch_gate_weight * (rasterized_branch_gate - 1)
render_gate = 1 + render_gate_weight * (rasterized_branch_gate - 1)
```

`branch_gate_map` exports and SRD diagnostics use `diagnostic_gate`; final `pbr_rgb` uses `render_gate * spec_light`.

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_render_gate_delay_m18_i30 \
  --scene_name ball \
  --iterations 30 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000 \
  --execute
```

Key artifacts:

- `outputs/srd_gs_render_gate_delay_m18_i30/results/ball/full_srd_gs_branch_raster_render_gate_delay/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_render_gate_delay_m18_i30/results/ball/full_srd_gs_branch_raster_render_gate_delay/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_render_gate_delay_m18_i30/results/ball/full_srd_gs_branch_raster_render_gate_delay/pbr_textures_specular_free/baking_report.json`
- `outputs/srd_gs_render_gate_delay_m18_i30/tables/ball_render_gate_delay_metric_summary.csv`

Manifest evidence:

```text
policy: raster_feature_chunks
gate_applied: false
branch_gate_weight: 1.0
render_gate_weight: 0.0
branch/specular/transport maps rasterized: true
branch/specular/transport backward_to_gaussian: true
```

This confirms that the diagnostic branch gate is fully scheduled at iteration 30, while rendered specular gate modulation is still neutral.

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M16 immediate branch-raster | 4.0390 | 2.7114 | 0.435425 | 0.001 | 82.9009 | 0.001642 |
| M17 gate-ramp branch-raster | 4.0389 | 2.7112 | 0.442081 | 0.001 | 85.6183 | 0.001714 |
| M18 render-gate delay | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 |

Mesh artifact check:

```text
mesh_surface.ply size: 143497970 bytes
```

## Interpretation

Supported:

- Render-gate delay is wired through CLI, checkpoint-loaded render/export paths, and branch-raster diagnostics.
- The run completed train, surface mesh extraction, specular-free texture export, test-split render pairs, and accepted-GT mesh evaluation.
- The variant improves short-budget PSNR/Refl-PSNR and Chamfer relative to M16/M17 branch-raster variants while preserving low baking highlight leakage.

Not supported:

- F-score remains `0.0`.
- Normal MAE is worse than M16 immediate branch-raster.
- The result is still one scene, two test render views, and a 30-iteration budget. It is not a paper-scale quality claim.

## Next Step

Run the same render-gate delay setting at a longer single-scene budget where Stage B/C losses activate before deciding whether to expand beyond `ball`.
