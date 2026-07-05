#!/usr/bin/env python3
"""Evaluate predicted geometry against GT geometry with safe NA outputs."""

import argparse
import json
from pathlib import Path

import numpy as np


def load_points(path, num_samples):
    import trimesh

    geom = trimesh.load(str(path), process=False)
    if isinstance(geom, trimesh.Scene):
        geoms = [g for g in geom.geometry.values()]
        geom = trimesh.util.concatenate(geoms) if geoms else None
    if geom is None:
        raise ValueError(f"no geometry in {path}")
    if hasattr(geom, "faces") and len(getattr(geom, "faces", [])) > 0:
        count = min(num_samples, max(num_samples, 1))
        points, _ = trimesh.sample.sample_surface(geom, count)
        return np.asarray(points, dtype=np.float64)
    vertices = np.asarray(geom.vertices, dtype=np.float64)
    if vertices.shape[0] > num_samples:
        rng = np.random.default_rng(0)
        vertices = vertices[rng.choice(vertices.shape[0], size=num_samples, replace=False)]
    return vertices


def bbox_stats(points):
    if points.size == 0:
        return {"count": 0, "bbox_min": "NA", "bbox_max": "NA", "bbox_diag": "NA"}
    bmin = points.min(axis=0)
    bmax = points.max(axis=0)
    return {
        "count": int(points.shape[0]),
        "bbox_min": bmin.tolist(),
        "bbox_max": bmax.tolist(),
        "bbox_diag": float(np.linalg.norm(bmax - bmin)),
    }


def compute_metrics(pred, gt, thresholds):
    from scipy.spatial import cKDTree

    pred_tree = cKDTree(pred)
    gt_tree = cKDTree(gt)
    pred_to_gt, _ = gt_tree.query(pred, k=1)
    gt_to_pred, _ = pred_tree.query(gt, k=1)
    metrics = {
        "chamfer_l1": float((pred_to_gt.mean() + gt_to_pred.mean()) * 0.5),
        "pred_to_gt_mean": float(pred_to_gt.mean()),
        "gt_to_pred_mean": float(gt_to_pred.mean()),
        "thresholds": {},
    }
    for threshold in thresholds:
        precision = float(np.mean(pred_to_gt < threshold))
        recall = float(np.mean(gt_to_pred < threshold))
        fscore = 0.0 if precision + recall == 0 else float(2 * precision * recall / (precision + recall))
        metrics["thresholds"][str(threshold)] = {
            "precision": precision,
            "recall": recall,
            "fscore": fscore,
        }
    return metrics


def write_outputs(out, payload):
    out.mkdir(parents=True, exist_ok=True)
    (out / "geometry_metrics.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# Geometry Metrics", "", f"Status: `{payload['status']}`", ""]
    if payload.get("reason"):
        lines.append(f"Reason: {payload['reason']}")
        lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- pred: `{payload['pred']}`")
    lines.append(f"- gt: `{payload['gt']}`")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    for key, value in payload.get("metrics", {}).items():
        if key != "thresholds":
            lines.append(f"- {key}: {value}")
    if payload.get("metrics", {}).get("thresholds"):
        lines.append("")
        lines.append("| Threshold | Precision | Recall | F-score |")
        lines.append("| -- | -- | -- | -- |")
        for threshold, item in payload["metrics"]["thresholds"].items():
            lines.append(f"| {threshold} | {item['precision']} | {item['recall']} | {item['fscore']} |")
    (out / "geometry_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True)
    parser.add_argument("--gt", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--num_samples", type=int, default=200000)
    parser.add_argument("--thresholds", nargs="+", type=float, default=[0.001, 0.002, 0.005, 0.01])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = {
        "pred": args.pred,
        "gt": args.gt,
        "num_samples": args.num_samples,
        "thresholds": args.thresholds,
        "status": "NA",
        "reason": "",
        "pred_stats": {},
        "gt_stats": {},
        "metrics": {},
        "dry_run": bool(args.dry_run),
    }
    pred_path = Path(args.pred)
    gt_path = Path(args.gt)
    if args.dry_run:
        payload["status"] = "dry_run"
        payload["reason"] = "paths checked only"
        payload["pred_exists"] = pred_path.exists()
        payload["gt_exists"] = gt_path.exists()
        write_outputs(Path(args.out), payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if not pred_path.exists() or not gt_path.exists():
        payload["reason"] = f"missing input: pred_exists={pred_path.exists()} gt_exists={gt_path.exists()}"
        write_outputs(Path(args.out), payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    try:
        pred = load_points(pred_path, args.num_samples)
        gt = load_points(gt_path, args.num_samples)
        payload["pred_stats"] = bbox_stats(pred)
        payload["gt_stats"] = bbox_stats(gt)
        payload["metrics"] = compute_metrics(pred, gt, args.thresholds)
        payload["status"] = "ok"
    except Exception as exc:
        payload["reason"] = str(exc)
    write_outputs(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
