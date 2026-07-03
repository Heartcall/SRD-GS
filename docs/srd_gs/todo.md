# SRD-GS Todo

## Current Rule

按照 implementation plan，每完成一个 Milestone 后停止并汇报，不自动进入下一阶段。

## Milestone Status

- Milestone 0: Baseline snapshot and static readiness - done
- Milestone 1: Baseline runtime repair and tests - done
- Milestone 2: SRD-GS representation fields - done
- Milestone 3: Renderer surface/reflection outputs - done
- Milestone 4: Loss functions and staged objective - done
- Milestone 5: Surface-only mesh extraction - done
- Milestone 6: Specular-free texture / material baking - done
- Milestone 7: Reflective asset evaluation scripts - done
- Milestone 8: Ablation configuration system - done
- Milestone 9: Minimal experiment loop - done
- Milestone 10: Paper-scale experiment expansion - done as dry-run package / paper-scale claim NO-GO
- Milestone 11: Claim-bearing metric-chain repair - partial GO for one-scene metric chain / broad paper-scale still blocked
- Milestone 12: Single-scene validation gate - conditional GO for inspection / paper-scale still blocked
- Milestone 13: GT mesh protocol revalidation - partial GO for accepted GT mesh metrics on existing ball smoke / paper-scale still blocked
- Milestone 14: Branch-map raster feature path - implementation GO / CUDA runtime verification still required
- Milestone 15: Branch-raster smoke runner - bounded runtime smoke GO / paper-scale still blocked
- Milestone 16: Single-scene three-variant comparison - bounded comparison GO / paper-scale still blocked
- Milestone 17: Branch-gate delay/ramp schedule - runtime/control plumbing GO / short-budget quality improvement NO-GO
- Milestone 18: Render-gate delay control - bounded control GO / short-budget partial metric improvement / paper-scale still blocked
- Milestone 19: Bounded Stage B/C render-gate-delay pilot - runtime GO / quality mixed / paper-scale still blocked
- Milestone 20: Same-budget render-gate-delay control - runtime GO / rendering still NO-GO / paper-scale still blocked
- Milestone 21: Neutral render-gate 300-iteration control - runtime GO / rendering still NO-GO / paper-scale still blocked
- Milestone 22: Render regression artifact diagnosis - read-only diagnosis GO / root-cause still incomplete / paper-scale still blocked
- Milestone 23: Checkpoint drift diagnosis - read-only diagnosis GO / opacity-reflection drift plausible / paper-scale still blocked
- Milestone 24: Reflection/specular freeze control - runtime GO / reflection-feature drift controlled / rendering still NO-GO / paper-scale still blocked
- Milestone 25: Opacity freeze control - runtime GO / rendering partially recovers / geometry tradeoff and paper-scale still blocked
- Milestone 26: Partial opacity LR control - runtime GO / mixed rendering-geometry tradeoff / paper-scale still blocked
- Milestone 27: Opacity-control tradeoff synthesis - read-only synthesis GO / tradeoff clarified / paper-scale still blocked
- Milestone 28: Failure/loss artifact synthesis - read-only synthesis GO / loss and failure-panel blockers explicit / paper-scale still blocked
- Milestone 29: Failure/loss instrumentation contract - dry-run instrumentation GO / runtime evidence not generated / paper-scale still blocked
- Milestone 30: Instrumented runtime preflight - bounded preflight GO / runtime launch NO-GO in current environment / paper-scale still blocked
- Milestone 31: CUDA preflight refinement - bounded diagnostic GO / runtime launch NO-GO in current environment / paper-scale still blocked
- Milestone 32: Instrumented runtime i30 - bounded single-scene runtime GO / runtime loss and failure-summary artifacts generated / paper-scale still blocked
- Milestone 33: Instrumented runtime diagnostic synthesis - read-only synthesis GO / mixed M32 diagnostic position / paper-scale still blocked
- Milestone 34: Diagnostic direction decision - read-only decision GO / eval-material artifact plumbing selected / paper-scale still blocked
- Milestone 35: Eval/material artifact plumbing audit - read-only artifact-plumbing GO / one export-diagnostic bridge candidate found / paper-scale still blocked
- Milestone 36: Highlight-leakage export diagnostic bridge - read-only export-diagnostic bridge GO / GT material accuracy still blocked / paper-scale still blocked
- Milestone 37: LPIPS / Refl-LPIPS dependency gate - read-only dependency gate GO / LPIPS compute not run / paper-scale still blocked

## Immediate Next Milestone

Do not launch broad paper-scale experiments yet. Milestone 37 confirms that LPIPS/Refl-LPIPS dependencies and M32 render-eval artifacts are ready for a future bounded compute pass, but it did not compute or write LPIPS values. The next step should be one bounded M38 action. If LPIPS compute is selected, make it dry-run-first and write separate augmented outputs without overwriting M32 source metrics. Accepted GT depth/material artifacts, material-view manifest, runtime-cost logs, Stage B/C activation, opacity scheduling, and any multi-scene runtime remain deferred unless selected as the single bounded milestone. Do not broaden into paper-scale experiments.

## Completed Milestone 37 Notes

