# Ref-GS Limitation Analysis Helpers

This directory contains non-invasive helpers for evidence-first limitation analysis of
`Ref-GS: Directional Factorization for 2D Gaussian Splatting`.

Round3 adds a default-off `return_components` path in the renderer so component
buffers can be exported. Core training entrypoints and dataset loaders are not
modified, and renderer defaults keep training behavior unchanged.

## Environment

```bash
conda activate ref_gs
python --version
which python
nvidia-smi
```

If direct activation is unavailable in a non-interactive shell:

```bash
source /home/liuly/anaconda3/etc/profile.d/conda.sh
conda activate ref_gs
```

In this workspace, `nvidia-smi` may fail inside the restricted sandbox while the
host-level check succeeds. Treat this as an environment visibility issue, not as
a Ref-GS code result.

## Data Path

Default dataset root:

```bash
/data/liuly/dataset/3DGS
```

## Dataset Scan

```bash
python experiments/ref_gs_limitation_analysis/dataset_inventory.py \
  --root /data/liuly/dataset/3DGS \
  --out experiments/ref_gs_limitation_analysis/dataset_inventory.json
```

Outputs:

- `dataset_inventory.json`
- `dataset_inventory.md`

The scanner detects Blender transforms, COLMAP sparse layouts, image counts,
masks, train/test splits, mesh/eval point files, depth/normal/material-like files,
and small sanity candidates. It does not read full image arrays.

## Experiment Matrix Dry-Run

```bash
python experiments/ref_gs_limitation_analysis/make_experiment_matrix.py --dry-run
```

Outputs:

- `experiment_matrix.json`
- `experiment_matrix.csv`
- `experiment_matrix.md`

The dry-run prints commands only. It does not train.

## Small Sanity

Default mode validates the environment, `train.py --help`, and the default scene path:

```bash
bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh
```

To intentionally run a 2-iteration sanity on the default `Shiny Blender Synthetic/ball`:

```bash
RUN_TRAIN=1 bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh
```

For the stronger component pipeline sanity, use:

```bash
bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
RUN_TRAIN=1 SANITY_ITER=2 bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
```

The component sanity runs `env_check.sh`, optionally trains for exactly
`SANITY_ITER`, exports one test view with `export_pbr_views.py`, evaluates
available PBR/render paths with `evaluate_pbr.py`, and can dry-run mesh export.
It is configurable:

```bash
SANITY_SCRIPT=train-NeRF.py \
SCENE_PATH="/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
MODEL_PATH=output/ref_gs_limitation_sanity/materials_iter2 \
SANITY_ITER=2 \
RUN_TRAIN=0 RUN_EXPORT=1 RUN_EVAL=1 RUN_MESH=1 \
RENDER_FUNC=nerf \
bash experiments/ref_gs_limitation_analysis/run_component_sanity.sh
```

For CI/audit usage, set `STRICT=1`. Default mode stays safe-fail and records
internal failures in logs; strict mode returns nonzero when requested training
fails, an expected checkpoint is missing, export fails, eval exits nonzero, or a
requested non-dry-run mesh command exits nonzero.

Use `ROUND_NAME=round4` to write `component_sanity_round4_*.log` files instead
of the default round3 filenames. The same round name is used in the default
component sanity export, metric, and mesh output paths unless `EXPORT_DIR`,
`METRIC_DIR`, or `MESH_PATH` are set explicitly.

Use `SANITY_LOG_DIR=/tmp/sanity_logs` when tests or CI should not write into the
formal experiment log directory. The sanity runner passes that directory through
to `env_check.sh` as `env_check_${ROUND_NAME}.txt`; `env_check.sh` also accepts
`ENV_CHECK_LOG_DIR` or `ENV_CHECK_LOG_FILE` directly.

## Environment Check

```bash
bash experiments/ref_gs_limitation_analysis/env_check.sh
```

Output:

- `sanity_logs/env_check.txt`

The script records failures such as sandbox-hidden `nvidia-smi` without aborting.

## PBR / Component Export

```bash
python experiments/ref_gs_limitation_analysis/export_pbr_views.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path output/ref_gs_limitation_sanity/ball_iter2 \
  --checkpoint output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth \
  --split test \
  --max_views 3 \
  --return_components \
  --render_func ref \
  --out_dir experiments/ref_gs_limitation_analysis/exports/ball_iter2
```

Use `--dry-run` to validate paths without constructing CUDA modules. The exporter
writes `manifest.json` and records missing keys instead of fabricating buffers.
With `--return_components`, the renderer returns additional component buffers
without changing default training behavior. Supported render functions:

- `ref`: `pbr_rgb`, stock `render`, diffuse/specular, albedo, roughness, features, alpha, normal, depth.
- `nerf`: same component set plus stock `render`.
- `real`: same component set plus `ref_w` and `out_w`.

Missing keys are still recorded per view in the manifest when a render function
does not produce them.

## PBR Evaluation

```bash
python experiments/ref_gs_limitation_analysis/evaluate_pbr.py \
  --export_dir experiments/ref_gs_limitation_analysis/exports/ball_iter2 \
  --out experiments/ref_gs_limitation_analysis/metrics/ball_iter2_pbr_eval
```

