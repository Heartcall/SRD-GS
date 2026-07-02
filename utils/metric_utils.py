import csv
import json
import math
import os

import imageio.v2 as imageio
import numpy as np


def _as_float_array(array):
    array = np.asarray(array, dtype=np.float32)
    if array.max(initial=0.0) > 1.5:
        array = array / 255.0
    return np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0)


def _metric_record(category, name, value, supports_hypothesis, not_available_reason=None, higher_is_better=None):
    if value is not None:
        value = float(value)
        if not math.isfinite(value):
            value = None
            not_available_reason = not_available_reason or "non_finite_value"
    return {
        "category": category,
        "name": name,
        "value": value,
        "supports_hypothesis": supports_hypothesis,
        "higher_is_better": higher_is_better,
        "not_available_reason": not_available_reason if value is None else None,
    }


def _masked_values(array, mask):
    array = _as_float_array(array)
    if mask is None:
        return array.reshape(-1, array.shape[-1]) if array.ndim == 3 else array.reshape(-1)
    mask = np.asarray(mask).astype(bool)
    if mask.shape != array.shape[:2]:
        raise ValueError("mask shape must match image height and width")
    if not mask.any():
        return None
    return array[mask]


def psnr(pred, target, mask=None, max_value=1.0):
    pred_values = _masked_values(pred, mask)
    target_values = _masked_values(target, mask)
    if pred_values is None or target_values is None:
        return None
    mse = np.mean((pred_values - target_values) ** 2)
    if mse <= 1e-12:
        return 100.0
    return 20.0 * math.log10(max_value) - 10.0 * math.log10(float(mse))


def ssim(pred, target, mask=None, max_value=1.0):
    pred_values = _masked_values(pred, mask)
    target_values = _masked_values(target, mask)
    if pred_values is None or target_values is None:
        return None
    pred_values = pred_values.astype(np.float64)
    target_values = target_values.astype(np.float64)
    c1 = (0.01 * max_value) ** 2
    c2 = (0.03 * max_value) ** 2
    mu_x = pred_values.mean()
    mu_y = target_values.mean()
    var_x = pred_values.var()
    var_y = target_values.var()
    cov_xy = ((pred_values - mu_x) * (target_values - mu_y)).mean()
    denom = (mu_x ** 2 + mu_y ** 2 + c1) * (var_x + var_y + c2)
    if denom <= 1e-12:
        return 1.0 if np.allclose(pred_values, target_values) else 0.0
    return ((2 * mu_x * mu_y + c1) * (2 * cov_xy + c2)) / denom


def estimate_reflective_mask(pred_rgb, gt_rgb=None, threshold=0.2):
    pred_rgb = _as_float_array(pred_rgb)
    if gt_rgb is None:
        intensity = pred_rgb.max(axis=-1) if pred_rgb.ndim == 3 else pred_rgb
        return intensity > threshold
    gt_rgb = _as_float_array(gt_rgb)
    residual = np.abs(pred_rgb - gt_rgb).max(axis=-1)
    return residual > threshold


def compute_reflective_asset_metrics(pred_rgb, gt_rgb, reflective_mask=None, lpips_value=None, refl_lpips_value=None):
    if pred_rgb is None or gt_rgb is None:
        reason = "missing_pred_or_gt_rgb"
        return [
            _metric_record("rendering", "psnr", None, "rendering_fidelity", reason, True),
            _metric_record("rendering", "ssim", None, "rendering_fidelity", reason, True),
            _metric_record("rendering", "lpips", None, "rendering_fidelity", "lpips_not_available", False),
            _metric_record("reflective_region", "refl_psnr", None, "reflective_region_fidelity", reason, True),
            _metric_record("reflective_region", "refl_ssim", None, "reflective_region_fidelity", reason, True),
            _metric_record("reflective_region", "refl_lpips", None, "reflective_region_fidelity", "lpips_not_available", False),
        ]

    pred_rgb = _as_float_array(pred_rgb)
    gt_rgb = _as_float_array(gt_rgb)
    if pred_rgb.shape != gt_rgb.shape:
        raise ValueError("pred_rgb and gt_rgb must have the same shape")

    metrics = [
        _metric_record("rendering", "psnr", psnr(pred_rgb, gt_rgb), "rendering_fidelity", higher_is_better=True),
        _metric_record("rendering", "ssim", ssim(pred_rgb, gt_rgb), "rendering_fidelity", higher_is_better=True),
        _metric_record(
            "rendering",
            "lpips",
            lpips_value,
            "rendering_fidelity",
            None if lpips_value is not None else "lpips_not_available",
            higher_is_better=False,
        ),
    ]

    if reflective_mask is None:
        reason = "reflective_mask_not_available"
        metrics.extend([
            _metric_record("reflective_region", "refl_psnr", None, "reflective_region_fidelity", reason, True),
            _metric_record("reflective_region", "refl_ssim", None, "reflective_region_fidelity", reason, True),
            _metric_record("reflective_region", "refl_lpips", None, "reflective_region_fidelity", "lpips_not_available", False),
        ])
    else:
        reflective_mask = np.asarray(reflective_mask).astype(bool)
        empty_reason = None if reflective_mask.any() else "empty_reflective_mask"
        metrics.extend([
            _metric_record(
                "reflective_region",
                "refl_psnr",
                psnr(pred_rgb, gt_rgb, reflective_mask) if reflective_mask.any() else None,
                "reflective_region_fidelity",
                empty_reason,
                True,
            ),
            _metric_record(
                "reflective_region",
                "refl_ssim",
                ssim(pred_rgb, gt_rgb, reflective_mask) if reflective_mask.any() else None,
                "reflective_region_fidelity",
                empty_reason,
                True,
            ),
            _metric_record(
                "reflective_region",
                "refl_lpips",
                refl_lpips_value,
                "reflective_region_fidelity",
                None if refl_lpips_value is not None else "lpips_not_available",
                False,
            ),
        ])
    return metrics