- Added `scripts/srd_gs/gate_lpips_dependency_m37.py`.
- Added `tests/test_lpips_dependency_gate.py`.
- Generated `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.csv`.
- Generated `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json`.
- Generated `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.md`.
- M37 is read-only: it consumes M32 eval/material metrics and render-eval artifacts, probes the `ref_gs` LPIPS dependency, and does not launch training, rendering, mesh extraction, texture export, or evaluation.
- Summary result: `rendering/lpips` and `reflective_region/refl_lpips` are both `ready_for_bounded_compute`; `metrics_computed=false`; source metrics remain unchanged and unavailable.
- This milestone supports dependency/artifact readiness only. It does not support LPIPS quality values, SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, GT PBR material accuracy, or paper-scale claims.

## Completed Milestone 36 Notes

- Added `scripts/srd_gs/bridge_highlight_leakage_diagnostic_m36.py`.
- Added `tests/test_highlight_leakage_diagnostic_bridge.py`.
- Generated `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.csv`.
- Generated `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.json`.
- Generated `outputs/srd_gs_highlight_leakage_bridge_m36/highlight_leakage_diagnostic_summary.md`.
- Generated `outputs/srd_gs_highlight_leakage_bridge_m36/eval_material_augmented_metrics.csv`.
- Generated `outputs/srd_gs_highlight_leakage_bridge_m36/eval_material_augmented_metrics.json`.
- M36 is read-only: it consumes M32 eval/material and texture-export artifacts plus the M35 plan, and does not launch training, rendering, mesh extraction, texture export, or evaluation.
- Summary result: source unavailable metric count remains `10`; one separate export diagnostic is bridged; remaining metric blockers are `9`.
- This milestone supports export-diagnostic reporting only. It does not support SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, GT PBR material accuracy, or paper-scale claims.

## Completed Milestone 35 Notes

- Added `scripts/srd_gs/audit_eval_material_artifacts_m35.py`.
- Added `tests/test_eval_material_artifact_plumbing.py`.
- Generated `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_requirements.csv`.
- Generated `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_plan.json`.
- Generated `outputs/srd_gs_eval_material_plumbing_m35/eval_material_artifact_plan.md`.
- M35 is read-only: it consumes M32 metric/failure/manifest/texture artifacts and does not launch training, rendering, mesh extraction, texture export, or evaluation.
- Summary result: ten unavailable metrics remain explicit; one metric is a plumbing candidate (`texture_material/highlight_leakage_score`), two are blocked by missing LPIPS dependency, three by missing accepted GT artifacts, one by missing material-view manifest, and three by missing runtime logs.
- This milestone supports artifact-requirement classification only. It does not support SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, GT PBR material accuracy, or paper-scale claims.

## Completed Milestone 34 Notes

- Added `scripts/srd_gs/decide_diagnostic_direction_m34.py`.
- Added `tests/test_diagnostic_direction_decision.py`.
- Generated `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_matrix.csv`.
- Generated `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_decision.json`.
- Generated `outputs/srd_gs_diagnostic_direction_m34/diagnostic_direction_decision.md`.
- M34 is read-only: it consumes M33 synthesis summary and does not launch training, rendering, mesh extraction, texture export, or evaluation.
- Recommendation: `eval_material_artifact_plumbing`.
- Deferred directions: `opacity_schedule` and `stage_bc_activation`.
- This milestone supports bounded direction selection only. It does not support SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 33 Notes

