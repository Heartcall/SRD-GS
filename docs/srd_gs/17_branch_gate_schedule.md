# Milestone 17: Branch-gate Delay/Ramp Schedule

Status: runtime/control plumbing GO; short-budget quality improvement NO-GO

## Goal

Milestone 16 showed that immediate branch-raster gate usage is technically runnable but hurts PSNR/Refl-PSNR at a 30-iteration `ball` budget. Milestone 17 adds an opt-in delayed/ramped branch-gate schedule to test whether reducing early gate strength improves that tradeoff.

## Implementation

Added:

- `utils/srd_schedule.py::compute_srd_branch_gate_weight()`
- `--srd_branch_gate_start_iter`
- `--srd_branch_gate_ramp_iters`
- `configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml`

The default values are `0` and `0`, so existing baseline, fallback SRD-GS, and immediate branch-raster commands keep their previous behavior.

When branch-gate scheduling is enabled, the renderer uses:

```text
effective_gate = 1 + branch_gate_weight * (rasterized_branch_gate - 1)
```

This keeps the gate neutral before the schedule starts and linearly blends toward the learned branch gate during the ramp.

The checkpoint iteration is now propagated into:

- `render_eval_pairs.py`
- `export_pbr_textures.py`
- `extract_surface_mesh.py` through `GaussianExtractor(render_iteration=...)`

This prevents evaluation/export from accidentally using `iteration=0` schedule behavior.

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_branch_gate_ramp_m17_i30 \
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

- `outputs/srd_gs_branch_gate_ramp_m17_i30/results/ball/full_srd_gs_branch_raster_gate_ramp/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_branch_gate_ramp_m17_i30/results/ball/full_srd_gs_branch_raster_gate_ramp/render_eval_pairs/render_eval_manifest.json`
- `outputs/srd_gs_branch_gate_ramp_m17_i30/tables/ball_gate_ramp_metric_summary.csv`

Manifest evidence:

```text
policy: raster_feature_chunks
gate_applied: true
branch_gate_weight: 1.0
branch/specular/transport maps rasterized: true
branch/specular/transport backward_to_gaussian: true
```

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M16 immediate branch-raster | 4.0390 | 2.7114 | 0.435425 | 0.001 | 82.9009 | 0.001642 |
| M17 gate-ramp branch-raster | 4.0389 | 2.7112 | 0.442081 | 0.001 | 85.6183 | 0.001714 |

## Interpretation

Supported:

- The opt-in branch-gate schedule is wired through training, rendering, texture export, and mesh extraction.
- Default behavior remains backward-compatible.
- The scheduled variant completes the full metric chain and preserves non-fallback branch diagnostics.

Not supported:

- The `start_iter=10`, `ramp_iters=20`, 30-iteration setting does not improve rendering fidelity over immediate branch-raster.
- It does not improve Chamfer or normal MAE over immediate branch-raster.
- It should not be promoted to multi-scene paper-scale experiments.

## Next Step

The next engineering lever should be stronger than a simple branch-gate ramp. Candidate bounded tests:

- keep branch-gate modulation disabled for rendering until Stage B/C while still rasterizing diagnostics;
- ramp specular-weight or separation losses rather than the rendered gate;
- run a longer single-scene budget where Stage B losses activate before evaluating branch-raster quality.

Keep all geometry metrics raw-coordinate primary and continue treating paper-scale quality claims as blocked.
