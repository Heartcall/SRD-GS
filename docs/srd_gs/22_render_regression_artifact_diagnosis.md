# Milestone 22: Render Regression Artifact Diagnosis

Status: read-only artifact diagnosis GO; rendering quality still NO-GO; paper-scale still NO-GO

## Goal

Milestone 21 showed that keeping rendered branch-gate modulation neutral at the 300-iteration checkpoint did not recover PSNR/Refl-PSNR. Milestone 22 performs a read-only diagnosis over existing M18/M20/M21 artifacts before launching any more training.

The goal is to localize the 300-iteration rendering drop across:

- checkpoint-length training dynamics;
- rendered gate activation;
- specular/diffuse decomposition behavior;
- branch diagnostic map behavior;
- evaluation-mask effects.

This milestone does not launch training, rendering, mesh extraction, texture export, or broad multi-scene experiments.

## Implementation

Added:

- `scripts/srd_gs/diagnose_render_regression.py`
- `tests/test_render_regression_diagnosis.py`

The diagnostic script accepts repeated `--case LABEL=RESULT_ROOT` arguments and writes:

- `case_summary.csv`
- `map_stats.csv`
- `pairwise_deltas.csv`
- `diagnosis_summary.json`
- `diagnosis_report.md`

The test constructs temporary M18/M20/M21-style artifacts and verifies that the script writes all outputs, preserves `render_gate_weight=0.0` for the neutral case, reports negative PSNR/Refl-PSNR deltas, and keeps the report's paper-scale gate at `NO-GO`.

## Runtime Evidence

Executed command:

```bash
python scripts/srd_gs/diagnose_render_regression.py \
  --case M18_render_gate_delay_i30=outputs/srd_gs_render_gate_delay_m18_i30/results/ball/full_srd_gs_branch_raster_render_gate_delay \
  --case M20_i300_render_gate_on=outputs/srd_gs_i300_control_m20/results/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control \
  --case M21_i300_render_gate_neutral=outputs/srd_gs_i300_neutral_gate_m21/results/ball/full_srd_gs_branch_raster_render_gate_neutral_i300 \
  --output_dir outputs/srd_gs_render_regression_diag_m22
```

Key artifacts:

- `outputs/srd_gs_render_regression_diag_m22/case_summary.csv`
- `outputs/srd_gs_render_regression_diag_m22/map_stats.csv`
- `outputs/srd_gs_render_regression_diag_m22/pairwise_deltas.csv`
- `outputs/srd_gs_render_regression_diag_m22/diagnosis_summary.json`
- `outputs/srd_gs_render_regression_diag_m22/diagnosis_report.md`

Diagnosis flags:

```text
rendering_regression_vs_baseline
render_gate_activation_not_sole_cause
geometry_can_improve_while_rendering_degrades
```

## Metrics and Deltas

| Variant | Iter | Render gate | PSNR | Refl-PSNR | Chamfer | F-score | Leakage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 30 | 0.0 | 4.0842 | 2.7730 | 0.428561 | 0.000 | 0.001707 |
| M20 render gate on | 300 | 1.0 | 2.9394 | 1.5411 | 0.311117 | 0.000 | 0.006588 |
| M21 render gate neutral | 300 | 0.0 | 2.9205 | 1.5409 | 0.300529 | 0.001 | 0.003792 |

Pairwise deltas versus M18:

| Variant | PSNR delta | Refl-PSNR delta | Chamfer delta | F-score delta | Leakage delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| M20 render gate on | -1.1448 | -1.2319 | -0.117444 | 0.000 | +0.004881 |
| M21 render gate neutral | -1.1637 | -1.2321 | -0.128032 | +0.001 | +0.002085 |

Selected map statistics:

| Variant | RGB residual L1 mean | Reflective residual L1 mean | Specular mean | Branch gate mean | Reflective mask mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 0.5094 | 0.6630 | 0.0577 | 0.0228 | 0.7344 |
| M20 render gate on | 0.5711 | 0.7574 | 0.2700 | 0.0249 | 0.7202 |
| M21 render gate neutral | 0.5752 | 0.7597 | 0.1446 | 0.0254 | 0.7233 |

## Interpretation

Supported:

- The M20 and M21 render-pair artifacts both show a rendering regression versus M18 in PSNR and Refl-PSNR.
- M21 has `render_gate_weight=0.0` and still shows the same degraded PSNR/Refl-PSNR level, so rendered branch-gate activation is not the sole cause.
- The 300-iteration variants improve raw-coordinate Chamfer versus M18 while worsening RGB/reflective residuals, so geometry and rendering quality are moving in different directions in this bounded evidence set.
- Branch-gate map means and reflective-mask means are similar across the three cases, which makes a gross branch-mask coverage change less likely as the only explanation.
- Specular/diffuse statistics change substantially from M18 to M20/M21, but this diagnosis does not prove whether those changes are cause or effect.

Not supported:

- A complete root-cause diagnosis. The current artifact statistics localize the issue but do not distinguish checkpoint-length optimization dynamics from learned specular/diffuse parameter drift.
- Rendering-quality recovery.
- Stable mesh/material superiority.
- PBR material quality without GT albedo/roughness.
- Any broad paper-scale claim.

## Failure Conditions Observed

- No missing artifact was reported in the M18/M20/M21 diagnosis tables.
- No empty mesh or failed metric file was introduced in this milestone.
- Quality failure remains: PSNR/Refl-PSNR are still degraded for both 300-iteration variants.

## Next Step

Before any new training or multi-scene expansion, run a read-only checkpoint/training-log diagnosis over M18/M20/M21. The next bounded milestone should inspect checkpoint parameter statistics and training logs for Gaussian count, opacity/scale distributions, diffuse/specular branch parameter drift, and loss progression. If that identifies a concrete mechanism, only then test one small single-scene control.
