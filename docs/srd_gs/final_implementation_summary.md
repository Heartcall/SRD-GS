# SRD-GS Final Implementation Summary

## Scope

本文件总结当前分支 `srd-gs` 已完成的 SRD-GS 工程落地状态。当前目标是把 `SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping` 在 Ref-GS/SRD-GS 代码仓库中打通为可运行、可测试、可继续扩展的实验管线。

当前结论必须按证据边界解读：

- Engineering pipeline: GO for one-scene 20-iteration smoke.
- Paper-scale quality claim: NO-GO.
- Stable mesh/material improvement claim: NO-GO.

## Implemented Code

### Baseline Runtime Repair

- `utils/render_utils.py` was added to satisfy `utils/mesh_utils.py` imports.
- `save_img_u8()` supports RGB, grayscale, tensor, and numpy image export paths used by mesh and texture scripts.
- Import/runtime tests cover the repaired baseline modules.

### SRD-GS Representation

- `arguments/__init__.py` adds baseline-safe SRD-GS CLI flags.
- `scene/gaussian_model.py` adds SRD branch tensors and optimizer groups for:
  - surface diffuse/material fields;
  - reflection/specular fields;
  - branch gating and transport features.
- PLY save/load and densification/pruning plumbing were extended with backward-compatible defaults.

### Renderer Buffers

- `gaussian_renderer/__init__.py::render()` exposes SRD buffers when `enable_srd_gs=True`:
  - `surface_rgb`
  - `diffuse_rgb`
  - `specular_rgb`
  - `roughness_map`
  - `reflection_dir`
  - `branch_gate_map`
  - `specular_weight_map`
  - `transport_feature_map`
  - `reflection_residual`
  - `surface_depth`
  - `surface_normal`
  - `surface_alpha`
- SRD extra branch maps now use base-width chunked feature raster passes for the installed fixed-width CUDA rasterizer. The fallback config remains available for comparison.

### Losses and Staged Training

- `utils/loss_utils.py` implements SRD losses for branch separation, material consistency, reflection transport consistency, and geometry-related constraints.
- `train.py` adds Stage A/B/C schedule helpers and integrates SRD losses behind `enable_srd_gs`.
- The SRD training path remains gated so the baseline Ref-GS path is preserved.

### Mesh Extraction

- `utils/mesh_utils.py::GaussianExtractor` supports `surface`, `unified`, and `all_branch` mesh modes.
- `extract_surface_mesh.py` adds a CLI for surface-only mesh extraction.
- `surface` mode uses surface depth/normal/alpha buffers and masks low-alpha regions before bounded TSDF fusion.

### Texture / Material Export

- `utils/texture_baking.py` implements image-space material baking with `specular_free` and `direct_rgb` modes.
- `export_pbr_textures.py` exports:
  - `albedo.png`
  - `roughness.png`
  - `normal.png`
  - `specular_weight.png`
  - `highlight_leakage_mask.png`
  - `baking_report.json`
- UV atlas baking and mesh-vertex material baking are not implemented yet.

### Evaluation and Ablations

- `utils/metric_utils.py` implements blocked-safe metric records with explicit unavailable reasons.
- `eval_reflective_assets.py` writes `metrics.json`, `metrics.csv`, qualitative-panel directories, and failure-case directories.
- `configs/srd_gs/*.yaml` defines baseline, full SRD-GS, and ablation variants.
- `scripts/srd_gs/run_one_scene.sh` and `scripts/srd_gs/run_ablation_one_scene.sh` default to dry-run.
- `scripts/srd_gs/collect_results.py`, `make_tables.py`, and `make_failure_panels.py` aggregate available results.
- `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` generates a bounded branch-raster smoke chain with `eval=True`, test-split render-pair export, and accepted-GT mesh evaluation.
- `scripts/srd_gs/run_single_scene_comparison.sh` runs a bounded one-scene comparison across `refgs_baseline`, `full_srd_gs`, and `full_srd_gs_branch_raster`.