def _pairwise_squared_distance(a, b):
    diff = a[:, None, :] - b[None, :, :]
    return np.sum(diff * diff, axis=-1)


def compute_geometry_metrics(
    pred_points=None,
    gt_points=None,
    pred_normals=None,
    gt_normals=None,
    pred_depth=None,
    gt_depth=None,
    fscore_threshold=0.01,
):
    metrics = []
    if pred_points is None or gt_points is None:
        reason = "gt_geometry_not_available" if gt_points is None else "pred_geometry_not_available"
        metrics.append(_metric_record("geometry", "chamfer_distance", None, "surface_geometry_quality", reason, False))
        metrics.append(_metric_record("geometry", "f_score", None, "surface_geometry_quality", reason, True))
    else:
        pred_points = np.asarray(pred_points, dtype=np.float32).reshape(-1, 3)
        gt_points = np.asarray(gt_points, dtype=np.float32).reshape(-1, 3)
        if len(pred_points) == 0 or len(gt_points) == 0:
            metrics.append(_metric_record("geometry", "chamfer_distance", None, "surface_geometry_quality", "empty_point_set", False))
            metrics.append(_metric_record("geometry", "f_score", None, "surface_geometry_quality", "empty_point_set", True))
        else:
            dist2 = _pairwise_squared_distance(pred_points, gt_points)
            pred_to_gt = np.sqrt(dist2.min(axis=1))
            gt_to_pred = np.sqrt(dist2.min(axis=0))
            chamfer = pred_to_gt.mean() + gt_to_pred.mean()
            precision = (pred_to_gt < fscore_threshold).mean()
            recall = (gt_to_pred < fscore_threshold).mean()
            f_score = 0.0 if precision + recall <= 1e-12 else 2.0 * precision * recall / (precision + recall)
            metrics.append(_metric_record("geometry", "chamfer_distance", chamfer, "surface_geometry_quality", higher_is_better=False))
            metrics.append(_metric_record("geometry", "f_score", f_score, "surface_geometry_quality", higher_is_better=True))

    if pred_normals is None or gt_normals is None:
        reason = "gt_normal_not_available" if gt_normals is None else "pred_normal_not_available"
        metrics.append(_metric_record("geometry", "normal_mae", None, "normal_stability", reason, False))
    else:
        pred_normals = np.asarray(pred_normals, dtype=np.float32).reshape(-1, 3)
        gt_normals = np.asarray(gt_normals, dtype=np.float32).reshape(-1, 3)
        denom_pred = np.linalg.norm(pred_normals, axis=1, keepdims=True).clip(1e-6)
        denom_gt = np.linalg.norm(gt_normals, axis=1, keepdims=True).clip(1e-6)
        cos = np.sum((pred_normals / denom_pred) * (gt_normals / denom_gt), axis=1).clip(-1.0, 1.0)
        metrics.append(_metric_record("geometry", "normal_mae", np.degrees(np.arccos(cos)).mean(), "normal_stability", higher_is_better=False))

    if pred_depth is None or gt_depth is None:
        reason = "gt_depth_not_available" if gt_depth is None else "pred_depth_not_available"
        metrics.append(_metric_record("geometry", "depth_error", None, "depth_stability", reason, False))
    else:
        pred_depth = np.asarray(pred_depth, dtype=np.float32)
        gt_depth = np.asarray(gt_depth, dtype=np.float32)
        valid = np.isfinite(pred_depth) & np.isfinite(gt_depth) & (gt_depth > 0)
        value = None if not valid.any() else np.abs(pred_depth[valid] - gt_depth[valid]).mean()
        reason = None if valid.any() else "empty_valid_depth"
        metrics.append(_metric_record("geometry", "depth_error", value, "depth_stability", reason, False))
    return metrics


