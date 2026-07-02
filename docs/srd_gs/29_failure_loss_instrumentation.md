# Milestone 29: Failure/loss instrumentation contract

Status: dry-run instrumentation GO; runtime evidence not generated; paper-scale still blocked

## Objective

Add dry-run-first instrumentation so future bounded SRD-GS runs can produce explicit loss-log and failure-panel artifacts. M28 showed that completed M20/M21/M24/M25/M26 result roots were auditable but lacked loss logs and failure panels. M29 closes the instrumentation contract only; it does not launch training, rendering, mesh extraction, texture export, or evaluation.

This is not a broad paper-scale experiment.

## Claim Boundary

- Allowed claim: future bounded runner outputs now pass a train-only `--srd_loss_log_path` to `train.py`.
- Allowed claim: the loss-log flag is isolated to training and does not leak into mesh, texture, render-pair, or eval commands.
- Allowed claim: eval metric output now writes a concrete `failure_case_panels/failure_summary.md` artifact when eval is executed.
- Allowed claim: the M29 dry-run package is ready for a future bounded instrumented run.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: loss progression or root cause has been observed in runtime.
- Disallowed claim: rendering recovery, geometry superiority, or PBR material accuracy is validated.
- Disallowed claim: results generalize beyond a future one-scene bounded run.

## Implementation

- Added opt-in SRD loss CSV logging helpers in `train.py`.
- Added `srd_loss_log_path` to loading parameters with default `""` for baseline compatibility.
- Updated `scripts/srd_gs/run_branch_raster_smoke_one_scene.sh` to pass `--srd_loss_log_path <result_root>/loss_log.csv` only to the training command and to predeclare the eval failure-panel directory in dry-run packages.
- Updated `utils/metric_utils.py` so `write_metrics_outputs()` writes `failure_case_panels/failure_summary.md`.
- Updated `scripts/srd_gs/summarize_failure_loss_artifacts.py` to detect `failure_case_panels/*` and `eval_with_gt_mesh/failure_case_panels/*`.
- Added `scripts/srd_gs/inspect_failure_loss_instrumentation.py` to summarize the dry-run instrumentation contract.
- Added tests for loss CSV logging, dry-run inspection, runner command isolation, and failure-summary output.

## Commands

Focused RED/GREEN loop:

```bash
conda run -n ref_gs python -m unittest tests.test_srd_loss_logging tests.test_failure_loss_instrumentation tests.test_branch_raster_smoke_runner tests.test_reflective_asset_metrics
```

Dry-run command package:

```bash
bash scripts/srd_gs/run_branch_raster_smoke_one_scene.sh \
  --config configs/srd_gs/full_srd_gs_branch_raster_opacity_quarter_i300.yaml \
  --scene_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --output_root outputs/srd_gs_failure_loss_instrumentation_m29_dryrun \
  --scene_name ball \
  --iterations 300 \
  --max_mesh_views 4 \
  --depth_trunc 10.0 \
  --max_texture_views 2 \
  --max_eval_views 2 \
  --geometry_sample_count 1000
```

Instrumentation summary:

```bash
python scripts/srd_gs/inspect_failure_loss_instrumentation.py \
  --result_root outputs/srd_gs_failure_loss_instrumentation_m29_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300 \
  --label M29_opacity_quarter_dryrun \
  --output_dir outputs/srd_gs_failure_loss_instrumentation_m29
```

## Outputs

- `outputs/srd_gs_failure_loss_instrumentation_m29_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/train_command.txt`
- `outputs/srd_gs_failure_loss_instrumentation_m29_dryrun/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/failure_case_panels/`
- `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.csv`
- `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.json`
- `outputs/srd_gs_failure_loss_instrumentation_m29/failure_loss_instrumentation.md`

## Instrumentation Matrix

| Label | Train command | Loss log in train | Loss flag leaks | Failure-panel dir | Contract ready |
| --- | ---: | ---: | ---: | ---: | ---: |
| M29 opacity-quarter dry-run | true | true | false | true | true |

## Interpretation

M29 removes the instrumentation blocker for a future bounded run: the runner now knows where training should write `loss_log.csv`, non-training commands stay clean, and eval output has an explicit failure-summary artifact path. This is still dry-run evidence only. No loss curves, runtime failure cases, rendering metrics, mesh metrics, or material metrics were generated in this milestone.

## Failure Conditions

- If `--srd_loss_log_path` appears outside the training command, the milestone fails.
- If `--enable_srd_gs=False` behavior changes, the milestone fails. The new loss log path is opt-in and empty by default.
- If failure summaries are treated as image-grid qualitative evidence, the milestone fails. They are instrumentation artifacts.
- If dry-run readiness is promoted to runtime root-cause evidence, the milestone fails.
- If multi-scene or paper-scale conclusions are drawn from M29, the milestone fails.

## Verification

- Focused TDD RED exposed missing loss logger, missing inspector, missing runner loss-log path, and missing failure summary.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_srd_loss_logging tests.test_failure_loss_instrumentation tests.test_branch_raster_smoke_runner tests.test_reflective_asset_metrics` passed, 15 tests.
- M29 dry-run command package passed and wrote command files under `outputs/srd_gs_failure_loss_instrumentation_m29_dryrun`.
- M29 instrumentation summary passed and wrote the three output artifacts under `outputs/srd_gs_failure_loss_instrumentation_m29`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 30 should remain bounded. Recommended next step is one explicitly gated single-scene instrumented run, using the M29 contract, to generate actual `loss_log.csv` and `failure_case_panels/failure_summary.md` runtime artifacts. Do not launch broad paper-scale experiments until loss progression, failure evidence, rendering/geometry tradeoff, and F-score blockers are addressed.