## Runtime Smoke Evidence

Milestone 9 ran a bounded engineering smoke:

- Dataset: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
- Variants: `refgs_baseline`, `full_srd_gs`
- Iterations: `20`
- Output root: `outputs/srd_gs_smoke`

Key artifacts:

- `outputs/srd_gs_smoke/ball/smoke_report.md`
- `outputs/srd_gs_smoke/ball/eval/metrics_summary.csv`
- `outputs/srd_gs_smoke/results/ball/refgs_baseline/mesh_unified.ply`
- `outputs/srd_gs_smoke/results/ball/full_srd_gs/mesh_surface.ply`
- `outputs/srd_gs_smoke/results/ball/refgs_baseline/pbr_textures_direct_rgb/baking_report.json`
- `outputs/srd_gs_smoke/results/ball/full_srd_gs/pbr_textures_specular_free/baking_report.json`

Interpretation:

- The smoke verifies that train -> mesh -> texture/material export -> eval scripting can execute on one scene.
- The smoke does not verify paper-scale rendering, geometry, material, or relighting quality.
- Highlight leakage is available only as an export-path diagnostic in the smoke.

## Paper-scale Expansion Package

Milestone 10 generated a dry-run paper-scale package instead of launching broad training:

- `outputs/srd_gs_experiments/experiment_summary.md`
- `outputs/srd_gs_experiments/tables/paper_scale_dry_run_matrix.csv`
- `outputs/srd_gs_experiments/tables/smoke_metrics_summary.csv`
- `outputs/srd_gs_experiments/metrics/smoke_metrics_summary.csv`
- `outputs/srd_gs_experiments/figures/smoke_highlight_leakage.png`
- `outputs/srd_gs_experiments/failure_cases/claim_gate_status.png`
- `outputs/srd_gs_experiments/raw_logs/paper_scale_gate.txt`

The package answers the seven Milestone 10 questions with explicit NO-GO / Needs Verification status where metrics are missing.

## Claim Gate

Current supported claim:

