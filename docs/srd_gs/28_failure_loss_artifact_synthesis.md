# Milestone 28: Failure/loss artifact synthesis

Status: read-only synthesis GO; core artifact chains complete; loss/failure-panel blockers explicit; paper-scale still blocked

## Objective

Audit the completed bounded `ball` artifacts from M20/M21/M24/M25/M26 for core artifact-chain completeness, render-eval buffer completeness, loss-log availability, and failure-panel availability. This milestone does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: the completed M20/M21/M24/M25/M26 `ball` result roots have complete core train/mesh/texture/render/eval artifacts.
- Allowed claim: the audited render-eval manifests have complete referenced render fields for the checked views.
- Allowed claim: loss-log and failure-panel artifacts are absent from the audited result roots and should remain explicit blockers.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: the opacity/rendering tradeoff root cause is proven.
- Disallowed claim: rendering recovery, geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond these one-scene short-budget artifacts.

## Implementation

- Added `scripts/srd_gs/summarize_failure_loss_artifacts.py`.
- Added `tests/test_failure_loss_synthesis.py`.
- The script consumes explicit `--case LABEL=RESULT_ROOT` arguments.
- The script writes:
  - `failure_loss_artifact_matrix.csv`
  - `failure_loss_synthesis.json`
  - `failure_loss_synthesis.md`
- The script is read-only with respect to experiment artifacts and has no CUDA/runtime dependency.

## Command

```bash
python scripts/srd_gs/summarize_failure_loss_artifacts.py \
  --case M20_i300_render_gate_on=outputs/srd_gs_i300_control_m20/results/ball/full_srd_gs_branch_raster_render_gate_delay_i300_control \
  --case M21_i300_render_gate_neutral=outputs/srd_gs_i300_neutral_gate_m21/results/ball/full_srd_gs_branch_raster_render_gate_neutral_i300 \
  --case M24_reflection_freeze_i300=outputs/srd_gs_reflection_freeze_m24_i300/results/ball/full_srd_gs_branch_raster_reflection_freeze_i300 \
  --case M25_opacity_freeze_i300=outputs/srd_gs_opacity_freeze_m25_i300/results/ball/full_srd_gs_branch_raster_opacity_freeze_i300 \
  --case M26_opacity_quarter_i300=outputs/srd_gs_opacity_quarter_m26_i300/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --output_dir outputs/srd_gs_failure_loss_synthesis_m28
```

## Outputs

- `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_artifact_matrix.csv`
- `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_synthesis.json`
- `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_synthesis.md`

## Artifact Matrix

| Variant | Core chain | Render fields | Loss logs | Failure panels |
| --- | ---: | ---: | ---: | ---: |
| M20 render gate on | true | 18/18 | 0 | 0 |
| M21 render gate neutral | true | 18/18 | 0 | 0 |
| M24 reflection/specular freeze | true | 18/18 | 0 | 0 |
| M25 opacity freeze | true | 18/18 | 0 | 0 |
| M26 quarter opacity LR | true | 18/18 | 0 | 0 |

## Interpretation

The completed bounded result roots are suitable for artifact-level inspection because their core train/mesh/texture/render/eval artifacts and referenced render-eval buffers are present. They are not sufficient for a stronger root-cause or paper-scale claim because no loss logs and no failure-panel artifacts are present in the audited result roots.

This milestone narrows the next engineering need to instrumentation or explicitly approved one-scene runtime, not broad experiment expansion.

## Failure Conditions

- If the script launches training, rendering, mesh extraction, texture export, or evaluation, the milestone fails. It only reads existing files.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. No baseline runtime code is touched.
- If absent loss logs are ignored in conclusions, the milestone fails.
- If absent failure panels are ignored in conclusions, the milestone fails.
- If multi-scene or paper-scale conclusions are drawn from this audit, the milestone fails. Paper-scale remains NO-GO.

## Verification

- Focused TDD RED: `python -m unittest tests.test_failure_loss_synthesis` failed before the script existed.
- Focused TDD GREEN: `python -m unittest tests.test_failure_loss_synthesis` passed, 1 test.
- M28 summary command passed and wrote the three output artifacts under `outputs/srd_gs_failure_loss_synthesis_m28`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 29 should remain bounded. Recommended options are either adding loss/failure-panel instrumentation in dry-run-first form or running one explicitly approved single-scene opacity-scale control such as `0.125` on `ball`. Do not launch broad paper-scale experiments until the rendering/geometry tradeoff, F-score blocker, and loss/failure evidence gaps are resolved.