- Added `scripts/srd_gs/synthesize_instrumented_runtime_m33.py`.
- Added `tests/test_instrumented_runtime_synthesis.py`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_metric_comparison.csv`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_loss_progression_summary.csv`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_unavailable_metrics.csv`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m32_manifest_summary.csv`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json`.
- Generated `outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_report.md`.
- M33 is read-only: it consumes existing M32 artifacts and prior M26 render-regression summary artifacts.
- Summary result: M32 ranks `1` for PSNR/Refl-PSNR and `7` for Chamfer/Normal MAE among compared rows; F-score remains `0.0`.
- M32 loss logging has three rows at iterations `10/20/30`, final stage `stage_a`, final total loss `0.564937`, and non-monotonic total loss progression.
- M32 failure summary still reports ten unavailable metrics.
- This milestone supports diagnostic synthesis only. It does not support SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 32 Notes

- Added a regression test for direct env-python CUDA false negatives with `conda run -n ref_gs` fallback.
- Updated `scripts/srd_gs/preflight_instrumented_runtime.py` to parse Torch probe output defensively and fall back to `conda run -n ref_gs` when direct env-python probing reports CUDA unavailable.
- Generated `outputs/srd_gs_instrumented_runtime_m32_dryrun/` as a 30-iteration `ball` dry-run command package.
- Generated host-visible preflight artifacts under `outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe/`.
- Host-visible preflight summary: instrumentation contract ready `true`, Torch CUDA available `true`, Torch device count `8`, training GPU 2 utilization `0`, workspace free `29.98` GB, process matches `0`, blockers `none`, warnings `workspace_storage_tight`, runtime GO `true`.
- Executed exactly one bounded 30-iteration `ball` runtime chain under `outputs/srd_gs_instrumented_runtime_m32_i30/`.
- Generated `loss_log.csv` with three rows at iterations 10, 20, and 30.
- Generated `eval_with_gt_mesh/failure_case_panels/failure_summary.md`.
- Generated `tables/ball_instrumented_i30_metric_summary.csv` with 17 rows.
- Key metrics: PSNR `4.342511`, Refl-PSNR `2.938904`, Chamfer `0.487437`, F-score `0.0`, Normal MAE `87.332283`, texture baking highlight leakage `0.000975`.
- Unsupported/failed metrics remain explicit: LPIPS/refl-LPIPS, GT depth, eval-level highlight leakage mask, GT albedo, GT roughness, material consistency, training time, peak memory, and render FPS.
- This milestone supports bounded runtime instrumentation evidence only. It does not support SRD-GS superiority over Ref-GS, rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 31 Notes

- Updated `scripts/srd_gs/preflight_instrumented_runtime.py` to collect Torch CUDA visibility through the explicit `ref_gs` interpreter when available.
- Added preflight fields for `torch_cuda_available`, `torch_device_count`, and `torch_training_gpu_visible`.
- Refined blocker classification to distinguish `gpu_utilization_unavailable` from `training_gpu_not_visible`.
- Extended `tests/test_instrumented_runtime_preflight.py` for the refined CUDA visibility behavior.
- Generated `outputs/srd_gs_cuda_preflight_refine_m31_dryrun/` as a 30-iteration `ball` dry-run command package.
- Generated `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.csv`.
- Generated `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.json`.
- Generated `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.md`.
- Summary result: instrumentation contract ready `true`, workspace free `30.18` GB, process matches `0`, Torch CUDA available `false`, Torch device count `0`, blocker `training_gpu_not_visible`, runtime GO `false`.
- No train/render/mesh/texture/eval runtime was launched.
- This milestone supports bounded preflight diagnostic correctness only. It does not support runtime loss progression, runtime failure-case behavior, rendering recovery, geometry superiority, PBR material accuracy, SRD-GS superiority over Ref-GS, or paper-scale claims.

## Completed Milestone 30 Notes

- Added `scripts/srd_gs/preflight_instrumented_runtime.py`.
- Added `tests/test_instrumented_runtime_preflight.py`.
- Generated `outputs/srd_gs_instrumented_runtime_m30_dryrun/` as a 30-iteration `ball` dry-run command package.
- Generated `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.csv`.
- Generated `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.json`.
- Generated `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.md`.
- Summary result: instrumentation contract ready `true`, process matches `0`, workspace free `18.38` GB, blockers `training_gpu_not_visible` and `workspace_free_below_threshold`, runtime GO `false`.
- No train/render/mesh/texture/eval runtime was launched.
- This milestone supports bounded runtime-readiness gating only. It does not support runtime loss progression, runtime failure-case behavior, rendering recovery, geometry superiority, PBR material accuracy, SRD-GS superiority over Ref-GS, or paper-scale claims.

## Completed Milestone 29 Notes

- Added opt-in `train.py` SRD loss CSV logging helpers and `--srd_loss_log_path`, defaulting to empty for baseline compatibility.
- Updated `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` to pass `--srd_loss_log_path <result_root>/loss_log.csv` only to training.
- Updated eval metric output to write `failure_case_panels/failure_summary.md` and updated M28 artifact scanning to detect failure-case panel paths.
- Added `scripts/srd_gs/inspect_failure_loss_instrumentation.py`.
- Added tests for loss CSV logging, dry-run instrumentation inspection, runner command isolation, and failure-summary output.
- Generated `outputs/srd_gs_failure_loss_instrumentation_m29_dryrun/` as a dry-run command package only.
- Generated `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.csv`.
- Generated `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.json`.
- Generated `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.md`.
- Summary result: train command available `true`, loss log in train command `true`, loss flag leaks `false`, failure-panel dir expected `true`, contract ready `true`.
- This milestone supports dry-run instrumentation readiness only. It does not support runtime loss progression, root-cause proof, rendering recovery, geometry superiority, PBR material accuracy, SRD-GS superiority over Ref-GS, or paper-scale claims.

## Completed Milestone 28 Notes

- Added `scripts/srd_gs/summarize_failure_loss_artifacts.py`.
- Added `tests/test_failure_loss_synthesis.py`.
- Generated `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_artifact_matrix.csv`.
- Generated `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_synthesis.json`.
- Generated `outputs/srd_gs_failure_loss_synthesis_m28/failure_loss_synthesis.md`.
- M28 is read-only: it consumes explicit M20/M21/M24/M25/M26 result roots and checks artifact existence/manifest references.
- All five audited cases have complete core artifact chains and `18/18` referenced render fields.
- All five audited cases have `0` detected loss-log artifacts and `0` detected failure-panel artifacts.
- This milestone supports artifact-chain completeness and explicit blocker tracking only. It does not support root-cause proof, rendering recovery, geometry superiority, PBR material accuracy, SRD-GS superiority over Ref-GS, or paper-scale claims.

## Completed Milestone 27 Notes

- Added `scripts/srd_gs/summarize_opacity_tradeoff.py`.
- Added `tests/test_opacity_tradeoff_summary.py`.
- Generated `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.csv`.
- Generated `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.json`.
- Generated `outputs/srd_gs_opacity_tradeoff_m27/opacity_tradeoff_summary.md`.
- M27 is read-only: it consumes M26's existing `render_regression/case_summary.csv` and `checkpoint_drift/parameter_deltas.csv`.
- Summary result: M25 is best for PSNR/Refl-PSNR, M24 is best for Chamfer/leakage, and M26 is best for Normal MAE and closest activated-opacity delta to M18.
- M24-M26 all have F-score `0.0`, so stable geometry improvement remains blocked.
- This milestone supports a bounded `ball` opacity-control tradeoff summary only. It does not support full rendering recovery, geometry superiority, PBR material accuracy, SRD-GS superiority over Ref-GS, or paper-scale claims.

## Completed Milestone 26 Notes

- Added `configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml`.
- The config keeps M24 reflection/specular freeze and uses `--srd_opacity_lr_scale 0.25`.
- Added tests for dry-run command isolation and ablation config discovery.
- Dry-run verified that opacity/reflection/specular LR scale flags appear in `train_command.txt` and do not appear in render/texture command files.
- Initial sandbox execution failed with `RuntimeError: No CUDA GPUs are available`; the same bounded command succeeded in the approved host-visible CUDA context.
- Executed the bounded 300-iteration `ball` chain under `outputs/srd_gs_opacity_quarter_m26_i300`.
- The run completed train, surface mesh extraction, specular-free texture export, render-eval pair generation, accepted-GT mesh evaluation, summary collection, checkpoint drift diagnosis, and render-regression diagnosis.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, `render_gate_weight=0.0`, and `gate_applied=false`.
- Metrics: PSNR `3.1155`, Refl-PSNR `1.9098`, Chamfer `0.327672`, F-score `0.0`, Normal MAE `68.5402`, baking highlight leakage `7.6283e-06`.
- Versus M18, activated opacity mean delta is `+0.007478`, reflection-feature absolute mean delta is `-0.010269`, and specular-weight mean delta is `+0.000001`.
- M26 improves Chamfer and Normal MAE versus M25, but PSNR/Refl-PSNR are worse than M25 and still below M18.
- This milestone supports an opacity LR tradeoff curve on `ball`; it does not support full rendering recovery, stable quality superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 25 Notes

- Added optimizer learning-rate scale flag `--srd_opacity_lr_scale`, defaulting to `1.0` for backward compatibility.
- Applied the scale only to the existing opacity optimizer group in `scene/gaussian_model.py`.
- Added `configs/srd_gs/full_srd_gs_branch_raster_opacity_freeze_i300.yaml`.
- The M25 config keeps the M24 reflection/specular freeze, adds `--srd_opacity_lr_scale 0.0`, and keeps neutral rendered gate modulation.
- Added tests for neutral defaults, target optimizer scaling, dry-run command isolation, and ablation config discovery.
- Dry-run verified that opacity/reflection/specular LR scale flags appear in `train_command.txt` and do not appear in render/texture command files.
- Initial sandbox execution failed with `RuntimeError: No CUDA GPUs are available`; the same bounded command succeeded in the approved host-visible CUDA context.
- Executed the bounded 300-iteration `ball` chain under `outputs/srd_gs_opacity_freeze_m25_i300`.
- The run completed train, surface mesh extraction, specular-free texture export, render-eval pair generation, accepted-GT mesh evaluation, summary collection, checkpoint drift diagnosis, and render-regression diagnosis.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, `render_gate_weight=0.0`, and `gate_applied=false`.
- Metrics: PSNR `3.6522`, Refl-PSNR `2.3203`, Chamfer `0.397042`, F-score `0.0`, Normal MAE `73.8319`, baking highlight leakage `0.000229`.
- Versus M18, activated opacity mean delta is `-0.072880`; reflection-feature absolute mean delta is `-0.010269`; specular-weight mean delta is `+0.000001`.
- Versus M18, PSNR delta is `-0.4320` and Refl-PSNR delta is `-0.4527`, which is much closer than M20/M21/M24 but still not recovered.
- This milestone supports opacity dynamics as a contributor to the rendering regression. It does not support full rendering recovery, stable quality superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 24 Notes

- Added optimizer learning-rate scale flags `--srd_reflection_feature_lr_scale` and `--srd_specular_weight_lr_scale`, both defaulting to `1.0` for backward compatibility.
- Applied the scales only to SRD reflection-feature and specular-weight optimizer groups in `scene/gaussian_model.py`.
- Extended `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` with optional `train_only_args` so optimizer-only flags affect training without leaking into mesh, texture, render, or eval commands.
- Added `configs/srd_gs/full_srd_gs_branch_raster_reflection_freeze_i300.yaml`.
- Added tests for neutral defaults, target optimizer scaling, dry-run command isolation, and ablation config discovery.
- Dry-run verified that freeze flags appear in `train_command.txt` and do not appear in render/texture command files.
- Executed the bounded 300-iteration `ball` chain under `outputs/srd_gs_reflection_freeze_m24_i300`.
- The run completed train, surface mesh extraction, specular-free texture export, render-eval pair generation, accepted-GT mesh evaluation, summary collection, checkpoint drift diagnosis, and render-regression diagnosis.
- Initial sandbox execution failed with `RuntimeError: No CUDA GPUs are available`; the same bounded command succeeded in the approved host-visible CUDA context.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, `render_gate_weight=0.0`, and `gate_applied=false`.
- Metrics: PSNR `2.8750`, Refl-PSNR `1.7308`, Chamfer `0.286904`, F-score `0.0`, Normal MAE `74.6085`, baking highlight leakage `3.6667e-07`.
- Versus M18, reflection-feature absolute mean delta is `-0.010269` and specular-weight mean delta is `+0.000001`, confirming the targeted freeze took effect.
- Versus M18, activated opacity mean delta is `+0.166588`, larger than M20/M21, so opacity drift remains a plausible blocker.
- This milestone supports optimizer-control plumbing and narrows the mechanism diagnosis. It does not support rendering recovery, stable quality superiority, PBR material accuracy, or paper-scale claims.

## Completed Milestone 23 Notes

- Added `scripts/srd_gs/diagnose_checkpoint_drift.py`.
- Added `tests/test_checkpoint_drift_diagnosis.py` with temporary M18/M20/M21-style PLY checkpoints.
- Ran a read-only checkpoint/config diagnosis over existing M18/M20/M21 `ball` model roots.
- Wrote `outputs/srd_gs_checkpoint_drift_diag_m23/checkpoint_summary.csv`, `parameter_stats.csv`, `parameter_deltas.csv`, `checkpoint_diagnosis_summary.json`, and `checkpoint_diagnosis_report.md`.
- Diagnosis flags: `no_gaussian_count_growth`, `training_loss_logs_unavailable`, and `branch_or_specular_parameter_drift_present`.
- All three checkpoints have Gaussian count `100000`; Gaussian count growth alone does not explain the rendering drop.
- M20/M21 versus M18 activated opacity mean deltas are `+0.143890` and `+0.143303`.
- M20/M21 versus M18 reflection-feature absolute mean deltas are `+0.043091` and `+0.043523`.
- Training loss logs were unavailable, so loss progression remains unverified.
- The diagnosis identifies opacity/reflection-feature drift as a plausible next control target, but does not prove complete root cause. Rendering quality, stable superiority, material/PBR, and paper-scale claims remain NO-GO.

## Completed Milestone 22 Notes

- Added `scripts/srd_gs/diagnose_render_regression.py`.
- Added `tests/test_render_regression_diagnosis.py` with temporary M18/M20/M21-style artifacts.
- Ran a read-only diagnosis over existing M18/M20/M21 `ball` result roots.
- Wrote `outputs/srd_gs_render_regression_diag_m22/case_summary.csv`, `map_stats.csv`, `pairwise_deltas.csv`, `diagnosis_summary.json`, and `diagnosis_report.md`.
- Diagnosis flags: `rendering_regression_vs_baseline`, `render_gate_activation_not_sole_cause`, and `geometry_can_improve_while_rendering_degrades`.
- M20 versus M18 deltas: PSNR `-1.1448`, Refl-PSNR `-1.2319`, Chamfer `-0.117444`, leakage `+0.004881`.
- M21 versus M18 deltas: PSNR `-1.1637`, Refl-PSNR `-1.2321`, Chamfer `-0.128032`, leakage `+0.002085`.
- The artifact diagnosis localizes the remaining issue away from rendered gate activation alone, but does not prove a full root cause. Rendering quality, stable superiority, material/PBR, and paper-scale claims remain NO-GO.

## Completed Milestone 21 Notes

- Added `configs/srd_gs/full_srd_gs_branch_raster_render_gate_neutral_i300.yaml`.
- Added tests that require the M21 config and verify dry-run commands keep diagnostic branch-gate scheduling while pushing `--srd_render_gate_start_iter` beyond the 300-iteration checkpoint.
- Executed `outputs/srd_gs_i300_neutral_gate_m21` on `ball` for 300 iterations.
- Training progress stayed in `stage_a` through iteration 300.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, and `render_gate_weight=0.0`.
- Metrics: PSNR `2.9205`, Refl-PSNR `1.5409`, Chamfer `0.300529`, F-score `0.001`, Normal MAE `75.9167`, baking highlight leakage `0.003792`.
- Pipeline/control evidence is GO. Rendering quality remains NO-GO. Geometry/material diagnostics are mixed and single-scene only. Paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 20 Notes

- Added `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_i300_control.yaml`.
- Added tests that require the M20 config and verify dry-run commands keep M19 render-gate timing while omitting accelerated Stage B/C flags.
- Executed `outputs/srd_gs_i300_control_m20` on `ball` for 300 iterations.
- Training progress stayed in `stage_a` through iteration 300.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, and `render_gate_weight=1.0`.
- Metrics: PSNR `2.9394`, Refl-PSNR `1.5411`, Chamfer `0.311117`, F-score `0.0`, Normal MAE `75.4314`, baking highlight leakage `0.006588`.
- Pipeline/control evidence is GO; rendering quality, F-score, and material/PBR claims remain NO-GO; paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 19 Notes

- Added `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_stagebc.yaml`.
- Added tests that require the Stage B/C config and verify dry-run commands include `--srd_reflection_warmup 100`, `--srd_render_gate_start_iter 200`, and `--srd_render_gate_ramp_iters 100`.
- Executed `outputs/srd_gs_stagebc_m19_i300` on `ball` for 300 iterations.
- Training progress covered `stage_a`, `stage_b`, and `stage_c`; Stage C showed non-zero `tex` loss.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, and `render_gate_weight=1.0`.
- Metrics: PSNR `2.9393`, Refl-PSNR `1.5355`, Chamfer `0.316800`, F-score `0.0`, Normal MAE `75.8534`, baking highlight leakage `0.005147`.
- Pipeline/control evidence is GO; rendering quality and F-score remain NO-GO; paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 18 Notes

- Added `utils/srd_schedule.py::compute_srd_render_gate_weight()`.
- Added `--srd_render_gate_start_iter` and `--srd_render_gate_ramp_iters` with backward-compatible `-1` defaults that reuse the branch-gate diagnostic schedule.
- `gaussian_renderer.render()` now keeps diagnostic `branch_gate_map` separate from the gate used to modulate rendered specular.
- Added `configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml`.
- Executed `outputs/srd_gs_render_gate_delay_m18_i30` on `ball` for 30 iterations.
- Manifest evidence records `policy=raster_feature_chunks`, `branch_gate_weight=1.0`, and `render_gate_weight=0.0`.
- Metrics: PSNR `4.0842`, Refl-PSNR `2.7730`, Chamfer `0.428561`, F-score `0.0`, Normal MAE `86.4124`, baking highlight leakage `0.001707`.
- Compared with M16/M17 branch-raster variants, this improves PSNR/Refl-PSNR and Chamfer while preserving low highlight leakage, but does not improve F-score or normal MAE.
- Paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 17 Notes

- Added `utils/srd_schedule.py::compute_srd_branch_gate_weight()`.
- Added `--srd_branch_gate_start_iter` and `--srd_branch_gate_ramp_iters` with backward-compatible defaults.
- `gaussian_renderer.render()` now applies an effective gate `1 + weight * (gate - 1)` when `--srd_use_branch_gate` is enabled.
- Propagated checkpoint iteration into `render_eval_pairs.py`, `export_pbr_textures.py`, and `extract_surface_mesh.py`/`GaussianExtractor`.
- Added `configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml`.
- Executed `outputs/srd_gs_branch_gate_ramp_m17_i30` on `ball` for 30 iterations.
- The schedule variant completed train/mesh/texture/render/eval and kept non-fallback `raster_feature_chunks` diagnostics.
- The schedule variant did not improve PSNR/Refl-PSNR, Chamfer, or normal MAE versus the M16 immediate branch-raster variant.
- Paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 16 Notes

- Added `scripts/srd_gs/run_single_scene_comparison.sh`.
- Updated `scripts/srd_gs/collect_results.py` to correctly infer scene/variant from `eval_with_gt_mesh/metrics.json`.
- Added `tests/test_single_scene_comparison_runner.py`.
- Executed `outputs/srd_gs_single_scene_comparison_m16_i30` on Shiny Blender Synthetic `ball` for 30 iterations.
- The branch-raster variant preserved non-fallback `raster_feature_chunks` diagnostics and completed the full train/mesh/texture/render/eval chain.
- The branch-raster variant reduced image-space baking highlight leakage but hurt PSNR/Refl-PSNR and did not improve Chamfer in this short-budget comparison.
- Paper-scale and stable quality-superiority claims remain blocked.

## Completed Milestone 15 Notes

- Added `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh`.
- The runner defaults to dry-run and writes train, mesh, texture, render-pair, and accepted-GT mesh eval commands.
- The train command includes `--eval` so test-split render metrics are available after training.
- The eval command passes `--source_path` and `--pred_geometry`, enabling accepted scene GT mesh discovery such as `ball_gt_mesh.ply`.
- Added `tests/test_branch_raster_smoke_runner.py` to lock the command contract.
- Replaced one-shot 11-channel branch-map packing in `gaussian_renderer.render()` with base-width chunked raster passes so the installed CUDA backward returns compatible gradients.
- Added runner guards for conda `libstdc++`, `depth_trunc=10.0`, and bounded texture-view export.
- Executed `outputs/srd_gs_branch_raster_smoke_m15_depth10` on `ball` for 10 iterations with non-fallback `raster_feature_chunks` manifest policy and accepted-GT mesh metrics.
- Broad paper-scale experiments remain blocked until a longer single-scene run and multi-scene validation pass.

## Completed Milestone 14 Notes

- Added `--srd_rasterize_branch_maps` with default `False`.
- Added `utils/srd_branch_maps.py` for pure tensor packing/unpacking of roughness, reflection feature, branch gate, specular weight, and transport feature channels.
- `gaussian_renderer.render()` now uses this helper when SRD-GS is enabled.
- Default/fallback behavior remains neutral unless `--srd_rasterize_branch_maps` is explicitly passed.
- Added `configs/srd_gs/full_srd_gs_branch_raster.yaml` for dry-run/runtime experiments.
- Dry-run command generation verified that the new config passes `--enable_srd_gs --srd_rasterize_branch_maps --srd_use_branch_gate`.
- Branch-map rasterization remains `Needs Runtime Verification` until CUDA render/training smoke confirms non-fallback maps and backward stability.

## Completed Milestone 13 Notes

- `utils/geometry_eval_utils.py` now discovers explicit scene GT meshes as `<scene>/<scene>_gt_mesh.ply`, with `../gt/<scene>_gt_mesh.ply` as fallback.
- `points3d.ply` remains rejected by default as dataset-reader generated initialization geometry.
- `eval_reflective_assets.py --source_path ...` now automatically enables geometry metrics when `build_geometry_protocol()` finds accepted GT mesh.
- `utils/srd_branch_policy.py` avoids importing `gaussian_renderer` for pure branch-map policy checks.
- ASCII PLY mesh loading computes vertex normals from faces locally, avoiding `open3d` for the updated GT mesh.
- New outputs live under `outputs/srd_gs_validation/ball_gt_mesh/` and `outputs/srd_gs_metric_chain/ball/*/eval_with_gt_mesh/`.
- Paper-scale gate remains `NO-GO` because `srd_branch_maps_not_rasterized` is still unresolved.

## Completed Milestone 12 Notes

- `scripts/srd_gs/inspect_single_scene_validation.py` writes a JSON/Markdown validation gate report without launching training, rendering, or evaluation.
- `tests/test_single_scene_validation_gate.py` covers the report builder, report writer, and direct script entrypoint.
- For Shiny Blender Synthetic `ball`, `eval=True` exposes 100 effective train frames and 200 effective test frames.
- `points3d.ply` is classified as `not_accepted_gt` because the Blender dataset reader can generate/store it as a random point cloud.
- SRD branch maps remain non-rasterized fallback buffers.
- `outputs/srd_gs_validation/ball/single_scene_validation_report.{json,md}` record `Paper-scale gate: NO-GO`.

## Completed Milestone 11 Notes

- `render_eval_pairs.py` exports `pred_rgb`, `gt_rgb`, SRD diagnostic buffers, auto reflective masks, and `render_eval_manifest.json`.
- `eval_reflective_assets.py` can read a render-eval pair directory and compute PSNR, SSIM, Refl-PSNR, and Refl-SSIM.
- `utils/geometry_eval_utils.py` defines a raw-coordinate geometry protocol and can compute Chamfer/F-score/normal MAE from explicit geometry paths.
- `configs/srd_gs/full_srd_gs.yaml` no longer enables `--srd_use_branch_gate` while branch maps are fallback.
- The one-scene smoke used existing 20-iteration checkpoints and `train` split with `max_views=2`.
- Ref-GS and SRD-GS now both have non-null RGB/reflective metrics in `outputs/srd_gs_metric_chain/ball/*/eval/metrics.csv`.
- Candidate-GT geometry metrics exist in `outputs/srd_gs_metric_chain/ball/*/eval_with_candidate_gt/metrics.csv` only because `--accept_dataset_points3d_as_gt` was explicitly supplied.
- Broad paper-scale experiments remain blocked.

## Completed Milestone 10 Notes

- `scripts/srd_gs/make_paper_scale_package.py` creates the required `outputs/srd_gs_experiments/` structure.
- `outputs/srd_gs_experiments/experiment_summary.md` answers the seven Milestone 10 questions.
- The current package includes completed smoke rows and planned paper-scale candidate rows.
- Claim gate is explicitly `Paper-scale claim gate: NO-GO`.
- No broad multi-scene training or paper-scale ablation execution was launched.
- `docs/srd_gs/final_implementation_summary.md` records the full implementation and evidence boundary.

## Next Engineering Tasks Before Paper-scale Runs

- Add render/GT export so rendering metrics are real, not `null`.
- Add accepted GT geometry loading and raw-coordinate geometry evaluation.
- Replace or extend the current SRD branch-map renderer fallback.
- Run one longer single-scene SRD experiment before multi-scene ablations.
- Keep stable mesh/material improvement claims blocked until reflective-region geometry/material metrics exist.

## Completed Milestone 9 Notes

- Minimal smoke scene: Shiny Blender Synthetic `ball`.
- Ref-GS baseline and SRD-GS minimal both trained for 20 iterations.
- Mesh extraction completed for Ref-GS unified mesh and SRD-GS surface-only mesh.
- Texture export completed for direct RGB baseline and SRD-GS specular-free path.
- Eval wrote `metrics.json` and `metrics.csv` for both variants.
- Summary files: `outputs/srd_gs_smoke/ball/eval/metrics_summary.csv` and `outputs/srd_gs_smoke/ball/eval/metrics_summary.md`.
- Full smoke report: `outputs/srd_gs_smoke/ball/smoke_report.md`.
- Engineering smoke passed, but rendering/geometry/material quality claims remain unsupported.

## Completed Milestone 8 Notes

- Ten ablation config files were added under `configs/srd_gs/`.
- Each config records hypothesis, removed component, expected supporting result, refuting result, and metrics to inspect first.
- `scripts/srd_gs/run_one_scene.sh` writes train/mesh/texture/eval commands and defaults to dry-run.
- `scripts/srd_gs/run_ablation_one_scene.sh` loops over `configs/srd_gs/*.yaml`.
- `scripts/srd_gs/collect_results.py` flattens `metrics.json` files into CSV.
- `scripts/srd_gs/make_tables.py` creates a Markdown table from collected metrics.
- `scripts/srd_gs/make_failure_panels.py` currently creates a failure-panel source index, not image grids.
- `naive_specular_rgb_consistency.yaml` is placeholder-only until that loss exists.
- No training or real ablation execution was launched.

## Completed Milestone 7 Notes

- `utils/metric_utils.py` implements blocked-safe metric records with `value`, `supports_hypothesis`, `higher_is_better`, and `not_available_reason`.
- Rendering metrics include PSNR, SSIM, and LPIPS placeholder status.
- Reflective-region metrics include Refl-PSNR, Refl-SSIM, and Refl-LPIPS placeholder status.
- Geometry metrics include Chamfer Distance, F-score, normal MAE, and depth error when corresponding GT inputs are supplied.
- Texture/material metrics include highlight leakage score, albedo error, roughness error, and material consistency.
- `eval_reflective_assets.py` writes `metrics.json`, `metrics.csv`, `qualitative_panels/`, and `failure_case_panels/`.
- Automatic reflective masks are saved as `reflective_mask.png` when requested.
- Real scene evaluation remains `Needs Runtime Verification`.

## Completed Milestone 6 Notes

- `utils/texture_baking.py` implements image-space material baking.
- `compute_baking_weights()` combines alpha confidence, visibility confidence, view angle weight, specular residual downweight, branch-gate downweight, and optional reprojection confidence.
- `bake_image_space_materials(..., mode="specular_free")` uses `surface_rgb` / `diffuse_rgb` and does not use final `pbr_rgb` as albedo.
- `bake_image_space_materials(..., mode="direct_rgb")` provides the comparison baseline that directly bakes final RGB.
- `export_pbr_textures.py` exports `albedo.png`, `roughness.png`, `normal.png`, `specular_weight.png`, `highlight_leakage_mask.png`, and `baking_report.json`.
- UV atlas baking and mesh-vertex material baking are not implemented.
- Real export on trained checkpoints remains `Needs Runtime Verification`.

## Completed Milestone 5 Notes

- `gaussian_renderer/__init__.py::render()` now exposes `surface_alpha`, `surface_depth`, and `surface_normal` in SRD mode.
- `utils/mesh_utils.py::GaussianExtractor` now accepts `surface_only=True` and `mesh_mode="surface"` by default.
- `GaussianExtractor` can select `surface`, `unified`, or `all_branch` mesh buffers.
- Surface-only bounded TSDF fusion masks depth where surface alpha is below `0.5`.
- `extract_surface_mesh.py` provides `surface`, `unified`, and `all_branch` mesh extraction modes.
- Diagnostic images include surface depth, surface normal, surface alpha, specular RGB, and branch gate map.
- Real extraction on trained checkpoints remains `Needs Runtime Verification`.
- No mesh-quality claim is made yet.

## Completed Milestone 4 Notes

- SRD losses are implemented in `utils/loss_utils.py`.
- `train.py` has Stage A/B/C schedule helpers.
- SRD losses are gated by `enable_srd_gs`.
- `train-NeRF.py`, `train-NeRO.py`, and `train-real.py` are not yet SRD-loss aware.
- Real SRD training smoke remains `Needs Runtime Verification`.

## Completed Milestone 3 Notes

- `render()` now returns SRD separated buffers when `pc.enable_srd_gs=True`.
- Baseline `render()` output keys remain present.
- `srd_detach_specular_geometry` and `srd_use_branch_gate` are consumed by the renderer.
- Runtime CUDA render remains `Needs Runtime Verification`.

## Completed Milestone 2 Notes

- SRD CLI flags were added with baseline-safe defaults.
- SRD branch-aware Gaussian parameters were added.
- Optimizer groups and densification/pruning plumbing were added for SRD tensors.
- PLY save/load supports old Ref-GS files through fallback defaults.
- Runtime checkpoint round-trip remains `Needs Runtime Verification`.

## Completed Milestone 1 Notes

- `utils/render_utils.py` was added to satisfy `utils/mesh_utils.py` imports.
- Baseline import tests pass under `conda run -n ref_gs`.
- Renderer contract is currently verified only by static source inspection.
- Runtime mesh extraction is still `Needs Runtime Verification`.

## Milestone 1 Original Focus

Milestone 1 should focus on baseline runtime repair and test scaffolding before SRD-GS method implementation:

- Verify whether `utils/mesh_utils.py` imports missing `utils.render_utils`.
- Add or repair minimal utility code only if required by baseline import/runtime tests.
- Add static/import tests for baseline modules.
- Run tests under `conda run -n ref_gs`.
- Keep changes minimal and avoid introducing SRD-GS method behavior before the baseline is import-clean.

## SRD-GS Implementation Targets After Baseline Repair

- Add explicit surface branch attributes for geometry, diffuse albedo, roughness, and texture/material export.
- Add reflection branch or reflection transport attributes for view-dependent specular residual.
- Modify renderer outputs to expose `surface_rgb`, `reflection_rgb`, `diffuse_albedo_map`, `roughness_map`, `normal_map`, `depth_map`, and branch masks where available.
- Add losses for photometric reconstruction, normal-depth consistency, branch separation, diffuse/material consistency, and reflection transport consistency.
- Add staged training controls to avoid optimizing reflection behavior before geometry reaches a usable state.
- Ensure mesh extraction uses surface branch attributes only.
- Add texture baking and PBR material export path with explicit highlight leakage diagnostics.

## Runtime Validation Still Required

- Baseline import validation.
- Baseline smoke training on a small scene.
- Baseline rendering verification.
- Baseline mesh extraction verification.
- SRD-GS component unit tests.
- SRD-GS smoke training.
- Reflective-region geometry/material evaluation.