```text
SRD-GS has an implemented and tested engineering path for surface/reflection branch parameters, renderer buffers, SRD losses, surface-only mesh extraction, image-space specular-free material export, blocked-safe evaluation, ablation configuration, and a one-scene smoke loop.
SRD-GS branch/specular/transport maps can run through the installed fixed-width CUDA rasterizer by using base-width chunked feature passes; this reached a bounded 10-iteration `ball` smoke with test-split render pairs and accepted-GT mesh metrics.
The three-variant `ball` comparison at 30 iterations runs end-to-end and records baseline, fallback SRD-GS, and branch-raster SRD-GS metrics in one summary table.
Opt-in branch-gate delay/ramp scheduling is implemented and verified through the same train/render/export/eval chain.
Render-gate delay decouples diagnostic branch-gate rasterization from rendered specular modulation and is verified on a bounded 30-iteration `ball` run.
The render-gate-delay branch-raster path can execute Stage B/C losses in a bounded 300-iteration `ball` pilot with non-fallback diagnostics, but the quality signal is mixed.
A same-budget 300-iteration Stage-A control keeps M19's final rendered gate state and shows similar rendering degradation, suggesting accelerated Stage B/C is not the sole cause.
A neutral-render-gate 300-iteration Stage-A control keeps diagnostics active and improves Chamfer/F-score/leakage over M20, but PSNR/Refl-PSNR still do not recover.
A read-only M18/M20/M21 artifact diagnosis confirms the 300-iteration rendering regression persists even when `render_gate_weight=0.0`, so rendered gate activation is not the sole cause; the complete root cause remains unresolved.
A read-only M18/M20/M21 checkpoint diagnosis shows Gaussian count is unchanged while activated opacity and reflection-feature magnitude drift upward in the 300-iteration checkpoints, making opacity/reflection-feature drift a plausible next control target.
A bounded 300-iteration reflection/specular freeze control suppresses reflection-feature/specular-weight drift and completes the train/mesh/texture/render/eval chain, but PSNR still does not recover and activated opacity drift remains larger than M18.
A bounded 300-iteration opacity freeze control suppresses activated-opacity drift and partially recovers PSNR/Refl-PSNR versus M20/M21/M24, but it still does not match M18 rendering and introduces a geometry tradeoff versus M20/M21/M24.
A bounded 300-iteration quarter-opacity-LR control keeps activated opacity near M18 and improves Chamfer/Normal MAE versus full opacity freeze, but gives up part of the rendering recovery and still leaves F-score at zero.
A read-only opacity-control synthesis over completed `ball` artifacts shows M25 is best for PSNR/Refl-PSNR, M24 is best for Chamfer/leakage, and M26 is best for Normal MAE and closest activated-opacity delta to M18; this clarifies a tradeoff but does not resolve F-score or paper-scale blockers.
A read-only failure/loss artifact synthesis confirms M20/M21/M24/M25/M26 have complete audited core artifact chains and render-eval field references, but no detected loss logs or failure-panel artifacts; those remain explicit blockers for root-cause and claim-bearing analysis.
A dry-run failure/loss instrumentation contract now passes a train-only SRD loss CSV path through the bounded runner and makes eval outputs write failure-summary artifacts; this removes an instrumentation blocker for future bounded runs but does not generate runtime loss curves or quality evidence.
A bounded M30 runtime preflight prepares a 30-iteration instrumented `ball` command package and blocks launch when GPU visibility/storage gates are not acceptable; this supports readiness gating only, not runtime quality evidence.
A bounded M31 CUDA-preflight refinement records Torch CUDA visibility explicitly and confirms storage/process gates pass, but runtime launch remains blocked because the `ref_gs` runtime cannot see CUDA devices.
A bounded M32 single-scene 30-iteration `ball` instrumented run completes the train/mesh/texture/render-eval/accepted-GT-eval chain and produces `loss_log.csv`, `failure_summary.md`, and a 17-row metric summary, but F-score remains zero and several metrics remain unavailable.
A read-only M33 diagnostic synthesis positions M32 against prior short-budget controls: PSNR/Refl-PSNR rank best in the diagnostic table, but Chamfer/Normal MAE rank worst, F-score remains zero, loss is non-monotonic over three rows, and ten metrics remain unavailable.
A read-only M34 direction decision selects eval/material artifact plumbing as the next bounded direction because unavailable metrics and evaluation-context blockers dominate the current evidence gap; Stage B/C activation and opacity schedule remain deferred runtime directions.
A read-only M35 eval/material artifact plumbing audit maps the ten unavailable M32 metrics to blocker classes and identifies one future plumbing candidate: surfacing texture-export highlight-leakage artifacts as an explicitly labeled export diagnostic, not as GT PBR material accuracy.
```

Current unsupported claims:

```text
SRD-GS improves reflective-region normal MAE.
SRD-GS improves reflective-region mesh Chamfer / F-score.
SRD-GS preserves Ref-GS rendering PSNR/SSIM/LPIPS at paper scale.
SRD-GS improves relighting or PBR material accuracy.
SRD-GS has stable multi-scene mesh/material superiority.
```

## Critical Blockers Before Paper Claims

