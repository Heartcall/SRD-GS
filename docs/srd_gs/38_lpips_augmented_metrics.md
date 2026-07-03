# Milestone 38: LPIPS augmented metrics

Status: bounded LPIPS compute plumbing GO; source metrics preserved; paper-scale still blocked

## Objective

Implement the M37-recommended dry-run-first LPIPS compute plumbing pass. This milestone reads existing M32 render-eval artifacts, computes LPIPS and reflective-region LPIPS for the two-frame bounded M32 artifact set, and writes separate augmented outputs without overwriting source M32 metrics.

This milestone does not launch training, rendering, mesh extraction, texture export, broad evaluation, or multi-scene experiments.

## Claim Boundary

- Allowed claim: bounded LPIPS/Refl-LPIPS values were computed for the existing M32 two-frame `ball` artifact set.
- Allowed claim: the computed values are written only to M38 augmented outputs.
- Allowed claim: source M32 metrics remain unchanged and still contain `lpips_not_available`.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.
- Disallowed claim: GT material/depth, material-view, or runtime-cost blockers are solved.
- Disallowed claim: the two-frame values generalize beyond this bounded diagnostic artifact set.

## Implementation

- Added `scripts/srd_gs/compute_lpips_augmented_metrics_m38.py`.
- Added `tests/test_lpips_compute_plumbing.py`.
- The script supports:
  - `--dry_run` planning outputs;
  - deterministic test injection through `--metric_values_json`;
  - real CPU LPIPS computation through the installed `lpips` dependency.
- The script consumes:
  - M32 `eval_with_gt_mesh/metrics.csv`
  - M32 `eval_with_gt_mesh/metrics.json`
  - M32 `render_eval_pairs/render_eval_manifest.json`
  - M32 `render_eval_pairs/*`
  - M37 `lpips_dependency_gate.json`
- The script writes dry-run outputs:
  - `lpips_compute_plan.csv`
  - `lpips_compute_plan.json`
  - `lpips_compute_plan.md`
- The script writes compute outputs:
  - `lpips_frame_metrics.csv`
  - `lpips_augmented_metrics.csv`
  - `lpips_augmented_metrics.json`
  - `lpips_compute_summary.json`
  - `lpips_compute_summary.md`

## Commands

Dry run:

```bash
conda run -n ref_gs python scripts/srd_gs/compute_lpips_augmented_metrics_m38.py \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --metrics_json outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json \
  --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --eval_pairs_dir outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs \
  --gate_json outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json \
  --output_dir outputs/srd_gs_lpips_compute_m38_dryrun \
  --dry_run
```

Compute:

```bash
conda run -n ref_gs python scripts/srd_gs/compute_lpips_augmented_metrics_m38.py \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --metrics_json outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json \
  --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --eval_pairs_dir outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs \
  --gate_json outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json \
  --output_dir outputs/srd_gs_lpips_compute_m38 \
  --device cpu
```

## Outputs

- `outputs/srd_gs_lpips_compute_m38_dryrun/lpips_compute_plan.csv`
- `outputs/srd_gs_lpips_compute_m38_dryrun/lpips_compute_plan.json`
- `outputs/srd_gs_lpips_compute_m38_dryrun/lpips_compute_plan.md`
- `outputs/srd_gs_lpips_compute_m38/lpips_frame_metrics.csv`
- `outputs/srd_gs_lpips_compute_m38/lpips_augmented_metrics.csv`
- `outputs/srd_gs_lpips_compute_m38/lpips_augmented_metrics.json`
- `outputs/srd_gs_lpips_compute_m38/lpips_compute_summary.json`
- `outputs/srd_gs_lpips_compute_m38/lpips_compute_summary.md`

## Key Metrics

| Metric | Value |
| --- | ---: |
| Frames | 2 |
| LPIPS | 0.9455429017543793 |
| Refl-LPIPS | 0.8390642702579498 |
| Source unavailable LPIPS rows | 2 |
| Source metrics overwritten | false |

Per-frame rows:

| Frame | LPIPS | Refl-LPIPS | Reflective mask pixels |
| ---: | ---: | ---: | ---: |
| 0 | 0.9465986490249634 | 0.839540958404541 | 460062 |
| 1 | 0.9444871544837952 | 0.8385875821113586 | 460212 |

## Interpretation

M38 removes the LPIPS metric-computation plumbing blocker for the bounded M32 two-frame artifact set. It does not establish rendering recovery or method superiority. LPIPS/Refl-LPIPS are high in this short diagnostic artifact set, and the rest of the M32 quality caveats remain: F-score is zero, geometry metrics are weak, and several material/runtime metrics remain unavailable.

The source M32 metrics remain unchanged; the LPIPS values are only in `outputs/srd_gs_lpips_compute_m38`.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, or broad evaluation, it fails.
- If it overwrites source M32 metrics, it fails.
- If two-frame LPIPS values are treated as paper-scale rendering recovery or SRD-GS superiority, it fails.
- If remaining GT material/depth, material-view, or runtime-log blockers are marked solved, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_lpips_compute_plumbing` failed before `compute_lpips_augmented_metrics_m38.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_lpips_compute_plumbing` passed, 1 test.
- M38 dry-run command passed and wrote three dry-run artifacts under `outputs/srd_gs_lpips_compute_m38_dryrun`.
- M38 compute command passed and wrote five compute artifacts under `outputs/srd_gs_lpips_compute_m38`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 39 should remain bounded. A reasonable next step is a read-only diagnostic synthesis that incorporates M38 augmented LPIPS values with M33/M36/M37 evidence and keeps all quality limitations explicit. Do not launch broad paper-scale experiments.
