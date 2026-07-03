# Milestone 37: LPIPS / Refl-LPIPS dependency gate

Status: read-only dependency gate GO; LPIPS compute not run; paper-scale still blocked

## Objective

Implement a bounded dependency/artifact gate for `rendering/lpips` and `reflective_region/refl_lpips`. This milestone checks whether the `ref_gs` environment and existing M32 render-eval artifacts are ready for a future LPIPS computation pass.

This milestone does not launch training, rendering, mesh extraction, texture export, evaluation, or multi-scene experiments. It does not compute LPIPS values and does not overwrite existing M32 metrics.

## Claim Boundary

- Allowed claim: `lpips` and torch are importable in `ref_gs`.
- Allowed claim: LPIPS model initialization succeeds in the current environment.
- Allowed claim: M32 render-eval pred/GT RGB artifacts and reflective masks are present for a future bounded compute pass.
- Allowed claim: `rendering/lpips` and `reflective_region/refl_lpips` are dependency/artifact-ready for future bounded compute.
- Disallowed claim: LPIPS or Refl-LPIPS values were computed.
- Disallowed claim: SRD-GS improves over Ref-GS.
- Disallowed claim: rendering recovery, stable geometry superiority, or paper-scale quality is validated.
- Disallowed claim: remaining GT material/depth, material-view, or runtime-log blockers are solved.

## Implementation

- Added `scripts/srd_gs/gate_lpips_dependency_m37.py`.
- Added `tests/test_lpips_dependency_gate.py`.
- The script consumes:
  - M32 `eval_with_gt_mesh/metrics.csv`
  - M32 `eval_with_gt_mesh/metrics.json`
  - M32 `render_eval_pairs/render_eval_manifest.json`
  - M32 `render_eval_pairs/*`
- The script writes:
  - `lpips_dependency_gate.csv`
  - `lpips_dependency_gate.json`
  - `lpips_dependency_gate.md`

## Command

```bash
conda run -n ref_gs python scripts/srd_gs/gate_lpips_dependency_m37.py \
  --metrics_csv outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.csv \
  --metrics_json outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/eval_with_gt_mesh/metrics.json \
  --manifest outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs/render_eval_manifest.json \
  --eval_pairs_dir outputs/srd_gs_instrumented_runtime_m32_i30/results/ball/full_srd_gs_branch_raster_opacity_quarter_i300/render_eval_pairs \
  --output_dir outputs/srd_gs_lpips_dependency_gate_m37
```

## Outputs

- `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.csv`
- `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.json`
- `outputs/srd_gs_lpips_dependency_gate_m37/lpips_dependency_gate.md`

## Key Gate Results

| Metric | Status | Import available | Model init available | Render pairs | Reflective mask |
| --- | --- | --- | --- | --- | --- |
| `rendering/lpips` | `ready_for_bounded_compute` | true | true | true | true |
| `reflective_region/refl_lpips` | `ready_for_bounded_compute` | true | true | true | true |

Additional probe evidence:

- `lpips_origin`: `/home/liuly/anaconda3/envs/ref_gs/lib/python3.7/site-packages/lpips/__init__.py`
- `torch_version`: `1.12.1`
- `metrics_computed`: false
- `runtime_launched`: false

## Interpretation

M37 removes the dependency-readiness blocker for LPIPS/Refl-LPIPS in the current `ref_gs` environment. It does not remove the metric-computation blocker: M32 source metrics still contain `lpips_not_available`, and no LPIPS values were written.

The next bounded step, if selected, should be a dry-run-first LPIPS compute plumbing pass that writes separate augmented metrics or a new output directory without overwriting the M32 source metrics.

## Failure Conditions

- If this milestone launches training, rendering, mesh extraction, texture export, or evaluation, it fails.
- If it writes LPIPS/Refl-LPIPS values into source M32 metrics, it fails.
- If dependency readiness is treated as rendering recovery or SRD-GS superiority, it fails.
- If remaining GT material/depth, material-view, or runtime-log blockers are marked solved, it fails.
- If the NO-GO paper-scale gate is weakened, it fails.

## Verification

- Focused TDD RED: `conda run -n ref_gs python -m unittest tests.test_lpips_dependency_gate` failed before `gate_lpips_dependency_m37.py` existed.
- Focused TDD GREEN: `conda run -n ref_gs python -m unittest tests.test_lpips_dependency_gate` passed, 1 test.
- M37 gate command passed and wrote three output artifacts under `outputs/srd_gs_lpips_dependency_gate_m37`.
- Full verification status is recorded in `implementation_log.md` after the final validation pass.

## Recommended Next Milestone

Milestone 38 should remain bounded. If LPIPS compute is chosen, implement a dry-run-first LPIPS metric computation pass that writes separate augmented outputs and preserves source M32 metrics. Do not launch broad paper-scale experiments.
