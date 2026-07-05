# Ref-GS Limitation Analysis Helpers

This directory contains non-invasive helpers for evidence-first limitation analysis of
`Ref-GS: Directional Factorization for 2D Gaussian Splatting`.

No core training, renderer, or dataset loader files are modified.

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