1. Test-split render/GT export requires checkpoints trained or regenerated with `eval=True`; the M16-M18 bounded runs satisfy this on `ball`, while older smoke metric-chain outputs may not.
2. Accepted GT mesh geometry is now available for Shiny Blender Synthetic `ball` through `ball_gt_mesh.ply`, and the metric chain runs against it. The current accepted-GT metrics are still single-scene short-budget evidence, not paper-scale evidence.
3. SRD branch-map rasterization now has an explicit feature-flagged chunked raster path and bounded `ball` smoke evidence. It still needs a longer single-scene run and multi-scene validation before paper-scale claims.
4. Current texture/material baking is image-space only; UV atlas or mesh-bound material baking is not implemented.
5. Ablation configs exist, but paper-scale ablation runs have not been executed.
6. The current comparison evidence is still one scene and a short 30-iteration budget.
7. The tested branch-gate ramp did not improve the immediate branch-raster tradeoff at 30 iterations.
8. Render-gate delay improves PSNR/Refl-PSNR and Chamfer over M16/M17 branch-raster variants at 30 iterations, but F-score remains zero and normal MAE is not improved.
9. The accelerated Stage B/C pilot improves Chamfer and Normal MAE over M18, but PSNR/Refl-PSNR degrade, F-score remains zero, and baking leakage increases.
10. The same-budget Stage-A control closely matches M19's rendering degradation, so the next blocker is rendered gate activation or 300-iteration dynamics rather than Stage B/C acceleration alone.
11. The neutral-render-gate control shows rendered gate activation is not the sole blocker; the remaining rendering drop likely needs artifact-level diagnosis of checkpoint dynamics, specular-weight behavior, branch diagnostics, or evaluation-mask effects.
12. The M22 artifact diagnosis narrows the issue away from rendered gate activation alone and gross branch-mask coverage changes, but it does not yet distinguish checkpoint-length optimization dynamics from learned diffuse/specular parameter drift.
13. The M23 checkpoint diagnosis shows all compared checkpoints have `100000` Gaussians, while M20/M21 opacity and reflection-feature statistics drift from M18; training loss logs are unavailable, so causality remains unproven.
14. The M24 reflection/specular freeze control suppresses the targeted reflection-feature/specular-weight drift but does not recover PSNR; activated opacity drift remains a plausible next blocker.
15. The M25 opacity freeze control improves PSNR/Refl-PSNR and controls opacity drift, but Chamfer worsens versus M20/M21/M24 and F-score remains zero; a partial opacity schedule is needed before broader experiments.
16. The M26 quarter-opacity-LR control improves Chamfer and Normal MAE versus full opacity freeze, but reduces PSNR/Refl-PSNR recovery; the next blocker is choosing or summarizing an opacity-control tradeoff, not paper-scale expansion.
17. The M27 synthesis confirms no single completed opacity-control setting resolves rendering, Chamfer, Normal MAE, and F-score together; M24-M26 keep F-score at zero and remain single-scene short-budget evidence.
18. The M28 artifact synthesis confirms the completed result roots are auditable, but loss progression and failure-panel evidence are absent; the opacity/rendering tradeoff root cause remains unproven.
19. The M29 instrumentation contract makes future bounded runs capable of writing result-root `loss_log.csv` and `failure_case_panels/failure_summary.md`, but runtime loss/failure evidence has not yet been generated.
20. The M30 preflight confirms the bounded instrumented command package is ready, but runtime launch is blocked in the current environment by GPU visibility and workspace free-space gates.
21. The M31 refined preflight confirms workspace/process gates pass, but the `ref_gs` runtime reports CUDA unavailable and zero CUDA devices, so the bounded instrumented run remains blocked.
22. The M32 bounded runtime removes the missing loss/failure-artifact blocker for one short `ball` run, but the resulting evidence remains non-comparative, short-budget, and quality-limited: F-score is `0.0`, SSIM is negative, and LPIPS/material/runtime metrics remain unavailable.
23. The M33 diagnostic synthesis confirms M32's rendering metric improvement is paired with worse geometry metrics and persistent unavailable metrics; the next step is a bounded diagnostic choice, not paper-scale expansion.
24. The M34 direction decision narrows the next step to eval/material artifact plumbing; it does not provide new runtime evidence or quality improvement.
25. The M35 eval/material artifact audit confirms that nine of ten unavailable metrics remain blocked by missing dependencies, accepted GT artifacts, material-view manifests, or runtime logs. The only immediate plumbing candidate is highlight-leakage export diagnostics, which must not be promoted to GT material accuracy.

