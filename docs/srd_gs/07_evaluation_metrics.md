# SRD-GS Reflective Asset Evaluation Metrics

## Scope

本文件记录 Milestone 7。当前阶段实现 reflective asset evaluation 的最小离线脚本，把 SRD-GS 的 rendering、reflective-region、geometry、texture/material、runtime claim 转换成结构化 metric records。未运行真实场景评估，未生成论文结果，未修改训练或 renderer。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Added

- `utils/metric_utils.py`
- `eval_reflective_assets.py`
- `scripts/srd_gs/run_eval_one_scene.sh`
- `tests/test_reflective_asset_metrics.py`
- `docs/srd_gs/07_evaluation_metrics.md`

## Metric Record Contract

Every metric is written as a dictionary with:

- `category`
- `name`
- `value`
- `supports_hypothesis`
- `higher_is_better`
- `not_available_reason`

If an input or GT reference is unavailable, the metric value is `null` in JSON and `not_available_reason` is populated. This is required to avoid fabricating geometry/material metrics.

## Supported Metrics

### Rendering

Implemented in `utils/metric_utils.py::compute_reflective_asset_metrics()`:

- `psnr`
- `ssim`
- `lpips`

`lpips` is reported as `null` with `not_available_reason="lpips_not_available"` unless an external LPIPS value is explicitly supplied. The current implementation does not download LPIPS weights.

### Reflective Region

Implemented in `compute_reflective_asset_metrics()`:

- `refl_psnr`
- `refl_ssim`
- `refl_lpips`

If a reflective mask is missing, reflective-region metrics are `null` with `reflective_mask_not_available`. If an automatic mask is requested by `eval_reflective_assets.py --auto_reflective_mask`, the script saves `reflective_mask.png` and records its source.

### Geometry

Implemented in `utils/metric_utils.py::compute_geometry_metrics()`:

- `chamfer_distance`, if predicted and GT point sets are supplied.
- `f_score`, if predicted and GT point sets are supplied.
- `normal_mae`, if predicted and GT normals are supplied.
- `depth_error`, if predicted and GT depth are supplied.

If GT geometry, normal, or depth is absent, the metric is `null` with a specific `not_available_reason`. Raw-coordinate evaluation is assumed; no ICP or similarity alignment is applied.

### Texture / Material

Implemented in `utils/metric_utils.py::compute_texture_material_metrics()`:

- `highlight_leakage_score`
- `albedo_error`
- `roughness_error`
- `material_consistency`

GT albedo and roughness are optional. If missing, the error metrics are `null` with explicit reasons.

### Runtime

Implemented in `utils/metric_utils.py::compute_runtime_metrics()`:

- `training_time`
- `peak_memory`
- `render_fps`

These values are only recorded if supplied to the evaluation script.

## Output Files

Implemented in `utils/metric_utils.py::write_metrics_outputs()`:

- `metrics.json`
- `metrics.csv`
- `qualitative_panels/`
- `failure_case_panels/`
- `reflective_mask.png`, when a mask is provided or automatically estimated.

## Evaluation Script

Added `eval_reflective_assets.py`.

Important arguments:

- `--pred_rgb`
- `--gt_rgb`
- `--reflective_mask`
- `--auto_reflective_mask`
- `--mask_threshold`
- `--material_report`
- `--highlight_leakage_mask`
- `--output_dir`
- `--training_time`
- `--peak_memory`
- `--render_fps`

The script is intentionally artifact-based. It evaluates saved images/reports and does not launch training or rendering.

## One-scene Runner

Added `scripts/srd_gs/run_eval_one_scene.sh`:

```bash
scripts/srd_gs/run_eval_one_scene.sh <pred_rgb.png> <gt_rgb.png> <output_dir> [reflective_mask.png]
```

If no reflective mask is supplied, it uses `--auto_reflective_mask` and saves the resulting mask visualization.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_reflective_asset_metrics
conda run -n ref_gs python -m unittest discover -s tests
conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py utils/render_utils.py utils/texture_baking.py utils/metric_utils.py extract_surface_mesh.py export_pbr_textures.py eval_reflective_assets.py
bash -n scripts/srd_gs/run_eval_one_scene.sh
git diff --check
```

## Tests Passed

- Rendering and reflective-region metrics are reported with hypothesis flags.
- Missing geometry GT produces explicit `null` metrics with `not_available_reason`.
- Output writer creates `metrics.json`, `metrics.csv`, `qualitative_panels/`, `failure_case_panels/`, and reflective mask visualization.
- full unittest discovery: passed, 31 tests.
- py_compile for SRD-modified Python files: passed.
- shell syntax check for `scripts/srd_gs/run_eval_one_scene.sh`: passed.
- `git diff --check`: passed.

## Tests Failed

Initial RED test failed because `utils.metric_utils` did not exist. No failures after implementation.

## Needs Runtime Verification

- Run `eval_reflective_assets.py` on real SRD-GS/Ref-GS rendered images.
- Verify reflective mask quality when using `--auto_reflective_mask`.
- Integrate LPIPS if local weights/dependency are available.
- Integrate real predicted/GT mesh or point cloud loading before claim-bearing Chamfer/F-score evaluation.
- Add qualitative/failure panels with actual image layouts in later milestones.

## Not Implemented in Milestone 7

- Real scene metric execution.
- LPIPS model loading.
- GT mesh/point-cloud file parsing in the CLI.
- Panel image composition.
- Dataset-level table aggregation.
- Scientific claim that SRD-GS improves any metric.
