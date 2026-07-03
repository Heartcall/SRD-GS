import argparse
import csv
import importlib
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np


TARGETS = {
    "rendering/lpips": {
        "category": "rendering",
        "name": "lpips",
        "supports_hypothesis": "rendering_fidelity",
        "higher_is_better": False,
    },
    "reflective_region/refl_lpips": {
        "category": "reflective_region",
        "name": "refl_lpips",
        "supports_hypothesis": "reflective_region_fidelity",
        "higher_is_better": False,
    },
}


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _resolve(root, relative_path):
    if not relative_path:
        return None
    path = Path(relative_path)
    return path if path.is_absolute() else Path(root) / path


def _as_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _read_rgb(path):
    image = imageio.imread(path)
    image = np.asarray(image)
    if image.ndim == 2:
        image = np.repeat(image[..., None], 3, axis=-1)
    if image.ndim == 3 and image.shape[-1] > 3:
        image = image[..., :3]
    image = image.astype(np.float32)
    if image.max(initial=0.0) > 1.5:
        image = image / 255.0
    return np.clip(image, 0.0, 1.0)


def _read_mask(path):
    if path is None or not path.exists():
        return None
    mask = np.asarray(imageio.imread(path))
    if mask.ndim == 3:
        mask = mask[..., 0]
    return mask > 127


def _to_tensor(torch, image):
    tensor = torch.from_numpy(image.transpose(2, 0, 1)).float().unsqueeze(0)
    return tensor * 2.0 - 1.0


def _frame_plan(manifest, eval_pairs_dir, max_frames):
    frames = manifest.get("frames") or []
    if max_frames is not None:
        frames = frames[:max_frames]
    planned = []
    for frame in frames:
        pred = _resolve(eval_pairs_dir, frame.get("pred_rgb"))
        gt = _resolve(eval_pairs_dir, frame.get("gt_rgb"))
        mask = _resolve(eval_pairs_dir, frame.get("reflective_mask"))
        planned.append(
            {
                "frame_index": frame.get("index"),
                "pred_rgb": str(pred) if pred else "",
                "gt_rgb": str(gt) if gt else "",
                "reflective_mask": str(mask) if mask else "",
                "pred_available": pred is not None and pred.exists(),
                "gt_available": gt is not None and gt.exists(),
                "reflective_mask_available": mask is not None and mask.exists(),
            }
        )
    return planned


def _metric_value_rows(values_payload):
    return values_payload.get("frames") or []


def _compute_frame_metrics(manifest, eval_pairs_dir, max_frames, lpips_net, device):
    torch = importlib.import_module("torch")
    lpips = importlib.import_module("lpips")
    loss_fn = lpips.LPIPS(net=lpips_net, verbose=False).to(device)
    loss_fn.eval()
    frame_rows = []
    for planned in _frame_plan(manifest, eval_pairs_dir, max_frames):
        pred = _read_rgb(planned["pred_rgb"])
        gt = _read_rgb(planned["gt_rgb"])
        mask = _read_mask(Path(planned["reflective_mask"])) if planned["reflective_mask"] else None
        with torch.no_grad():
            pred_tensor = _to_tensor(torch, pred).to(device)
            gt_tensor = _to_tensor(torch, gt).to(device)
            lpips_value = float(loss_fn(pred_tensor, gt_tensor).detach().cpu().item())
            refl_value = None
            mask_pixels = 0
            if mask is not None and mask.any():
                mask_pixels = int(mask.sum())
                masked_pred = pred.copy()
                masked_gt = gt.copy()
                masked_pred[~mask] = gt[~mask]
                masked_gt[~mask] = gt[~mask]
                refl_value = float(
                    loss_fn(_to_tensor(torch, masked_pred).to(device), _to_tensor(torch, masked_gt).to(device))
                    .detach()
                    .cpu()
                    .item()
                )
        frame_rows.append(
            {
                "frame_index": planned["frame_index"],
                "lpips": lpips_value,
                "refl_lpips": refl_value,
                "reflective_mask_pixels": mask_pixels,
            }
        )
    return frame_rows


def _mean(values):
    clean = [float(value) for value in values if value is not None and value != ""]
    if not clean:
        return None
    return sum(clean) / float(len(clean))


