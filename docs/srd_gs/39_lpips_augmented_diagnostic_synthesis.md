# Milestone 39: LPIPS augmented diagnostic synthesis

Status: read-only diagnostic synthesis GO; quality interpretation still mixed; paper-scale still blocked

## Objective

Implement the M38-recommended bounded synthesis that integrates M38 LPIPS/Refl-LPIPS values with M33 diagnostic position, M36 highlight-leakage export diagnostic, and M37 LPIPS dependency-gate evidence.

This milestone is read-only with respect to source experiment artifacts. It does not launch training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: M39 integrates M33/M36/M37/M38 diagnostic evidence into separate M39 summary artifacts.
- Allowed claim: bounded LPIPS/Refl-LPIPS values are now available for the existing two-frame M32 `ball` artifact set.
- Allowed claim: the integrated diagnostic position remains mixed or unresolved: M32 ranks first for PSNR/Refl-PSNR in the short-budget diagnostic table, but Chamfer/Normal MAE rank worst, F-score remains zero, and LPIPS/Refl-LPIPS are high.
- Allowed claim: M36 highlight leakage remains an export diagnostic, not accepted GT material accuracy.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, GT PBR material accuracy, or paper-scale quality is validated.
- Disallowed claim: the two-frame LPIPS values generalize beyond this bounded diagnostic artifact set.
- Disallowed claim: remaining accepted GT depth/material, material-view, or runtime-cost blockers are solved.

## Implementation

- Added `scripts/srd_gs/synthesize_lpips_augmented_diagnostics_m39.py`.
- Added `tests/test_lpips_augmented_diagnostic_synthesis.py`.
- The script consumes:
  - M33 `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json`
  - M33 `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_metric_comparison.csv`
  - M36 `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.json`
  - M36 `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.csv`
  - M37 `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json`
  - M38 `outputs/srd_gs_lpips_compute_m38/lpips_compute_summary.json`
  - M38 `outputs/srd_gs_lpips_compute_m38/lpips_augmented_metrics.csv`
- The script writes:
  - `lpips_augmented_diagnostic_summary.csv`
  - `lpips_augmented_diagnostic_summary.json`
  - `lpips_augmented_diagnostic_report.md`
  - `m39_metric_position.csv`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/synthesize_lpips_augmented_diagnostics_m39.py \
  --m33_summary outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json \
  --m33_metric_comparison outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_metric_comparison.csv \
  --m36_summary outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.json \
  --m36_diagnostic_csv outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.csv \
  --m37_gate_json outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json \
  --m38_summary outputs/srd_gs_lpips_compute_m38/lpips_compute_summary.json \
  --m38_augmented_metrics outputs/srd_gs_lpips_compute_m38/lpips_augmented_metrics.csv \
  --output_dir outputs/srd_gs_lpips_augmented_diagnostic_m39
```

## Outputs

- `outputs/srd_gs_lpips_augmented_diagnostic_m39/lpips_augmented_diagnostic_summary.csv`
- `outputs/srd_gs_lpips_augmented_diagnostic_m39/lpips_augmented_diagnostic_summary.json`
- `outputs/srd_gs_lpips_augmented_diagnostic_m39/lpips_augmented_diagnostic_report.md`
- `outputs/srd_gs_lpips_augmented_diagnostic_m39/m39_metric_position.csv`

## Key Metrics

| Metric | Value |
| --- | ---: |
| LPIPS | 0.9455429017543793 |
| Refl-LPIPS | 0.8390642702579498 |
| Highlight leakage export diagnostic | 0.000975149334408 |
| F-score | 0.0 |
| M32 PSNR rank in diagnostic table | 1 |
| M32 Refl-PSNR rank in diagnostic table | 1 |
| M32 Chamfer rank in diagnostic table | 7 |
| M32 Normal MAE rank in diagnostic table | 7 |

## Interpretation

M39 improves metric availability and diagnostic traceability, but it does not improve the scientific claim boundary. The integrated evidence remains mixed: M32's PSNR/Refl-PSNR position is favorable within a short-budget diagnostic table, while LPIPS/Refl-LPIPS are high, F-score remains zero, and geometry ranks are weak. The highlight-leakage value is explicitly an export diagnostic rather than accepted GT PBR material accuracy.

The paper-scale gate remains NO-GO.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, evaluation, broad evaluation, or multi-scene experiments, it fails.
- If LPIPS/Refl-LPIPS availability is treated as rendering recovery or SRD-GS superiority, it fails.
- If M36 highlight leakage is treated as GT PBR material accuracy, it fails.
- If F-score zero, high LPIPS/Refl-LPIPS, weak geometry ranks, or remaining unavailable metrics are ignored, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_lpips_augmented_diagnostic_synthesis` failed before `synthesize_lpips_augmented_diagnostics_m39.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_lpips_augmented_diagnostic_synthesis` passed, 1 test.
- M39 synthesis command passed and wrote four output artifacts under `outputs/srd_gs_lpips_augmented_diagnostic_m39`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 40 should remain bounded and choose one remaining unavailable-metric contract: accepted GT depth/material artifact protocol, material-view manifest definition, or runtime-cost logging. Do not launch broad paper-scale experiments.
