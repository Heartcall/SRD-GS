# Milestone 27: Opacity-control tradeoff synthesis

Status: read-only synthesis GO; opacity tradeoff clarified; paper-scale still blocked

## Objective

Summarize the completed bounded `ball` artifacts from M20/M21/M24/M25/M26 into a single opacity-control tradeoff table. This milestone does not launch training, rendering, mesh extraction, texture export, or evaluation. It only reads existing M26 diagnosis CSV artifacts.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: existing single-scene artifacts support an opacity-control tradeoff summary.
- Allowed claim: among compared controls, M25 has the best PSNR/Refl-PSNR, M24 has the best Chamfer/leakage, and M26 has the best Normal MAE and closest activated-opacity delta to M18.
- Allowed claim: M24-M26 still leave the F-score blocker unresolved.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: the rendering regression is fully fixed.
- Disallowed claim: geometry quality is stable or improved across all metrics.
- Disallowed claim: material/PBR quality is validated.
- Disallowed claim: results generalize beyond this one scene and one short checkpoint family.

## Implementation

- Added `scripts/srd_gs/summarize_opacity_tradeoff.py`.
- Added `tests/test_opacity_tradeoff_summary.py`.
- The script consumes:
  - `render_regression/case_summary.csv`
  - `checkpoint_drift/parameter_deltas.csv`
- The script writes:
  - `opacity_tradeoff_summary.csv`
  - `opacity_tradeoff_summary.json`
  - `opacity_tradeoff_summary.md`
- The script is read-only with respect to experiment artifacts and has no CUDA/runtime dependency.

## Command

```bash
python scripts/srd_gs/summarize_opacity_tradeoff.py \
  --case_summary outputs/srd_gs_opacity_quarter_m26_i300/render_regression/case_summary.csv \
  --parameter_deltas outputs/srd_gs_opacity_quarter_m26_i300/checkpoint_drift/parameter_deltas.csv \
  --output_dir outputs/srd_gs_opacity_tradeoff_m27
```

## Outputs

- `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.csv`
- `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.json`
- `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.md`

## Metrics

| Variant | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage | Opacity delta | M27 flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M18 render-gate delay | 4.0842 | 2.7730 | 0.428561 | 0.000 | 86.4124 | 0.001707 | n/a | baseline |
| M20 render gate on | 2.9394 | 1.5411 | 0.311117 | 0.000 | 75.4314 | 0.006588 | +0.143890 | context |
| M21 render gate neutral | 2.9205 | 1.5409 | 0.300529 | 0.001 | 75.9167 | 0.003792 | +0.143303 | context |
| M24 reflection/specular freeze | 2.8750 | 1.7308 | 0.286904 | 0.000 | 74.6085 | 0.00000037 | +0.166588 | best Chamfer/leakage |
| M25 opacity freeze | 3.6522 | 2.3203 | 0.397042 | 0.000 | 73.8319 | 0.000229 | -0.072880 | best PSNR/Refl-PSNR |
| M26 quarter opacity LR | 3.1155 | 1.9098 | 0.327672 | 0.000 | 68.5402 | 0.00000763 | +0.007478 | best Normal MAE/closest opacity |

## Interpretation

M27 confirms that the current controls do not identify a single dominant setting. M25 best recovers rendering, M24 best preserves Chamfer and leakage, and M26 best improves Normal MAE while keeping activated opacity closest to M18. M24-M26 all have F-score `0.0`, so the F-score and stable-geometry blockers remain open.

The tradeoff is useful for choosing the next bounded diagnostic, but it is not a paper-scale result and does not support SRD-GS superiority.

## Failure Conditions

- If the script launches training, rendering, mesh extraction, texture export, or evaluation, the milestone fails. It only reads existing CSVs.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. No baseline runtime code is touched.
- If rendering recovery is claimed as complete, the milestone fails. Full rendering recovery remains NO-GO.
- If geometry superiority is claimed from M27, the milestone fails. F-score remains zero for M24-M26 and Chamfer/Normal MAE disagree.
- If multi-scene conclusions are drawn from this synthesis, the milestone fails. Paper-scale remains NO-GO.

## Verification

- Focused TDD RED: `python -m unittest tests.test_opacity_tradeoff_summary` failed before the script existed.
- Focused TDD GREEN: `python -m unittest tests.test_opacity_tradeoff_summary` passed, 1 test.
- M27 summary command passed and wrote the three output artifacts under `outputs/srd_gs_opacity_tradeoff_m27`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 28 should remain bounded. Recommended options are either one dry-run-first opacity-scale control such as `0.125` on `ball`, or a read-only failure-panel/loss-log synthesis if additional runtime is not approved. Do not launch broad paper-scale experiments until the rendering/geometry tradeoff and F-score blocker are resolved.