Outputs:

- `per_view_metrics.csv`
- `summary_metrics.json`
- `summary_metrics.md`
- `missing_buffers.md`

Missing inputs are written as `NA`. The summary includes
`pbr_rgb_vs_render_gap` when both RGB buffers exist.

## Mesh Export

```bash
python experiments/ref_gs_limitation_analysis/export_mesh.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --model_path output/ref_gs_limitation_sanity/toaster_iter2 \
  --checkpoint output/ref_gs_limitation_sanity/toaster_iter2/chkpnt2.pth \
  --split test \
  --max_views 3 \
  --depth_ratio 1.0 \
  --out_mesh experiments/ref_gs_limitation_analysis/meshes/toaster_sanity/mesh.ply \
  --dry-run
```

The mesh exporter wraps `utils.mesh_utils.GaussianExtractor` and writes
`mesh_manifest.json` next to `--out_mesh`. If CUDA/Open3D/checkpoint inputs are
unavailable, it writes a safe `NA` manifest with the failure reason.

Use `--strict` when a non-dry-run mesh export is expected to succeed and should
return nonzero on `status != ok`.

## Geometry Evaluation

```bash
python experiments/ref_gs_limitation_analysis/evaluate_geometry.py \
  --pred predicted_mesh.ply \
  --gt "/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender/eval_pts.ply" \
  --out experiments/ref_gs_limitation_analysis/metrics/geometry_bell \
  --num_samples 200000 \
  --thresholds 0.001 0.002 0.005 0.01
```

The evaluator supports PLY mesh/point inputs, Chamfer-L1 style symmetric nearest
neighbor distance, Chamfer-L2, F-score thresholds, point counts, bbox stats, and
`geometry_pair_summary.json`. Missing inputs produce `NA` outputs.

## Timing / Memory Probe

```bash
bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh \
  --script train-NeRF.py \
  --scene "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" \
  --model output/ref_gs_limitation_timing/materials_iter10 \
  --iterations 10 \
  --dry-run
```

Outputs:

- `metrics/timing_probe/timing_summary.json`
- `metrics/timing_probe/timing_summary.md`

The output root and summary filename can be isolated with:

```bash
TIMING_OUT_DIR=/tmp/timing_metrics \
TIMING_LOG_DIR=/tmp/timing_logs \
TIMING_SUMMARY_BASENAME=timing_summary_unit \
bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh --dry-run
```

Without `--dry-run`, the script runs the requested short training command and
records wall-clock time, best-effort peak GPU memory from `nvidia-smi`,
checkpoint size, log path, and exit code.

Use `--strict` for CI/audit checks. In strict mode, a non-dry-run timing probe
returns the underlying training exit code when it is nonzero. GPU memory remains
`NA` with a reason when `nvidia-smi` is unavailable.

## Real-Scene Environment Sphere Coverage

```bash
python experiments/ref_gs_limitation_analysis/check_env_sphere_coverage.py \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Real/gardenspheres" \
  --center -0.2270 1.9700 1.7740 \
  --radius 0.974 \
  --xyz_axis 2 1 0 \
  --out experiments/ref_gs_limitation_analysis/metrics/gardenspheres_env_default_coverage
```

This does not train. It measures point-cloud coverage under radius, center, and
axis perturbations.

To choose a different script or scene:

```bash
RUN_TRAIN=1 \
SANITY_SCRIPT=train-NeRO.py \
SANITY_SCENE="/data/liuly/dataset/3DGS/GlossySyntheticConverted/bell_blender" \
SANITY_EXTRA="--albedo_bias 2 --albedo_lr 0.0005 --init_until_iter 1" \
bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh
```

## Full Experiments

Use `experiment_matrix.md` as the command source. Full runs are intentionally not
launched by these helpers.

Example:

```bash
python train.py \
  -s "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/toaster" \
  --eval --run_dim 256 --albedo_bias 0 \
  --model_path output/ref_gs_limitation/e2_toaster_depth0
```

## Metrics Collection

```bash
python experiments/ref_gs_limitation_analysis/collect_metrics.py \
  --roots output/ref_gs_limitation /tmp/ref_gs_limitation_sanity \
  --out experiments/ref_gs_limitation_analysis/metrics_summary.csv
```

This collector is conservative: missing metrics are written as `NA`.

## Visualization

Ref-GS periodically writes component buffers to the hard-coded `result/` directory
when rendering iterations satisfy `iteration % 500 == 0`.

```bash
python experiments/ref_gs_limitation_analysis/visualize_outputs.py \
  --input-dir result \
  --out experiments/ref_gs_limitation_analysis/output_contact_sheet.png
```

If component buffers are missing, the script reports which buffers need export
instead of failing.

## Current Evidence Boundary

- The generated limitations are hypotheses unless backed by completed experiment outputs.
- The stock repository has training entrypoints but no standalone render/eval CLI.
- Component-level and mesh-level evaluation require an exporter/evaluator wrapper before
  they can support scientific claims.
