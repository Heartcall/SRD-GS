import json
import os
from argparse import ArgumentParser

import imageio.v2 as imageio
import numpy as np

from utils.geometry_eval_utils import compute_geometry_metrics_from_paths
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


def _resolve(root, path):
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.join(root, path)


def _read_rgb(path):
    image = _read_image(path)
    if image is None:
        return None
    image = np.asarray(image)
    if image.ndim == 2:
        image = np.repeat(image[..., None], 3, axis=-1)
    if image.ndim == 3 and image.shape[-1] > 3:
        image = image[..., :3]
    return image


def _stack_manifest_images(root, frames, key):
    arrays = []
    for frame in frames:
        path = _resolve(root, frame.get(key))
        if not path or not os.path.exists(path):
            return None
        arrays.append(_read_rgb(path))
    if not arrays:
        return None
    return np.concatenate(arrays, axis=0)


def _stack_manifest_masks(root, frames):
    arrays = []
    for frame in frames:
        path = _resolve(root, frame.get("reflective_mask"))
        if not path or not os.path.exists(path):
            return None
        arrays.append(_read_mask(path))
    if not arrays:
        return None
    return np.concatenate(arrays, axis=0)


def evaluate_render_eval_pairs_dir(eval_pairs_dir, auto_reflective_mask=False, mask_threshold=0.2):
    manifest_path = os.path.join(eval_pairs_dir, "render_eval_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    frames = manifest.get("frames", [])
    pred_rgb = _stack_manifest_images(eval_pairs_dir, frames, "pred_rgb")
    gt_rgb = _stack_manifest_images(eval_pairs_dir, frames, "gt_rgb")
    reflective_mask = _stack_manifest_masks(eval_pairs_dir, frames)
    if reflective_mask is None and auto_reflective_mask and pred_rgb is not None:
        reflective_mask = estimate_reflective_mask(pred_rgb, gt_rgb, threshold=mask_threshold)
    return compute_reflective_asset_metrics(pred_rgb, gt_rgb, reflective_mask)


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
    parser.add_argument("--eval_pairs_dir", type=str, default="")
    parser.add_argument("--pred_geometry", type=str, default="")
    parser.add_argument("--gt_geometry_path", type=str, default="")
    parser.add_argument("--source_path", type=str, default="")
    parser.add_argument("--accept_dataset_points3d_as_gt", action="store_true", default=False)
    parser.add_argument("--geometry_sample_count", type=int, default=20000)
    parser.add_argument("--fscore_threshold", type=float, default=0.01)
    args = parser.parse_args()

    if args.eval_pairs_dir:
        pred_rgb = None
        gt_rgb = None
        reflective_mask = None
        mask_source = "manifest_or_auto"
        metrics = evaluate_render_eval_pairs_dir(
            args.eval_pairs_dir,
            auto_reflective_mask=args.auto_reflective_mask,
            mask_threshold=args.mask_threshold,
        )
    else:
        pred_rgb = _read_image(args.pred_rgb)
        gt_rgb = _read_image(args.gt_rgb)
        reflective_mask = _read_mask(args.reflective_mask)
        mask_source = "provided" if reflective_mask is not None else None
        if reflective_mask is None and args.auto_reflective_mask and pred_rgb is not None:
            reflective_mask = estimate_reflective_mask(pred_rgb, gt_rgb, threshold=args.mask_threshold)
            mask_source = "auto_residual_threshold" if gt_rgb is not None else "auto_intensity_threshold"

        metrics = []
        metrics.extend(compute_reflective_asset_metrics(pred_rgb, gt_rgb, reflective_mask))

    reflective_mask_for_output = None
    if args.eval_pairs_dir:
        manifest_mask = os.path.join(args.eval_pairs_dir, "reflective_mask.png")
        reflective_mask_for_output = _read_mask(manifest_mask) if os.path.exists(manifest_mask) else None
    else:
        reflective_mask_for_output = reflective_mask
    if args.pred_geometry or args.gt_geometry_path or args.source_path:
        metrics.extend(
            compute_geometry_metrics_from_paths(
                pred_geometry_path=args.pred_geometry,
                gt_geometry_path=args.gt_geometry_path,
                source_path=args.source_path,
                accept_gt_geometry=args.accept_dataset_points3d_as_gt,
                sample_count=args.geometry_sample_count,
                fscore_threshold=args.fscore_threshold,
            )
        )
    else:
        metrics.extend(compute_geometry_metrics())

    material_report = _read_optional_json(args.material_report)
    highlight_leakage_mask = _read_image(args.highlight_leakage_mask)
    if highlight_leakage_mask is None and material_report.get("highlight_leakage_score") is not None:
        highlight_leakage_score = np.asarray([[material_report["highlight_leakage_score"]]], dtype=np.float32)
        highlight_leakage_mask = highlight_leakage_score
    metrics.extend(compute_texture_material_metrics(highlight_leakage_mask=highlight_leakage_mask))
    metrics.extend(compute_runtime_metrics(args.training_time, args.peak_memory, args.render_fps))

    outputs = write_metrics_outputs(metrics, args.output_dir, reflective_mask=reflective_mask_for_output, mask_source=mask_source)
    print("Wrote metrics:", outputs["metrics_json"])
    print("Wrote metrics CSV:", outputs["metrics_csv"])


if __name__ == "__main__":
    main()