def _summary_from_frame_rows(frame_rows, args, source_unavailable_count):
    lpips_value = _mean([row.get("lpips") for row in frame_rows])
    refl_lpips_value = _mean([row.get("refl_lpips") for row in frame_rows])
    return {
        "milestone": "M38",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "dry_run_first_required": True,
        "metrics_computed": True,
        "source_metrics_overwritten": False,
        "metric_scope": "bounded_lpips_compute",
        "lpips": lpips_value,
        "refl_lpips": refl_lpips_value,
        "frame_count": len(frame_rows),
        "source_unavailable_lpips_count": source_unavailable_count,
        "metrics_csv": str(args.metrics_csv),
        "metrics_json": str(args.metrics_json),
        "manifest": str(args.manifest),
        "eval_pairs_dir": str(args.eval_pairs_dir),
        "gate_json": str(args.gate_json),
        "supported_conclusions": [
            "LPIPS and Refl-LPIPS values were computed for the bounded M32 two-frame artifact set.",
            "The values are written only to separate M38 augmented outputs; source M32 metrics remain unchanged.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
            "GT material/depth or runtime-cost blockers are solved.",
        ],
        "recommended_next_milestone": (
            "Use M38 augmented metrics in the next bounded diagnostic synthesis, or choose another remaining "
            "unavailable-metric contract such as accepted GT depth/material artifacts, material-view manifests, "
            "or runtime-cost logging."
        ),
    }


def _source_unavailable_lpips_count(metrics_rows):
    count = 0
    for row in metrics_rows:
        metric_id = "{}/{}".format(row.get("category", ""), row.get("name", ""))
        if metric_id in TARGETS and (row.get("not_available_reason") or row.get("value") in ("", None)):
            count += 1
    return count


def _augment_rows(metrics_rows, lpips_value, refl_lpips_value):
    fieldnames = [
        "category",
        "name",
        "value",
        "supports_hypothesis",
        "higher_is_better",
        "not_available_reason",
        "metric_scope",
        "source_metric_state",
    ]
    output = []
    replacements = {
        "rendering/lpips": lpips_value,
        "reflective_region/refl_lpips": refl_lpips_value,
    }
    for row in metrics_rows:
        metric_id = "{}/{}".format(row.get("category", ""), row.get("name", ""))
        out = {field: row.get(field, "") for field in fieldnames}
        out["metric_scope"] = row.get("metric_scope", "")
        out["source_metric_state"] = "copied"
        if metric_id in replacements and replacements[metric_id] is not None:
            out["value"] = "{:.12g}".format(replacements[metric_id])
            out["not_available_reason"] = ""
            out["metric_scope"] = "bounded_lpips_compute"
            out["source_metric_state"] = "augmented_from_m38"
            target = TARGETS[metric_id]
            out["supports_hypothesis"] = target["supports_hypothesis"]
            out["higher_is_better"] = str(target["higher_is_better"])
        output.append(out)
    return output, fieldnames


def _augment_json(metrics_json_path, lpips_value, refl_lpips_value):
    payload = _read_json(metrics_json_path)
    replacements = {
        "rendering/lpips": lpips_value,
        "reflective_region/refl_lpips": refl_lpips_value,
    }
    metrics = []
    for row in payload.get("metrics") or []:
        out = dict(row)
        metric_id = "{}/{}".format(out.get("category", ""), out.get("name", ""))
        if metric_id in replacements and replacements[metric_id] is not None:
            out["value"] = float(replacements[metric_id])
            out["not_available_reason"] = None
            out["metric_scope"] = "bounded_lpips_compute"
            out["source_metric_state"] = "augmented_from_m38"
        metrics.append(out)
    payload["metrics"] = metrics
    payload["m38_lpips_compute"] = {
        "paper_scale_gate": "NO-GO",
        "metric_scope": "bounded_lpips_compute",
        "source_metrics_overwritten": False,
    }
    return payload


