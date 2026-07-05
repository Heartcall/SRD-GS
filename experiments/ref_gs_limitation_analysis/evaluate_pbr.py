#!/usr/bin/env python3
"""Evaluate exported Ref-GS PBR and stock render images against GT."""

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


def load_image(path):
    if not path or not Path(path).exists():
        return None
    arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    return arr


def mae(pred, gt):
    return float(np.mean(np.abs(pred - gt)))


def psnr(pred, gt):
    mse = float(np.mean((pred - gt) ** 2))
    if mse <= 1e-12:
        return float("inf")
    return float(-10.0 * math.log10(mse))


def ssim_score(pred, gt):
    try:
        from skimage.metrics import structural_similarity

        return float(structural_similarity(gt, pred, channel_axis=2, data_range=1.0))
    except Exception:
        return "NA"


def maybe_lpips(pairs):
    try:
        import torch
        import lpips
    except Exception as exc:
        return {}, f"lpips_unavailable: {exc}"
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        loss_fn = lpips.LPIPS(net="alex").to(device)
        scores = {}
        for key, pred, gt in pairs:
            pred_t = torch.from_numpy(pred).permute(2, 0, 1)[None].to(device) * 2 - 1
            gt_t = torch.from_numpy(gt).permute(2, 0, 1)[None].to(device) * 2 - 1
            with torch.no_grad():
                scores[key] = float(loss_fn(pred_t, gt_t).item())
        return scores, None
    except Exception as exc:
        return {}, f"lpips_failed: {exc}"


def metric_row(view, key, pred_path, gt_path):
    row = {
        "view": view,
        "target": key,
        "pred_path": pred_path or "NA",
        "gt_path": gt_path or "NA",
        "mae": "NA",
        "psnr": "NA",
        "ssim": "NA",
        "lpips": "NA",
        "status": "missing",
    }
    pred = load_image(pred_path)
    gt = load_image(gt_path)
    if pred is None or gt is None:
        return row, None
    if pred.shape != gt.shape:
        row["status"] = f"shape_mismatch:{pred.shape}!={gt.shape}"
        return row, None
    row["mae"] = mae(pred, gt)
    row["psnr"] = psnr(pred, gt)
    row["ssim"] = ssim_score(pred, gt)
    row["status"] = "ok"
    return row, (key, pred, gt)


def summarize(rows, notes):
    summary = {"notes": notes, "targets": {}}
    for target in sorted(set(row["target"] for row in rows)):
        valid = [row for row in rows if row["target"] == target and row["status"] == "ok"]
        summary["targets"][target] = {
            "valid_views": len(valid),
            "total_views": sum(1 for row in rows if row["target"] == target),
        }
        for metric in ("mae", "psnr", "ssim", "lpips"):
            vals = [row[metric] for row in valid if isinstance(row[metric], (int, float)) and np.isfinite(row[metric])]
            summary["targets"][target][metric] = float(np.mean(vals)) if vals else "NA"
    return summary


def write_markdown(path, summary):
    lines = ["# PBR Evaluation Summary", ""]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    lines += ["", "| Target | Valid Views | MAE | PSNR | SSIM | LPIPS |", "| -- | -- | -- | -- | -- | -- |"]
    for target, item in sorted(summary["targets"].items()):
        lines.append(
            f"| {target} | {item['valid_views']}/{item['total_views']} | {item['mae']} | {item['psnr']} | {item['ssim']} | {item['lpips']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export_dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip-lpips", action="store_true")
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = export_dir / "manifest.json"
    notes = []
    rows = []
    lpips_pairs = []
    if not manifest_path.exists():
        notes.append(f"manifest_missing: {manifest_path}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("dry_run"):
            notes.append("export_manifest_is_dry_run")
        for view in manifest.get("views", []):
            files = view.get("files", {})
            gt_path = files.get("gt")
            for key in ("pbr_rgb", "render", "albedo"):
                row, pair = metric_row(view.get("image_name", str(view.get("index", "NA"))), key, files.get(key), gt_path)
                rows.append(row)
                if pair:
                    lpips_pairs.append((f"{row['view']}::{key}", pair[1], pair[2]))
    if not rows:
        rows.append(
            {
                "view": "NA",
                "target": "pbr_rgb",
                "pred_path": "NA",
                "gt_path": "NA",
                "mae": "NA",
                "psnr": "NA",
                "ssim": "NA",
                "lpips": "NA",
                "status": "no_exported_views",
            }
        )
    if args.skip_lpips:
        notes.append("lpips_skipped")
    else:
        scores, note = maybe_lpips(lpips_pairs)
        if note:
            notes.append(note)
        for row in rows:
            key = f"{row['view']}::{row['target']}"
            if key in scores:
                row["lpips"] = scores[key]

    with (out / "per_view_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows, notes)
    (out / "summary_metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(out / "summary_metrics.md", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
