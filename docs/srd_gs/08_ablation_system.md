# SRD-GS Ablation Configuration System

## Scope

本文件记录 Milestone 8。当前阶段实现 dry-run-first ablation configuration system，使 SRD-GS 的关键消融可以生成训练、surface-only mesh、texture export、evaluation 命令，并能汇总 `metrics.json`。本阶段不启动训练、不运行 mesh extraction、不运行真实评估，也不产生实验结论。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Added

Configs:

- `configs/srd_gs/refgs_baseline.yaml`
- `configs/srd_gs/full_srd_gs.yaml`
- `configs/srd_gs/no_reflection_branch.yaml`
- `configs/srd_gs/no_branch_separation.yaml`
- `configs/srd_gs/no_geo_loss.yaml`
- `configs/srd_gs/no_transport_consistency.yaml`
- `configs/srd_gs/naive_specular_rgb_consistency.yaml`
- `configs/srd_gs/no_texture_despecularization.yaml`
- `configs/srd_gs/no_staged_training.yaml`
- `configs/srd_gs/all_branch_mesh.yaml`

Scripts:

- `scripts/srd_gs/run_one_scene.sh`
- `scripts/srd_gs/run_ablation_one_scene.sh`
- `scripts/srd_gs/collect_results.py`
- `scripts/srd_gs/make_tables.py`
- `scripts/srd_gs/make_failure_panels.py`

Tests/docs:

- `tests/test_ablation_system_contract.py`
- `docs/srd_gs/08_ablation_system.md`

## Config Contract

Each config records:

- `name`
- `implementation_status`
- `hypothesis`
- `what_it_removes`
- `expected_supporting_result`
- `refuting_result`
- `metrics_to_inspect_first`
- `train_args`
- `mesh_mode`
- `texture_mode`
- `eval_enabled`

Important boundary: these configs define intended experiment controls. They do not prove that a scientific ablation has been run.

## Runnable vs Placeholder Variants

Runnable or proxy-runnable configs:

- `refgs_baseline.yaml`
- `full_srd_gs.yaml`
- `no_reflection_branch.yaml`, proxy removal through existing SRD loss weights.
- `no_branch_separation.yaml`
- `no_geo_loss.yaml`
- `no_transport_consistency.yaml`
- `no_texture_despecularization.yaml`
- `no_staged_training.yaml`
- `all_branch_mesh.yaml`

Placeholder config:

- `naive_specular_rgb_consistency.yaml`

`naive_specular_rgb_consistency.yaml` is marked `placeholder_config_not_runnable_until_loss_exists` because the current codebase does not implement a naive specular RGB consistency loss. This is intentional; the config records the planned negative control without inventing a non-existent flag or result.

## Runner Behavior

### `scripts/srd_gs/run_one_scene.sh`

Usage:

```bash
scripts/srd_gs/run_one_scene.sh \
  --config configs/srd_gs/full_srd_gs.yaml \
  --source_path <scene_path> \
  --output_root <output_root> \
  --scene_name <scene_name> \
  --iterations 31000
```

Default behavior is `DRY_RUN=1`. It writes command files:

- `train_command.txt`
- `mesh_command.txt`
- `texture_command.txt`
- `eval_command.txt`

It only executes commands when `--execute` is explicitly supplied.

### `scripts/srd_gs/run_ablation_one_scene.sh`

Runs `run_one_scene.sh` over `configs/srd_gs/*.yaml` by default. It passes through scene/output arguments and keeps dry-run behavior unless `--execute` is supplied.

## Result Collection

### `scripts/srd_gs/collect_results.py`

Collects nested `metrics.json` files and writes a flat CSV with:

- `scene`
- `variant`
- `category`
- `name`
- `value`
- `supports_hypothesis`
- `higher_is_better`
- `not_available_reason`
- `metrics_path`

### `scripts/srd_gs/make_tables.py`

Converts the collected CSV into a Markdown table.

### `scripts/srd_gs/make_failure_panels.py`

Creates a failure-panel source index from directories containing `metrics.json` or `reflective_mask.png`. It does not yet compose image grids.

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_ablation_system_contract
conda run -n ref_gs python -m unittest discover -s tests
conda run -n ref_gs python -m py_compile arguments/__init__.py scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py utils/render_utils.py utils/texture_baking.py utils/metric_utils.py extract_surface_mesh.py export_pbr_textures.py eval_reflective_assets.py scripts/srd_gs/collect_results.py scripts/srd_gs/make_tables.py scripts/srd_gs/make_failure_panels.py
bash -n scripts/srd_gs/run_one_scene.sh
bash -n scripts/srd_gs/run_ablation_one_scene.sh
scripts/srd_gs/run_one_scene.sh --config configs/srd_gs/full_srd_gs.yaml --source_path /tmp/srd_dummy_scene --output_root /tmp/srd_ablation_dryrun --scene_name dummy --iterations 10
git diff --check
```

## Tests Passed

- All ten required ablation config files exist.
- Each config records hypothesis, removal, supporting result, refuting result, and metrics to inspect first.
- Runners default to dry-run and reference training, mesh extraction, texture export, and evaluation steps.
- `collect_results.py` summarizes nested `metrics.json` into CSV.
- full unittest discovery: passed, 34 tests.
- py_compile for SRD-modified Python files and ablation utility scripts: passed.
- shell syntax checks for `run_one_scene.sh` and `run_ablation_one_scene.sh`: passed.
- dry-run generated train/mesh/texture/eval command files under `/tmp/srd_ablation_dryrun/results/dummy/full_srd_gs`.
- `git diff --check`: passed.

## Tests Failed

Initial RED test failed because configs and ablation scripts did not exist. No failures after implementation.

## Needs Runtime Verification

- Dry-run command review on a real scene path.
- Explicit `--execute` smoke run for one small scene.
- Verify config `train_args` are accepted by `train.py`.
- Verify each mesh/texture/eval command consumes produced artifacts correctly.
- Verify collected metrics row counts against real ablation outputs.

## Not Implemented in Milestone 8

- Real ablation training.
- Real mesh/texture/evaluation execution.
- YAML parsing beyond simple shell key extraction for runner command generation.
- Dataset-level statistical analysis.
- Image-grid failure panel composition.
- Any scientific claim from ablation results.
