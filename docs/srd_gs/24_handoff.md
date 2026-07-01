# SRD-GS Milestone 24 Handoff

## Current State

- Branch: `srd-gs`
- Latest completed milestone: Milestone 24
- Scope completed this run: bounded single-scene `ball` reflection/specular freeze control at 300 iterations.
- Paper-scale gate: NO-GO

## What Changed

- Added SRD optimizer LR scale flags:
  - `--srd_reflection_feature_lr_scale`
  - `--srd_specular_weight_lr_scale`
- Defaults are `1.0`, preserving existing behavior unless explicitly changed.
- Added optional runner field `train_only_args` so training-only optimizer flags do not leak into mesh, texture, render, or eval commands.
- Added M24 config:
  - `configs/srd_gs/full_srd_gs_branch_raster_reflection_freeze_i300.yaml`

## Key Outputs

- `outputs/srd_gs_reflection_freeze_m24_i300/results/ball/full_srd_gs_branch_raster_reflection_freeze_i300/eval_with_gt_mesh/metrics.json`
- `outputs/srd_gs_reflection_freeze_m24_i300/tables/ball_reflection_freeze_metric_summary.csv`
- `outputs/srd_gs_reflection_freeze_m24_i300/checkpoint_drift/parameter_deltas.csv`
- `outputs/srd_gs_reflection_freeze_m24_i300/render_regression/case_summary.csv`

## Key Findings

- M24 controlled the targeted reflection-feature/specular-weight drift.
- PSNR did not recover: M24 PSNR is `2.8750`, below M20/M21 and far below M18.
- Refl-PSNR, Chamfer, Normal MAE, and leakage improved relative to M20/M21, but F-score remains `0.0`.
- Activated opacity mean drift versus M18 is `+0.166588`, larger than M20/M21.

## Failure Boundaries

- Do not claim SRD-GS is better than Ref-GS.
- Do not claim rendering recovery.
- Do not claim PBR/material accuracy.
- Do not treat this as multi-scene evidence.
- Do not launch broad paper-scale experiments next.

## Recommended Next Milestone

Milestone 25 should be one bounded, dry-run-first opacity-drift control on `ball`. Keep it baseline-compatible and single-checkpoint. The target is to test whether controlling opacity drift can recover rendering without invalidating the existing mesh/texture/eval chain.
