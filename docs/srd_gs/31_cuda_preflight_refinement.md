# Milestone 31: CUDA preflight refinement

Status: bounded preflight diagnostic GO; runtime launch NO-GO in current environment; paper-scale still blocked

## Objective

Rerun the bounded instrumented runtime gate after M30 and refine CUDA visibility diagnostics so the preflight distinguishes Torch CUDA visibility from `nvidia-smi` utilization visibility. This milestone does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: the bounded preflight now records Torch CUDA availability, device count, and whether the hardcoded training GPU index is visible.
- Allowed claim: the M31 dry-run command package is instrumented and ready for a future bounded run if runtime gates pass.
- Allowed claim: runtime launch remains blocked in the current environment because the training GPU is not visible to the `ref_gs` runtime.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: runtime loss progression or failure-case behavior has been observed.
- Disallowed claim: rendering recovery, geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond this one-scene dry-run/preflight package.

## Implementation

- Updated `scripts/srd_gs/preflight_instrumented_runtime.py` to collect Torch CUDA availability through the explicit `ref_gs` interpreter when possible.
- Added preflight fields:
  - `torch_cuda_available`
  - `torch_device_count`
  - `torch_training_gpu_visible`
- Refined blocker classification:
  - if Torch sees the training GPU but `nvidia-smi` rows are unavailable, block as `gpu_utilization_unavailable`;
  - if Torch cannot see the training GPU and no `nvidia-smi` row exists, block as `training_gpu_not_visible`.
- Extended `tests/test_instrumented_runtime_preflight.py` for the refined CUDA visibility behavior.

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
  --output_root outputs/srd_gs_cuda_preflight_refine_m31_dryrun \
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
  --result_root outputs/srd_gs_cuda_preflight_refine_m31_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M31_cuda_preflight_refine \
  --output_dir outputs/srd_gs_cuda_preflight_refine_m31 \
  --training_gpu_index 2 \
  --max_gpu_utilization_percent 50 \
  --workspace_path . \
  --min_workspace_free_gb 25
```

## Outputs

- `outputs/srd_gs_cuda_preflight_refine_m31_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/train_command.txt`
- `outputs/srd_gs_cuda_preflight_refine_m31_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/`
- `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.csv`
- `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.json`
- `outputs/srd_gs_cuda_preflight_refine_m31/instrumented_runtime_preflight.md`

## Preflight Matrix

| Label | Runtime GO | Contract ready | Torch CUDA | Torch devices | Training GPU visible | Workspace free GB | Process matches | Blockers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M31 CUDA preflight refine | false | true | false | 0 | false | 30.18 | 0 | `training_gpu_not_visible` |

## Interpretation

M31 resolves an ambiguity in the preflight gate but does not make the environment runtime-ready. The workspace free-space gate now passes, and no prohibited SRD processes are running, but the `ref_gs` runtime reports `torch.cuda.is_available() == False` and `torch.cuda.device_count() == 0`. Since `train.py` targets CUDA and hardcodes device 2, launching the bounded run would be an avoidable failed runtime attempt.

No `loss_log.csv`, render metrics, mesh metrics, texture metrics, or runtime failure-summary artifacts were generated in this milestone because no runtime chain was launched.

## Failure Conditions

- If runtime is launched while `runtime_go=false`, the milestone fails.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. M31 only changes preflight diagnostics.
- If CUDA preflight readiness is treated as runtime quality evidence, the milestone fails.
- If the remaining GPU visibility blocker is ignored, the milestone fails.
- If multi-scene or paper-scale conclusions are drawn from M31, the milestone fails.

## Verification

- Focused TDD RED: the refined preflight fields and direct interpreter probe were absent before implementation.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_instrumented_runtime_preflight` passed, 5 tests.
- M31 dry-run command package passed under `outputs/srd_gs_cuda_preflight_refine_m31_dryrun`.
- M31 runtime preflight wrote the three summary artifacts under `outputs/srd_gs_cuda_preflight_refine_m31`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 32 should remain bounded. First restore/verify CUDA visibility for the `ref_gs` runtime and rerun the same preflight. Only if `runtime_go=true`, launch exactly one single-scene instrumented `ball` run. Do not launch broad paper-scale experiments.