def compute_texture_material_metrics(
    highlight_leakage_mask=None,
    albedo=None,
    gt_albedo=None,
    roughness=None,
    gt_roughness=None,
    material_views=None,
):
    metrics = []
    if highlight_leakage_mask is None:
        metrics.append(_metric_record("texture_material", "highlight_leakage_score", None, "specular_free_texture", "highlight_leakage_mask_not_available", False))
    else:
        metrics.append(_metric_record("texture_material", "highlight_leakage_score", _as_float_array(highlight_leakage_mask).mean(), "specular_free_texture", higher_is_better=False))

    if albedo is None or gt_albedo is None:
        reason = "gt_albedo_not_available" if gt_albedo is None else "pred_albedo_not_available"
        metrics.append(_metric_record("texture_material", "albedo_error", None, "specular_free_texture", reason, False))
    else:
        metrics.append(_metric_record("texture_material", "albedo_error", np.abs(_as_float_array(albedo) - _as_float_array(gt_albedo)).mean(), "specular_free_texture", higher_is_better=False))

    if roughness is None or gt_roughness is None:
        reason = "gt_roughness_not_available" if gt_roughness is None else "pred_roughness_not_available"
        metrics.append(_metric_record("texture_material", "roughness_error", None, "pbr_material_quality", reason, False))
    else:
        metrics.append(_metric_record("texture_material", "roughness_error", np.abs(_as_float_array(roughness) - _as_float_array(gt_roughness)).mean(), "pbr_material_quality", higher_is_better=False))

    if material_views is None or len(material_views) < 2:
        metrics.append(_metric_record("texture_material", "material_consistency", None, "material_view_consistency", "need_at_least_two_material_views", False))
    else:
        arrays = [_as_float_array(view) for view in material_views]
        stack = np.stack(arrays, axis=0)
        metrics.append(_metric_record("texture_material", "material_consistency", stack.var(axis=0).mean(), "material_view_consistency", higher_is_better=False))
    return metrics


def compute_runtime_metrics(training_time=None, peak_memory=None, render_fps=None):
    return [
        _metric_record("runtime", "training_time", training_time, "runtime_cost", "training_time_not_available" if training_time is None else None, False),
        _metric_record("runtime", "peak_memory", peak_memory, "runtime_cost", "peak_memory_not_available" if peak_memory is None else None, False),
        _metric_record("runtime", "render_fps", render_fps, "runtime_cost", "render_fps_not_available" if render_fps is None else None, True),
    ]


def save_reflective_mask(mask, path):
    mask = np.asarray(mask).astype(np.float32)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    imageio.imwrite(path, (mask * 255.0 + 0.5).astype(np.uint8))


def write_failure_summary(metrics, path):
    unavailable = [metric for metric in metrics if metric.get("value") is None]
    lines = [
        "# SRD-GS Failure Summary",
        "",
        "This artifact records metric availability and failure-panel source evidence.",
        "",
        "## Unavailable Metrics",
        "",
    ]
    if unavailable:
        for metric in unavailable:
            lines.append(
                "- {category}/{name}: {reason}".format(
                    category=metric.get("category"),
                    name=metric.get("name"),
                    reason=metric.get("not_available_reason") or "not_available",
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This file is an instrumentation artifact, not a paper-scale quality claim.",
            "- Inspect the referenced metrics before promoting any conclusion.",
            "",
        ]
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def write_metrics_outputs(metrics, output_dir, reflective_mask=None, mask_source=None):
    os.makedirs(output_dir, exist_ok=True)
    qualitative_dir = os.path.join(output_dir, "qualitative_panels")
    failure_dir = os.path.join(output_dir, "failure_case_panels")
    os.makedirs(qualitative_dir, exist_ok=True)
    os.makedirs(failure_dir, exist_ok=True)

    reflective_mask_path = None
    if reflective_mask is not None:
        reflective_mask_path = os.path.join(output_dir, "reflective_mask.png")
        save_reflective_mask(reflective_mask, reflective_mask_path)

    metrics_json = os.path.join(output_dir, "metrics.json")
    metrics_csv = os.path.join(output_dir, "metrics.csv")
    failure_summary = os.path.join(failure_dir, "failure_summary.md")
    payload = {
        "metrics": metrics,
        "reflective_mask": {
            "source": mask_source,
            "path": os.path.abspath(reflective_mask_path) if reflective_mask_path else None,
        },
    }
    with open(metrics_json, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    with open(metrics_csv, "w", newline="", encoding="utf-8") as handle:
        fieldnames = ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow({field: metric.get(field) for field in fieldnames})
    write_failure_summary(metrics, failure_summary)
    return {
        "metrics_json": metrics_json,
        "metrics_csv": metrics_csv,
        "qualitative_panels": qualitative_dir,
        "failure_case_panels": failure_dir,
        "failure_summary": failure_summary,
        "reflective_mask": reflective_mask_path,
    }
