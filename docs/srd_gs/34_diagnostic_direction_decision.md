# Milestone 34: Diagnostic direction decision

Status: read-only decision GO; eval/material artifact plumbing selected; paper-scale still blocked

## Objective

Choose one bounded diagnostic direction after M33 clarified that M32 has improved PSNR/Refl-PSNR but worse geometry metrics, F-score `0.0`, non-monotonic short loss logging, and ten unavailable metrics. This milestone does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: existing M33 evidence supports selecting the next bounded diagnostic direction.
- Allowed claim: `eval_material_artifact_plumbing` is the least runtime-expanding next direction because unavailable metrics dominate the blocker list.
- Allowed claim: `stage_bc_activation` and `opacity_schedule` remain deferred runtime directions.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond this one-scene diagnostic chain.

## Implementation

- Added `scripts/srd_gs/decide_diagnostic_direction_m34.py`.
- Added `tests/test_diagnostic_direction_decision.py`.
- The script consumes `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json`.
- The script writes:
  - `diagnostic_direction_matrix.csv`
  - `diagnostic_direction_decision.json`
  - `diagnostic_direction_decision.md`

## Command

```bash
python scripts/srd_gs/decide_diagnostic_direction_m34.py \
  --m33_summary outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json \
  --output_dir outputs/srd_gs_diagnostic_direction_m34
```

## Outputs

- `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_matrix.csv`
- `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_decision.json`
- `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_decision.md`

## Decision Matrix

| Direction | Score | Scope | Reasons | Blockers |
| --- | ---: | --- | --- | --- |
| eval/material artifact plumbing | 6 | read-only or dry-run-first | 10 unavailable metrics; quality tradeoff needs metric plumbing; F-score needs eval context | does not test training dynamics |
| opacity schedule | 3 | single-scene runtime or dry-run | render/geometry tradeoff; F-score blocker | requires runtime; may repeat M25/M26 tradeoff |
| Stage B/C activation | 3 | single-scene runtime or dry-run | geometry blocker; short/unstable loss signal | requires runtime; does not reduce unavailable metrics first |

## Interpretation

M34 selects `eval_material_artifact_plumbing` as the next bounded direction. The selection is not a quality claim. It is a scope decision: before another runtime control, the metric chain should reduce the explicit unavailable-metric blockers that prevent stronger interpretation of existing short-budget evidence.

Stage B/C activation and opacity schedule remain legitimate future diagnostics, but both require runtime and do not directly reduce the ten unavailable metrics from M33.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, or evaluation, it fails. It only reads M33 summary artifacts.
- If the chosen direction is treated as evidence of SRD-GS superiority, it fails.
- If Stage B/C or opacity schedule is silently launched in the same milestone, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `python -m unittest tests.test_diagnostic_direction_decision` failed before the script existed.
- Focused TDD GREEN: `python -m unittest tests.test_diagnostic_direction_decision` passed, 1 test.
- M34 decision command passed and wrote the three output artifacts under `outputs/srd_gs_diagnostic_direction_m34`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 35 should implement the selected `eval_material_artifact_plumbing` direction as a read-only or dry-run-first bounded milestone. Do not launch broad paper-scale experiments.
