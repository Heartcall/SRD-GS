import argparse
import csv
import importlib
import importlib.util
import json
from pathlib import Path


TRUE = "true"
FALSE = "false"
TARGET_METRICS = {
    "rendering/lpips": {
        "requires_reflective_mask": False,
        "next_action": "run a bounded dry-run-first LPIPS metric computation pass without overwriting source metrics",
    },
    "reflective_region/refl_lpips": {
        "requires_reflective_mask": True,
        "next_action": "run a bounded dry-run-first reflective-region LPIPS pass with explicit mask provenance",
    },
}


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "category",
        "name",
        "status",
        "source_not_available_reason",
        "dependency_import_available",
        "dependency_model_init_available",
        "render_pair_available",
        "reflective_mask_available",
        "metrics_computed",
        "next_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _bool_text(value):
    return TRUE if bool(value) else FALSE


def _metric_id(row):
    return "{}/{}".format(row.get("category", ""), row.get("name", ""))


def _resolve(root, relative_path):
    if not relative_path:
        return None
    path = Path(relative_path)
    return path if path.is_absolute() else Path(root) / path


def _frame_files_available(manifest, eval_pairs_dir, keys):
    frames = manifest.get("frames") or []
    if not frames:
        return False
    for frame in frames:
        for key in keys:
            path = _resolve(eval_pairs_dir, frame.get(key))
            if path is None or not path.exists():
                return False
    return True


def _render_pair_available(manifest, eval_pairs_dir):
    return _frame_files_available(manifest, eval_pairs_dir, ["pred_rgb", "gt_rgb"])


def _reflective_mask_available(manifest, eval_pairs_dir):
    mask_info = manifest.get("reflective_mask") or {}
    if mask_info.get("available") is False:
        return False
    frame_masks = _frame_files_available(manifest, eval_pairs_dir, ["reflective_mask"])
    top_level_mask = _resolve(eval_pairs_dir, mask_info.get("path"))
    return frame_masks or (top_level_mask is not None and top_level_mask.exists())


def _probe_lpips_dependency(net):
    result = {
        "lpips_import_available": False,
        "lpips_origin": "",
        "torch_import_available": False,
        "torch_version": "",
        "model_init_attempted": False,
        "model_init_available": False,
        "model_init_error": "",
    }
    lpips_spec = importlib.util.find_spec("lpips")
    result["lpips_import_available"] = lpips_spec is not None
    result["lpips_origin"] = getattr(lpips_spec, "origin", "") if lpips_spec else ""
    torch_spec = importlib.util.find_spec("torch")
    result["torch_import_available"] = torch_spec is not None
    if torch_spec is not None:
        torch = importlib.import_module("torch")
        result["torch_version"] = getattr(torch, "__version__", "")
    if lpips_spec is None or torch_spec is None:
        return result
    result["model_init_attempted"] = True
    try:
        lpips = importlib.import_module("lpips")
        lpips.LPIPS(net=net, verbose=False)
        result["model_init_available"] = True
    except Exception as exc:  # pragma: no cover - host dependency behavior varies.
        result["model_init_error"] = "{}: {}".format(exc.__class__.__name__, exc)
    return result


def _load_probe(probe_json, net):
    if probe_json:
        return _read_json(probe_json)
    return _probe_lpips_dependency(net)


def _classify_metric(row, probe, render_pair_available, reflective_mask_available):
    metric_id = _metric_id(row)
    target = TARGET_METRICS[metric_id]
    dependency_import = bool(probe.get("lpips_import_available")) and bool(probe.get("torch_import_available"))
    dependency_model = bool(probe.get("model_init_available"))
    needs_mask = target["requires_reflective_mask"]
    has_mask = reflective_mask_available if needs_mask else True
    if not render_pair_available:
        status = "blocked_missing_render_pairs"
        next_action = "repair render-eval pred/gt RGB artifacts before LPIPS computation"
    elif needs_mask and not has_mask:
        status = "blocked_missing_reflective_mask"
        next_action = "provide reflective-region masks before refl-LPIPS computation"
    elif not dependency_import:
        status = "blocked_missing_dependency"
        next_action = "install or expose torch and lpips in the ref_gs environment before computation"
    elif not dependency_model:
        status = "blocked_lpips_model_init"
        next_action = "repair local LPIPS model/weight initialization before computation"
    else:
        status = "ready_for_bounded_compute"
        next_action = target["next_action"]
    return {
        "category": row.get("category", ""),
        "name": row.get("name", ""),
        "status": status,
        "source_not_available_reason": row.get("not_available_reason", ""),
        "dependency_import_available": _bool_text(dependency_import),
        "dependency_model_init_available": _bool_text(dependency_model),
        "render_pair_available": _bool_text(render_pair_available),
        "reflective_mask_available": _bool_text(has_mask),
        "metrics_computed": FALSE,
        "next_action": next_action,
    }


