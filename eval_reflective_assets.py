import json
import os
from argparse import ArgumentParser

import imageio.v2 as imageio
import numpy as np

from utils.metric_utils import (
    compute_geometry_metrics,
    compute_reflective_asset_metrics,
    compute_runtime_metrics,
    compute_texture_material_metrics,
    estimate_reflective_mask,
    write_metrics_outputs,
)


def _read_image(path):
    if not path:
        return None
    return imageio.imread(path)


def _read_mask(path):
    if not path:
        return None
    mask = imageio.imread(path)
    if mask.ndim == 3:
        mask = mask[..., 0]
    return mask > 127


def _read_optional_json(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = ArgumentParser(description="Evaluate SRD-GS reflective asset metrics from saved artifacts")
    parser.add_argument("--pred_rgb", type=str, default="")
    parser.add_argument("--gt_rgb", type=str, default="")
    parser.add_argument("--reflective_mask", type=str, default="")
    parser.add_argument("--auto_reflective_mask", action="store_true", default=False)
    parser.add_argument("--mask_threshold", type=float, default=0.2)
    parser.add_argument("--material_report", type=str, default="")
    parser.add_argument("--highlight_leakage_mask", type=str, default="")
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--training_time", type=float, default=None)
    parser.add_argument("--peak_memory", type=float, default=None)
    parser.add_argument("--render_fps", type=float, default=None)
    args = parser.parse_args()

    pred_rgb = _read_image(args.pred_rgb)
    gt_rgb = _read_image(args.gt_rgb)
    reflective_mask = _read_mask(args.reflective_mask)
    mask_source = "provided" if reflective_mask is not None else None
    if reflective_mask is None and args.auto_reflective_mask and pred_rgb is not None:
        reflective_mask = estimate_reflective_mask(pred_rgb, gt_rgb, threshold=args.mask_threshold)
        mask_source = "auto_residual_threshold" if gt_rgb is not None else "auto_intensity_threshold"

    metrics = []
    metrics.extend(compute_reflective_asset_metrics(pred_rgb, gt_rgb, reflective_mask))
    metrics.extend(compute_geometry_metrics())

    material_report = _read_optional_json(args.material_report)
    highlight_leakage_mask = _read_image(args.highlight_leakage_mask)
    if highlight_leakage_mask is None and material_report.get("highlight_leakage_score") is not None:
        highlight_leakage_score = np.asarray([[material_report["highlight_leakage_score"]]], dtype=np.float32)
        highlight_leakage_mask = highlight_leakage_score
    metrics.extend(compute_texture_material_metrics(highlight_leakage_mask=highlight_leakage_mask))
    metrics.extend(compute_runtime_metrics(args.training_time, args.peak_memory, args.render_fps))

    outputs = write_metrics_outputs(metrics, args.output_dir, reflective_mask=reflective_mask, mask_source=mask_source)
    print("Wrote metrics:", outputs["metrics_json"])
    print("Wrote metrics CSV:", outputs["metrics_csv"])


if __name__ == "__main__":
    main()