def _write_report(path, summary):
    lines = [
        "# Milestone 38 LPIPS augmented metrics",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "Source metrics overwritten: false",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Summary",
        "",
        "- Frames: {}".format(summary["frame_count"]),
        "- LPIPS: {}".format(summary["lpips"]),
        "- Refl-LPIPS: {}".format(summary["refl_lpips"]),
        "- Metric scope: {}".format(summary["metric_scope"]),
        "",
        "## Claim Boundary",
        "",
        "- Supported: bounded LPIPS/Refl-LPIPS values for existing M32 render-eval artifacts.",
        "- Unsupported: SRD-GS superiority, rendering recovery, paper-scale claims, or any claim beyond this two-frame diagnostic set.",
        "- Source M32 metrics remain unchanged.",
        "",
        "## Recommended Next Milestone",
        "",
        summary["recommended_next_milestone"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_plan(args, manifest, gate, metrics_rows):
    planned = _frame_plan(manifest, args.eval_pairs_dir, args.max_frames)
    ready = gate.get("dependency_gate_status") == "ready_for_bounded_compute"
    payload = {
        "milestone": "M38",
        "paper_scale_gate": "NO-GO",
        "dry_run": True,
        "metrics_computed": False,
        "source_metrics_overwritten": False,
        "gate_ready": ready,
        "planned_frame_count": len(planned),
        "planned_frames": planned,
        "source_unavailable_lpips_count": _source_unavailable_lpips_count(metrics_rows),
        "failure_conditions": [
            "Do not overwrite source M32 metrics.",
            "Do not run training, rendering, mesh extraction, texture export, or broad evaluation.",
            "Do not promote bounded LPIPS values to SRD-GS superiority or paper-scale claims.",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "lpips_compute_plan.json", payload)
    _write_csv(
        args.output_dir / "lpips_compute_plan.csv",
        [
            {
                "frame_index": row["frame_index"],
                "pred_available": str(row["pred_available"]).lower(),
                "gt_available": str(row["gt_available"]).lower(),
                "reflective_mask_available": str(row["reflective_mask_available"]).lower(),
            }
            for row in planned
        ],
        ["frame_index", "pred_available", "gt_available", "reflective_mask_available"],
    )
    lines = [
        "# Milestone 38 LPIPS compute dry run",
        "",
        "Paper-scale gate: NO-GO",
        "Metrics computed: false",
        "Source metrics overwritten: false",
        "",
        "- Gate ready: {}".format(str(ready).lower()),
        "- Planned frames: {}".format(len(planned)),
        "",
    ]
    (args.output_dir / "lpips_compute_plan.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Compute bounded LPIPS augmented metrics without overwriting source metrics.")
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--metrics_json", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--eval_pairs_dir", required=True, type=Path)
    parser.add_argument("--gate_json", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--dry_run", action="store_true", default=False)
    parser.add_argument("--metric_values_json", default=None, type=Path)
    parser.add_argument("--lpips_net", default="alex")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max_frames", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    manifest = _read_json(args.manifest)
    gate = _read_json(args.gate_json)
    if args.dry_run:
        _write_plan(args, manifest, gate, metrics_rows)
        print(f"Wrote {args.output_dir / 'lpips_compute_plan.json'}")
        print(f"Wrote {args.output_dir / 'lpips_compute_plan.csv'}")
        print(f"Wrote {args.output_dir / 'lpips_compute_plan.md'}")
        return
    if gate.get("dependency_gate_status") != "ready_for_bounded_compute":
        raise RuntimeError("LPIPS dependency gate is not ready_for_bounded_compute")
    if args.metric_values_json:
        frame_rows = _metric_value_rows(_read_json(args.metric_values_json))
    else:
        frame_rows = _compute_frame_metrics(
            manifest,
            args.eval_pairs_dir,
            args.max_frames,
            args.lpips_net,
            args.device,
        )
    source_unavailable_count = _source_unavailable_lpips_count(metrics_rows)
    summary = _summary_from_frame_rows(frame_rows, args, source_unavailable_count)
    augmented_rows, augmented_fieldnames = _augment_rows(metrics_rows, summary["lpips"], summary["refl_lpips"])
    augmented_json = _augment_json(args.metrics_json, summary["lpips"], summary["refl_lpips"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "lpips_frame_metrics.csv",
        frame_rows,
        ["frame_index", "lpips", "refl_lpips", "reflective_mask_pixels"],
    )
    _write_csv(args.output_dir / "lpips_augmented_metrics.csv", augmented_rows, augmented_fieldnames)
    _write_json(args.output_dir / "lpips_augmented_metrics.json", augmented_json)
    _write_json(args.output_dir / "lpips_compute_summary.json", summary)
    _write_report(args.output_dir / "lpips_compute_summary.md", summary)
    print(f"Wrote {args.output_dir / 'lpips_frame_metrics.csv'}")
    print(f"Wrote {args.output_dir / 'lpips_augmented_metrics.csv'}")
    print(f"Wrote {args.output_dir / 'lpips_augmented_metrics.json'}")
    print(f"Wrote {args.output_dir / 'lpips_compute_summary.json'}")
    print(f"Wrote {args.output_dir / 'lpips_compute_summary.md'}")


if __name__ == "__main__":
    main()
