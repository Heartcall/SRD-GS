# Milestone 16: Single-scene Three-variant Comparison

Status: bounded single-scene comparison GO; paper-scale and stable quality claims still blocked

## Goal

Milestone 16 compares the three nearest variants at the same budget before launching any multi-scene ablation matrix:

- `refgs_baseline`
- `full_srd_gs`
- `full_srd_gs_branch_raster`

The goal is to validate the metric chain and identify the next engineering lever, not to claim method superiority.

## Added Runner

`scripts/srd_gs/run_single_scene_comparison.sh` defaults to dry-run and calls the per-variant smoke runner for the three configs above. It then collects all `eval_with_gt_mesh/metrics.json` files into one table via `scripts/srd_gs/collect_results.py`.

The result collector now recognizes both:

- `<scene>/<variant>/eval/metrics.json`
- `<scene>/<variant>/eval_with_gt_mesh/metrics.json`

## Runtime Evidence

Executed command:

```bash
bash scripts/srd_gs/run_single_scene_comparison.sh \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_single_scene_comparison_m16_i30 \
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

- `outputs/srd_gs_single_scene_comparison_m16_i30/tables/ball_metric_summary.csv`
- `outputs/srd_gs_single_scene_comparison_m16_i30/results/ball/refgs_baseline/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_single_scene_comparison_m16_i30/results/ball/full_srd_gs/eval_with_gt_mesh/metrics.csv`
- `outputs/srd_gs_single_scene_comparison_m16_i30/results/ball/full_srd_gs_branch_raster/eval_with_gt_mesh/metrics.csv`

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Baking highlight leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `refgs_baseline` | 5.7927 | 5.2827 | 0.430455 | 0.000 | 85.4228 | 0.207529 |
| `full_srd_gs` | 5.7881 | 5.2728 | 0.429746 | 0.000 | 87.2881 | 0.206033 |
| `full_srd_gs_branch_raster` | 4.0390 | 2.7114 | 0.435425 | 0.001 | 82.9009 | 0.001642 |

Branch policy evidence:

- `refgs_baseline`: `baseline_no_srd`
- `full_srd_gs`: `fallback_neutral_gate`
- `full_srd_gs_branch_raster`: `raster_feature_chunks`, `gate_applied=true`, branch/specular/transport maps rasterized with backward enabled

## Interpretation

The 30-iteration result is an engineering comparison, not a paper result.

Supported:

- The three-variant single-scene metric chain runs end-to-end with `eval=True`.
- All three variants produce non-empty meshes with `depth_trunc=10.0`.
- The branch-raster variant continues to expose non-fallback branch diagnostics.
- The branch-raster variant has much lower image-space baking highlight leakage in this bounded run.

Not supported:

- A rendering-quality improvement claim. Branch-raster PSNR and Refl-PSNR are worse at this short budget.
- A stable mesh-quality improvement claim. Branch-raster improves normal MAE and tiny F-score here, but Chamfer is worse than both baseline and fallback SRD-GS.
- A paper-scale material claim. Material metrics still lack GT albedo/roughness references; baking leakage is a diagnostic only.

## Next Engineering Step

Do not launch the full multi-scene matrix yet. The next minimal lever should target the branch-raster quality tradeoff:

- delay or ramp `--srd_use_branch_gate` instead of enabling the gate from iteration 1; or
- run a longer single-scene branch-raster comparison after Stage A/B schedules activate.

The current evidence suggests the branch-raster path is technically runnable but too aggressive for early rendering fidelity.