def build_gate(metrics_rows, manifest, eval_pairs_dir, probe):
    render_pair = _render_pair_available(manifest, eval_pairs_dir)
    reflective_mask = _reflective_mask_available(manifest, eval_pairs_dir)
    source_rows = [row for row in metrics_rows if _metric_id(row) in TARGET_METRICS]
    gate_rows = [
        _classify_metric(row, probe, render_pair, reflective_mask)
        for row in source_rows
    ]
    ready_count = sum(1 for row in gate_rows if row["status"] == "ready_for_bounded_compute")
    blocked_count = len(gate_rows) - ready_count
    if ready_count == len(TARGET_METRICS) and len(gate_rows) == len(TARGET_METRICS):
        gate_status = "ready_for_bounded_compute"
    elif ready_count > 0:
        gate_status = "partially_ready"
    else:
        gate_status = "blocked"
    return gate_rows, {
        "milestone": "M37",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "runtime_launched": False,
        "metrics_computed": False,
        "dependency_gate_status": gate_status,
        "source_unavailable_lpips_count": len(source_rows),
        "ready_metric_count": ready_count,
        "blocked_metric_count": blocked_count,
        "lpips_probe": probe,
        "supported_conclusions": [
            "LPIPS/refl-LPIPS optional dependency readiness can be gated separately from metric computation.",
            "Existing source metrics remain unavailable until a future bounded compute pass writes explicit LPIPS values.",
        ],
        "unsupported_conclusions": [
            "LPIPS or refl-LPIPS values were computed in this milestone.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene claims.",
        ],
        "recommended_next_milestone": (
            "If M37 is ready, run a bounded dry-run-first LPIPS compute plumbing pass that writes separate "
            "augmented metrics without overwriting source M32 metrics. If blocked, fix the reported dependency "
            "or artifact gate first."
        ),
    }


def write_report(path, gate_rows, summary):
    lines = [
        "# Milestone 37 LPIPS dependency gate",
        "",
        "Paper-scale gate: NO-GO",
        "LPIPS values computed: false",
        "SRD-GS superiority: unsupported",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Summary",
        "",
        "- Dependency gate status: {}".format(summary["dependency_gate_status"]),
        "- Source LPIPS unavailable rows: {}".format(summary["source_unavailable_lpips_count"]),
        "- Ready metrics: {}".format(summary["ready_metric_count"]),
        "- Blocked metrics: {}".format(summary["blocked_metric_count"]),
        "",
        "## Gate Rows",
        "",
        "| Metric | Status | Import available | Model init available | Render pairs | Reflective mask |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in gate_rows:
        lines.append(
            "| {}/{} | {} | {} | {} | {} | {} |".format(
                row["category"],
                row["name"],
                row["status"],
                row["dependency_import_available"],
                row["dependency_model_init_available"],
                row["render_pair_available"],
                row["reflective_mask_available"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: dependency/artifact readiness for future bounded LPIPS computation.",
            "- Unsupported: LPIPS values, SRD-GS superiority, rendering recovery, or paper-scale claims.",
            "- Source metrics remain unchanged and unavailable until a future compute pass writes explicit values.",
            "",
            "## Recommended Next Milestone",
            "",
            summary["recommended_next_milestone"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Gate LPIPS/refl-LPIPS dependency readiness without computing metrics.")
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--metrics_json", required=False, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--eval_pairs_dir", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--probe_json", default=None, type=Path)
    parser.add_argument("--lpips_net", default="alex")
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    manifest = _read_json(args.manifest)
    probe = _load_probe(args.probe_json, args.lpips_net)
    gate_rows, summary = build_gate(metrics_rows, manifest, args.eval_pairs_dir, probe)
    summary["metrics_csv"] = str(args.metrics_csv)
    summary["metrics_json"] = str(args.metrics_json) if args.metrics_json else ""
    summary["manifest"] = str(args.manifest)
    summary["eval_pairs_dir"] = str(args.eval_pairs_dir)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "lpips_dependency_gate.csv", gate_rows)
    _write_json(args.output_dir / "lpips_dependency_gate.json", summary)
    write_report(args.output_dir / "lpips_dependency_gate.md", gate_rows, summary)
    print(f"Wrote {args.output_dir / 'lpips_dependency_gate.csv'}")
    print(f"Wrote {args.output_dir / 'lpips_dependency_gate.json'}")
    print(f"Wrote {args.output_dir / 'lpips_dependency_gate.md'}")


if __name__ == "__main__":
    main()
