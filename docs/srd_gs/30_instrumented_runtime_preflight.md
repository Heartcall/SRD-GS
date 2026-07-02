# Milestone 30: Instrumented runtime preflight

Status: bounded preflight GO; runtime launch NO-GO in current environment; paper-scale still blocked

## Objective

Use the Milestone 29 instrumentation contract to prepare one bounded 30-iteration `ball` instrumented smoke/control command package, then gate whether it is safe to launch runtime. This milestone is intentionally a preflight when the GPU/storage gates are not acceptable. It does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: the M30 dry-run command package is ready for a future bounded instrumented `ball` run.
- Allowed claim: the preflight detected runtime blockers before launching training.
- Allowed claim: instrumentation contract readiness is true for the M30 dry-run result root.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: runtime loss progression or failure-case behavior has been observed.
- Disallowed claim: rendering recovery, geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond the single-scene dry-run package.

## Implementation

- Added `scripts/srd_gs/preflight_instrumented_runtime.py`.
- Added `tests/test_instrumented_runtime_preflight.py`.
- The preflight script checks:
  - train-only `--srd_loss_log_path` instrumentation contract;
  - expected `eval_with_gt_mesh/failure_case_panels/` directory;
  - training GPU visibility and utilization;
  - workspace free-space threshold;
  - prohibited train/render/eval/export process matches.
- The script writes:
  - `instrumented_runtime_preflight.csv`
  - `instrumented_runtime_preflight.json`
  - `instrumented_runtime_preflight.md`

## Commands

Focused TDD:

```bash
conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight
```

Dry-run command package:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_instrumented_runtime_m30_dryrun \
  --scene_name ball \
  --iterations 30 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000
```

Runtime preflight:

```bash
python scripts/srd_gs/preflight_instrumented_runtime.py \
  --result_root outputs/srd_gs_instrumented_runtime_m30_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M30_instrumented_ball_i30_preflight \
  --output_dir outputs/srd_gs_instrumented_runtime_preflight_m30 \
  --training_gpu_index 2 \
  --max_gpu_utilization_percent 50 \
  --workspace_path . \
  --min_workspace_free_gb 25
```

## Outputs

- `outputs/srd_gs_instrumented_runtime_m30_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/train_command.txt`
- `outputs/srd_gs_instrumented_runtime_m30_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/`
- `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.csv`
- `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.json`
- `outputs/srd_gs_instrumented_runtime_preflight_m30/instrumented_runtime_preflight.md`

## Preflight Matrix

| Label | Runtime GO | Contract ready | GPU index | GPU util | Workspace free GB | Process matches | Blockers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M30 instrumented ball i30 preflight | false | true | 2 | n/a | 18.38 | 0 | `training_gpu_not_visible`; `workspace_free_below_threshold` |

## Interpretation

M30 confirms that the instrumented command package is ready, but the runtime launch is blocked in the current environment. GPU visibility failed during the preflight query, and workspace free space is below the 25G threshold. Since the branch has an explicit paper-scale `NO-GO` gate and M30's purpose is bounded runtime readiness, the correct action is to stop at preflight rather than launch training.

No `loss_log.csv`, render metrics, mesh metrics, texture metrics, or failure-summary runtime artifacts were generated in this milestone because no runtime chain was launched.

## Failure Conditions

- If runtime is launched while `runtime_go=false`, the milestone fails.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. M30 adds only a preflight helper and a dry-run package.
- If preflight readiness is treated as runtime quality evidence, the milestone fails.
- If GPU/storage blockers are ignored, the milestone fails.
- If multi-scene or paper-scale conclusions are drawn from M30, the milestone fails.

## Verification

- Focused TDD RED: `tests.test_instrumented_runtime_preflight` failed before `scripts/srd_gs/preflight_instrumented_runtime.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight` passed, 3 tests.
- M30 dry-run command package passed under `outputs/srd_gs_instrumented_runtime_m30_dryrun`.
- M30 runtime preflight wrote the three summary artifacts under `outputs/srd_gs_instrumented_runtime_preflight_m30`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 31 should remain bounded. Rerun the M30 preflight when GPU visibility is restored and workspace free space is above the agreed threshold. Only if `runtime_go=true`, launch exactly one single-scene instrumented `ball` run from the dry-run command package or its regenerated equivalent. Do not launch broad paper-scale experiments.
