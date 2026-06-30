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

## Immediate Next Milestone

Do not launch broad paper-scale experiments yet. Milestone 11 repaired the one-scene render/GT metric chain, but branch-map rasterization remains fallback and candidate GT geometry still needs dataset/protocol verification.

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