## Recommended Next Engineering Tasks

1. Regenerate one-scene Ref-GS and SRD-GS checkpoints with `eval=True` before test-split render metrics are used.
2. Expand the accepted GT mesh protocol scene-by-scene; keep raw-coordinate metrics primary and reject generated `points3d.ply` by default.
3. Keep the next step bounded: implement a read-only/dry-run-first highlight-leakage export diagnostic bridge into eval/material summaries before any additional one-scene runtime.
4. Preserve `--enable_srd_gs=False` behavior and avoid changing Ref-GS baseline training/rendering.
5. If another bounded control is executed later, keep it to `ball` and one short checkpoint before any broader claims.
6. Only after the validation gates pass, launch multi-scene ablations from `configs/srd_gs/*.yaml`.

## Verification Status

Fresh verification through Milestone 35:

- `conda run -n ref_gs python -m unittest tests.test_srd_branch_raster_features tests.test_srd_gaussian_model_static tests.test_srd_branch_map_fallback_policy tests.test_srd_render_contract_static`: passed, 16 tests.
- `conda run -n ref_gs python -m unittest tests.test_ablation_system_contract`: passed, 3 tests.
- `scripts/srd_gs/run_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster.yaml --source_path /tmp/srd_dummy_scene --output_root /tmp/srd_branch_raster_dryrun --scene_name dummy --iterations 10`: passed as dry-run.
- `python -m unittest tests.test_branch_raster_smoke_runner`: passed, 1 test.
- `conda run -n ref_gs python -m unittest tests.test_render_eval_pairs_static tests.test_srd_branch_raster_features tests.test_srd_render_contract_static`: passed, 12 tests.
- `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_branch_raster_smoke_m15_depth10 --scene_name ball --iterations 10 --max_mesh_views 4 --depth_trunc 10.0 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_single_scene_comparison_runner tests.test_ablation_system_contract`: passed, 4 tests.
- `bash scripts/srd_gs/run_single_scene_comparison.sh --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_single_scene_comparison_m16_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_srd_branch_gate_schedule tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 9 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_branch_gate_ramp_m17_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_srd_branch_gate_schedule tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 12 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_render_gate_delay_m18_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 7 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_stagebc.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_stagebc_m19_i300 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 8 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_i300_control.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_i300_control_m20 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 9 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_render_gate_neutral_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_i300_neutral_gate_m21 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python -m unittest tests.test_render_regression_diagnosis`: passed, 1 test.
- `python scripts/srd_gs/diagnose_render_regression.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --output_dir outputs/srd_gs_render_regression_diag_m22`: passed.
- `python -m unittest tests.test_checkpoint_drift_diagnosis`: passed, 1 test.
- `python scripts/srd_gs/diagnose_checkpoint_drift.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --output_dir outputs/srd_gs_checkpoint_drift_diag_m23`: passed.
- `python -m unittest tests.test_srd_gaussian_model_static tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 17 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_reflection_freeze_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_reflection_freeze_m24_i300 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed after host-visible CUDA approval.
- `python scripts/srd_gs/diagnose_checkpoint_drift.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --output_dir outputs/srd_gs_reflection_freeze_m24_i300/checkpoint_drift`: passed.
- `python scripts/srd_gs/diagnose_render_regression.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --output_dir outputs/srd_gs_reflection_freeze_m24_i300/render_regression`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 76 tests.
- `conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py tests/test_srd_gaussian_model_static.py tests/test_branch_raster_smoke_runner.py tests/test_ablation_system_contract.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M24 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_srd_gaussian_model_static tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 18 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_freeze_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_opacity_freeze_m25_i300 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed after host-visible CUDA approval.
- `python scripts/srd_gs/collect_results.py --results_root outputs/srd_gs_opacity_freeze_m25_i300/results --output_csv outputs/srd_gs_opacity_freeze_m25_i300/tables/ball_opacity_freeze_metric_summary.csv`: passed, 17 rows.
- `python scripts/srd_gs/diagnose_checkpoint_drift.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --case M25_opacity_freeze_i300=... --output_dir outputs/srd_gs_opacity_freeze_m25_i300/checkpoint_drift`: passed.
- `python scripts/srd_gs/diagnose_render_regression.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --case M25_opacity_freeze_i300=... --output_dir outputs/srd_gs_opacity_freeze_m25_i300/render_regression`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 77 tests.
- `conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py tests/test_srd_gaussian_model_static.py tests/test_branch_raster_smoke_runner.py tests/test_ablation_system_contract.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M25 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_branch_raster_smoke_runner tests.test_ablation_system_contract`: passed, 12 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_opacity_quarter_m26_i300 --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed after host-visible CUDA approval.
- `python scripts/srd_gs/collect_results.py --results_root outputs/srd_gs_opacity_quarter_m26_i300/results --output_csv outputs/srd_gs_opacity_quarter_m26_i300/tables/ball_opacity_quarter_metric_summary.csv`: passed, 17 rows.
- `python scripts/srd_gs/diagnose_checkpoint_drift.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --case M25_opacity_freeze_i300=... --case M26_opacity_quarter_i300=... --output_dir outputs/srd_gs_opacity_quarter_m26_i300/checkpoint_drift`: passed.
- `python scripts/srd_gs/diagnose_render_regression.py --case M18_render_gate_delay_i30=... --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --case M25_opacity_freeze_i300=... --case M26_opacity_quarter_i300=... --output_dir outputs/srd_gs_opacity_quarter_m26_i300/render_regression`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 78 tests.
- `conda run -n ref_gs python -m py_compile tests/test_branch_raster_smoke_runner.py tests/test_ablation_system_contract.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M26 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_opacity_tradeoff_summary`: passed, 1 test.
- `python scripts/srd_gs/summarize_opacity_tradeoff.py --case_summary outputs/srd_gs_opacity_quarter_m26_i300/render_regression/case_summary.csv --parameter_deltas outputs/srd_gs_opacity_quarter_m26_i300/checkpoint_drift/parameter_deltas.csv --output_dir outputs/srd_gs_opacity_tradeoff_m27`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 79 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/summarize_opacity_tradeoff.py tests/test_opacity_tradeoff_summary.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M27 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_failure_loss_synthesis`: passed, 1 test.
- `python scripts/srd_gs/summarize_failure_loss_artifacts.py --case M20_i300_render_gate_on=... --case M21_i300_render_gate_neutral=... --case M24_reflection_freeze_i300=... --case M25_opacity_freeze_i300=... --case M26_opacity_quarter_i300=... --output_dir outputs/srd_gs_failure_loss_synthesis_m28`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 80 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/summarize_failure_loss_artifacts.py tests/test_failure_loss_synthesis.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M28 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `conda run -n ref_gs python -m unittest tests.test_srd_loss_logging tests.test_failure_loss_instrumentation tests.test_branch_raster_smoke_runner tests.test_reflective_asset_metrics`: passed, 15 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_failure_loss_instrumentation_m29_dryrun --scene_name ball --iterations 300 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000`: passed as dry-run.
- `python scripts/srd_gs/inspect_failure_loss_instrumentation.py --result_root outputs/srd_gs_failure_loss_instrumentation_m29_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 --label M29_opacity_quarter_dryrun --output_dir outputs/srd_gs_failure_loss_instrumentation_m29`: passed.
- `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight`: passed, 3 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_instrumented_runtime_m30_dryrun --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000`: passed as dry-run.
- `python scripts/srd_gs/preflight_instrumented_runtime.py --result_root outputs/srd_gs_instrumented_runtime_m30_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 --label M30_instrumented_ball_i30_preflight --output_dir outputs/srd_gs_instrumented_runtime_preflight_m30 --training_gpu_index 2 --max_gpu_utilization_percent 50 --workspace_path . --min_workspace_free_gb 25`: passed and returned `runtime_go=false`.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 85 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/preflight_instrumented_runtime.py tests/test_instrumented_runtime_preflight.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M30 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight`: passed, 5 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_cuda_preflight_refine_m31_dryrun --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000`: passed as dry-run.
- `python scripts/srd_gs/preflight_instrumented_runtime.py --result_root outputs/srd_gs_cuda_preflight_refine_m31_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 --label M31_cuda_preflight_refine --output_dir outputs/srd_gs_cuda_preflight_refine_m31 --training_gpu_index 2 --max_gpu_utilization_percent 50 --workspace_path . --min_workspace_free_gb 25`: passed and returned `runtime_go=false`.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 87 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/preflight_instrumented_runtime.py tests/test_instrumented_runtime_preflight.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M31 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight`: passed, 6 tests.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_instrumented_runtime_m32_dryrun --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000`: passed as dry-run.
- `conda run -n ref_gs python scripts/srd_gs/preflight_instrumented_runtime.py --result_root outputs/srd_gs_instrumented_runtime_m32_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 --label M32_conda_run_preflight_probe --output_dir outputs/srd_gs_instrumented_runtime_preflight_m32_conda_probe --training_gpu_index 2 --max_gpu_utilization_percent 50 --workspace_path . --min_workspace_free_gb 25`: passed and returned `runtime_go=true`.
- `bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_root outputs/srd_gs_instrumented_runtime_m32_i30 --scene_name ball --iterations 30 --max_mesh_views 4 --depth_trunc 10.0 --max_texture_views 2 --max_eval_views 2 --geometry_sample_count 1000 --execute`: passed.
- `python scripts/srd_gs/collect_results.py --results_root outputs/srd_gs_instrumented_runtime_m32_i30/results --output_csv outputs/srd_gs_instrumented_runtime_m32_i30/tables/ball_instrumented_i30_metric_summary.csv`: passed, 17 rows.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 88 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/preflight_instrumented_runtime.py tests/test_instrumented_runtime_preflight.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M32 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_instrumented_runtime_synthesis`: passed, 1 test.
- `python scripts/srd_gs/synthesize_instrumented_runtime_m33.py --prior_case_summary outputs/srd_gs_opacity_quarter_m26_i300/render_regression/case_summary.csv --m32_metrics outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv --m32_loss_log outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/loss_log.csv --m32_manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json --m32_failure_summary outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md --output_dir outputs/srd_gs_m32_diagnostic_synthesis_m33`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 89 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/synthesize_instrumented_runtime_m33.py tests/test_instrumented_runtime_synthesis.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M33 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_diagnostic_direction_decision`: passed, 1 test.
- `python scripts/srd_gs/decide_diagnostic_direction_m34.py --m33_summary outputs/srd_gs_m32_diagnostic_synthesis_m33/m33_synthesis_summary.json --output_dir outputs/srd_gs_diagnostic_direction_m34`: passed.
- `conda run -n ref_gs python -m unittest discover -s tests`: passed, 90 tests.
- `conda run -n ref_gs python -m py_compile scripts/srd_gs/decide_diagnostic_direction_m34.py tests/test_diagnostic_direction_decision.py`: passed.
- `bash -n scripts/srd_gs/*.sh`: passed.
- `git diff --check`: passed.
- M34 artifact existence checks: passed.
- Prohibited process scan for train/mesh/texture/render/eval scripts: no residual processes.
- `python -m unittest tests.test_eval_material_artifact_plumbing`: passed, 1 test.
- `python scripts/srd_gs/audit_eval_material_artifacts_m35.py --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv --failure_summary outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/failure_summary.md --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json --result_root outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" --output_dir outputs/srd_gs_eval_material_plumbing_m35`: passed.
