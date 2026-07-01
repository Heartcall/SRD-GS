# Milestone 23: Checkpoint Drift Diagnosis

Status: read-only checkpoint diagnosis GO; root-cause still incomplete; paper-scale still NO-GO

## Goal

Milestone 22 localized the 300-iteration rendering drop away from rendered branch-gate activation alone. Milestone 23 performs a read-only diagnosis over M18/M20/M21 model checkpoints and config artifacts before launching any more training.

The goal is to inspect:

- Gaussian count;
- opacity and scale distributions;
- saved diffuse/specular/SRD branch parameter drift;
- available config and training-log evidence.

This milestone does not launch training, rendering, mesh extraction, texture export, or broad multi-scene experiments.

## Implementation

Added:

- `scripts/srd_gs/diagnose_checkpoint_drift.py`
- `tests/test_checkpoint_drift_diagnosis.py`

The diagnostic script accepts repeated `--case LABEL=MODEL_ROOT` arguments and writes:

- `checkpoint_summary.csv`
- `parameter_stats.csv`
- `parameter_deltas.csv`
- `checkpoint_diagnosis_summary.json`
- `checkpoint_diagnosis_report.md`

The test constructs temporary M18/M20/M21-style PLY checkpoints and verifies that the script writes all outputs, records Gaussian count and checkpoint iteration, detects branch/specular parameter drift, and keeps the report's paper-scale gate at `NO-GO`.

## Runtime Evidence

Executed command:

```bash
python scripts/srd_gs/diagnose_checkpoint_drift.py \
  --case M18_render_gate_delay_i30=outputs/srd_gs_render_gate_delay_m18_i30/models/ball/full_srd_gs_branch_raster_render_gate_delay \
  --case M20_i300_render_gate_on=outputs/srd_gs_i300_control_m20/models/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control \
  --case M21_i300_render_gate_neutral=outputs/srd_gs_i300_neutral_gate_m21/models/ball/full_srd_gs_branch_raster_render_gate_neutral_i300 \
  --output_dir outputs/srd_gs_checkpoint_drift_diag_m23
```

Key artifacts:

- `outputs/srd_gs_checkpoint_drift_diag_m23/checkpoint_summary.csv`
- `outputs/srd_gs_checkpoint_drift_diag_m23/parameter_stats.csv`
- `outputs/srd_gs_checkpoint_drift_diag_m23/parameter_deltas.csv`
- `outputs/srd_gs_checkpoint_drift_diag_m23/checkpoint_diagnosis_summary.json`
- `outputs/srd_gs_checkpoint_drift_diag_m23/checkpoint_diagnosis_report.md`

Diagnosis flags:

```text
no_gaussian_count_growth
training_loss_logs_unavailable
branch_or_specular_parameter_drift_present
```

## Checkpoint Summary

| Variant | Iter | Gaussian count | eval | SRD enabled | Render gate start | Render gate ramp |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| M18 render-gate delay | 30 | 100000 | True | True | 60 | 0 |
| M20 render gate on | 300 | 100000 | True | True | 200 | 100 |
| M21 render gate neutral | 300 | 100000 | True | True | 100000 | 0 |

## Parameter Deltas Versus M18

| Variant | Gaussian count delta | Opacity mean delta | Scale exp mean delta | Surface roughness mean delta | Reflection feature abs mean delta | Specular weight mean delta | Branch gate mean delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M20 render gate on | 0 | +0.143890 | +0.000985 | +0.008849 | +0.043091 | +0.000445 | -0.001356 |
| M21 render gate neutral | 0 | +0.143303 | +0.000986 | +0.007599 | +0.043523 | +0.000382 | 0.000000 |

Selected absolute means:

| Variant | Opacity activated | Scale exp | Reflection feature abs | Specular weight activated | Branch gate activated |
| --- | ---: | ---: | ---: | ---: | ---: |
| M18 render-gate delay | 0.172880 | 0.010646 | 0.010349 | 0.049999 | 0.050000 |
| M20 render gate on | 0.316771 | 0.011631 | 0.053440 | 0.050445 | 0.048644 |
| M21 render gate neutral | 0.316184 | 0.011632 | 0.053871 | 0.050382 | 0.050000 |

## Interpretation

Supported:

- Gaussian count is identical across M18/M20/M21, so Gaussian count growth alone does not explain the 300-iteration rendering drop.
- M20 and M21 both show much higher activated opacity mean than M18.
- M20 and M21 both show much higher reflection-feature absolute mean than M18.
- M21's branch-gate activated mean matches M18, while rendering remains degraded; this is consistent with M22's finding that branch-gate activation/coverage alone is not the full cause.
- The saved checkpoint statistics make opacity/reflection-feature drift plausible next investigation targets.

Not supported:

- A complete root-cause diagnosis. The current checkpoint statistics are correlational and do not prove whether opacity/reflection drift causes the rendering drop or co-occurs with longer training.
- Loss-progression analysis: no training loss logs were available in the supplied model roots.
- Rendering-quality recovery.
- Stable mesh/material superiority.
- PBR material quality without GT albedo/roughness.
- Any broad paper-scale claim.

## Failure Conditions Observed

- No checkpoint PLY was missing for M18/M20/M21.
- Config artifacts were present and confirmed `eval=True`, `enable_srd_gs=True`, and branch-raster settings.
- Training loss logs were unavailable, so Stage A loss progression could not be analyzed in this milestone.
- Quality failure remains inherited from M22: PSNR/Refl-PSNR are degraded for both 300-iteration variants.

## Next Step

Before any multi-scene expansion, run one bounded single-scene control that tests the now-plausible opacity/reflection-feature drift mechanism without changing the Ref-GS baseline path. A conservative next milestone is a dry-run-first config/control that freezes or strongly downweights SRD reflection-feature/specular-side updates through the short 300-iteration Stage-A window, then executes only if the generated commands and baseline compatibility checks pass.
