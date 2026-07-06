#!/usr/bin/env python3
"""Evaluate exported Ref-GS PBR/render/component RGB buffers against GT."""

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

PREDICTION_KEYS = ["pbr_rgb", "render", "diffuse", "specular", "spec", "albedo"]


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

        h, w = pred.shape[:2]
        if min(h, w) < 7:
            return "NA"
        return float(structural_similarity(gt, pred, channel_axis=2, data_range=1.0))
    except Exception:
        return "NA"


def json_value(value):
    if isinstance(value, float):
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        if math.isnan(value):
            return "NA"
    return value


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
        for row_id, pred, gt in pairs:
            pred_t = torch.from_numpy(pred).permute(2, 0, 1)[None].to(device) * 2 - 1
            gt_t = torch.from_numpy(gt).permute(2, 0, 1)[None].to(device) * 2 - 1
            with torch.no_grad():
                scores[row_id] = float(loss_fn(pred_t, gt_t).item())
        return scores, None
    except Exception as exc:
        return {}, f"lpips_failed: {exc}"


def path_for_buffer(view, key):
    buffers = view.get("buffers", {})
    entry = buffers.get(key, {})
    if entry.get("path"):
        return entry["path"]
    paths = entry.get("paths", {})
    if paths.get("png"):
        return paths["png"]
    return view.get("files", {}).get(key)


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
    return row, (f"{view}::{key}", pred, gt)


def summarize(rows, notes):
    summary = {"notes": notes, "targets": {}}
    for target in sorted(set(row["target"] for row in rows)):
        target_rows = [row for row in rows if row["target"] == target]
        valid = [row for row in target_rows if row["status"] == "ok"]
        summary["targets"][target] = {
            "valid_views": len(valid),
            "total_views": len(target_rows),
        }
        for metric in ("mae", "psnr", "ssim", "lpips"):
            vals = [row[metric] for row in valid if isinstance(row[metric], (int, float))]
            if vals and any(math.isinf(v) for v in vals):
                metric_value = "inf" if all(v >= 0 for v in vals if math.isinf(v)) else "NA"
            else:
                finite = [v for v in vals if np.isfinite(v)]
                metric_value = float(np.mean(finite)) if finite else "NA"
            summary["targets"][target][metric] = json_value(metric_value)
    summary["pbr_rgb_vs_render_gap"] = compute_gap(summary)
    return summary


def compute_gap(summary):
    pbr = summary["targets"].get("pbr_rgb")
    render = summary["targets"].get("render")
    if not pbr or not render or pbr.get("valid_views", 0) == 0 or render.get("valid_views", 0) == 0:
        return {
            "status": "NA",
            "reason": "pbr_rgb or render has no valid RGB views",
            "psnr_delta": "NA",
            "mae_delta": "NA",
            "lpips_delta": "NA",
        }

    def delta(metric):
        a = pbr.get(metric)
        b = render.get(metric)
        if a == "NA" or b == "NA":
            return "NA"
        if a == "inf":
            return "inf"
        if b == "inf":
            return "-inf"
        return json_value(float(a) - float(b))

    return {
        "status": "ok",
        "psnr_delta": delta("psnr"),
        "mae_delta": delta("mae"),
        "lpips_delta": delta("lpips"),
    }


def collect_missing(manifest, rows):
    missing = []
    for view in manifest.get("views", []):
        view_name = view.get("image_name", str(view.get("index", "NA")))
        buffers = view.get("buffers", {})
        for key, entry in sorted(buffers.items()):
            if entry.get("missing") or not entry.get("exported"):
                missing.append(
                    {
                        "view": view_name,
                        "key": key,
                        "reason": entry.get("reason", "missing"),
                    }
                )
    for row in rows:
        if row["status"] != "ok":
            missing.append({"view": row["view"], "key": row["target"], "reason": row["status"]})
    return missing


def write_markdown(path, summary):
    lines = ["# PBR Evaluation Summary", ""]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    lines += ["", "| Target | Valid Views | MAE | PSNR | SSIM | LPIPS |", "| -- | -- | -- | -- | -- | -- |"]
    for target, item in sorted(summary["targets"].items()):
        lines.append(
            f"| {target} | {item['valid_views']}/{item['total_views']} | {item['mae']} | {item['psnr']} | {item['ssim']} | {item['lpips']} |"
        )
    gap = summary["pbr_rgb_vs_render_gap"]
    lines += [
        "",
        "## pbr_rgb_vs_render_gap",
        "",
        f"- status: `{gap['status']}`",
        f"- reason: `{gap.get('reason', '')}`",
        f"- pbr_rgb_psnr - render_psnr: `{gap['psnr_delta']}`",
        f"- pbr_rgb_mae - render_mae: `{gap['mae_delta']}`",
        f"- pbr_rgb_lpips - render_lpips: `{gap['lpips_delta']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_missing(path, missing):
    lines = ["# Missing Buffers", ""]
    if not missing:
        lines.append("No missing buffers were reported.")
    else:
        lines += ["| View | Key | Reason |", "| -- | -- | -- |"]
        for item in missing:
            lines.append(f"| {item['view']} | {item['key']} | {item['reason']} |")
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
    manifest = {"views": []}
    if not manifest_path.exists():
        notes.append(f"manifest_missing: {manifest_path}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("dry_run"):
            notes.append("export_manifest_is_dry_run")
        for view in manifest.get("views", []):
            view_name = view.get("image_name", str(view.get("index", "NA")))
            gt_path = path_for_buffer(view, "gt")
            for key in PREDICTION_KEYS:
                row, pair = metric_row(view_name, key, path_for_buffer(view, key), gt_path)
                rows.append(row)
                if pair:
                    lpips_pairs.append(pair)
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
            row_id = f"{row['view']}::{row['target']}"
            if row_id in scores:
                row["lpips"] = scores[row_id]

    with (out / "per_view_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows, notes)
    missing = collect_missing(manifest, rows)
    (out / "summary_metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(out / "summary_metrics.md", summary)
    write_missing(out / "missing_buffers.md", missing)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
