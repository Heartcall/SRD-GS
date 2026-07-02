import argparse
import csv
import importlib.util
import json
from pathlib import Path


TRUE = "true"
FALSE = "false"


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json_if_exists(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _as_bool_text(value):
    return TRUE if bool(value) else FALSE


def _path_exists(path):
    return Path(path).exists() if path else False


def _any_existing(root, relative_candidates):
    root = Path(root)
    for candidate in relative_candidates:
        if (root / candidate).exists():
            return True
    return False


def _manifest_field_available(manifest, manifest_dir, field_name):
    field = (manifest.get("fields") or {}).get(field_name) or {}
    if field.get("available") is False:
        return False
    directory = field.get("directory") or field_name
    field_dir = Path(manifest_dir) / directory
    return field_dir.exists() and any(path.is_file() for path in field_dir.iterdir())


def _render_pair_available(manifest, manifest_dir):
    return (
        _manifest_field_available(manifest, manifest_dir, "pred_rgb")
        and _manifest_field_available(manifest, manifest_dir, "gt_rgb")
        and len(manifest.get("frames") or []) > 0
    )


def _texture_artifact_available(result_root):
    texture_root = Path(result_root) / "pbr_textures_specular_free"
    return (
        (texture_root / "baking_report.json").exists()
        and (texture_root / "highlight_leakage_mask.png").exists()
    )


def _lpips_dependency_available():
    return importlib.util.find_spec("lpips") is not None


def _classify_unavailable_metric(row, context):
    category = row.get("category", "")
    name = row.get("name", "")
    reason = row.get("not_available_reason", "")
    metric_id = f"{category}/{name}"
    render_pair = context["render_pair_available"]
    result_artifact = False
    source_artifact = False
    dependency = False
    required_artifacts = []
    next_action = ""
    status = "blocked_unknown_requirement"

    if metric_id in {"rendering/lpips", "reflective_region/refl_lpips"}:
        dependency = context["lpips_available"]
        result_artifact = render_pair
        required_artifacts = ["render_eval_pairs/pred_rgb", "render_eval_pairs/gt_rgb", "python:lpips"]
        if not render_pair:
            status = "blocked_missing_render_pairs"
            next_action = "repair render-eval pair export before LPIPS can be computed"
        elif dependency:
            status = "dependency_available"
            next_action = "wire eval LPIPS computation in a bounded dry-run-first metric pass"
        else:
            status = "blocked_missing_dependency"
            next_action = "install or gate the optional lpips dependency before enabling the metric"
    elif metric_id == "geometry/depth_error":
        result_artifact = _manifest_field_available(context["manifest"], context["manifest_dir"], "surface_depth")
        source_artifact = context["gt_depth_available"]
        required_artifacts = ["render_eval_pairs/surface_depth", "source:gt_depth"]
        if not source_artifact:
            status = "blocked_missing_gt"
            next_action = "add an accepted GT-depth artifact contract before computing depth error"
        elif result_artifact:
            status = "plumbing_candidate"
            next_action = "connect accepted GT depth with exported surface_depth in eval"
        else:
            status = "blocked_missing_prediction_artifact"
            next_action = "export prediction depth before computing depth error"
    elif metric_id == "texture_material/highlight_leakage_score":
        result_artifact = context["texture_highlight_artifact_available"]
        required_artifacts = [
            "pbr_textures_specular_free/baking_report.json",
            "pbr_textures_specular_free/highlight_leakage_mask.png",
        ]
        if result_artifact:
            status = "plumbing_candidate"
            next_action = "bridge texture export highlight-leakage diagnostics into eval summary with explicit export-diagnostic labeling"
        else:
            status = "blocked_missing_result_artifact"
            next_action = "export highlight leakage mask and baking report before surfacing the diagnostic"
    elif metric_id == "texture_material/albedo_error":
        result_artifact = _any_existing(context["result_root"], ["pbr_textures_specular_free/albedo.png"])
        source_artifact = context["gt_albedo_available"]
        required_artifacts = ["pbr_textures_specular_free/albedo.png", "source:gt_albedo"]
        status = "plumbing_candidate" if result_artifact and source_artifact else "blocked_missing_gt"
        next_action = "add accepted GT albedo before computing albedo error"
    elif metric_id == "texture_material/roughness_error":
        result_artifact = _any_existing(context["result_root"], ["pbr_textures_specular_free/roughness.png"])
        source_artifact = context["gt_roughness_available"]
        required_artifacts = ["pbr_textures_specular_free/roughness.png", "source:gt_roughness"]
        status = "plumbing_candidate" if result_artifact and source_artifact else "blocked_missing_gt"
        next_action = "add accepted GT roughness before computing roughness error"
    elif metric_id == "texture_material/material_consistency":
        frame_count = len(context["manifest"].get("frames") or [])
        result_artifact = frame_count >= 2 and _manifest_field_available(context["manifest"], context["manifest_dir"], "roughness_map")
        material_manifest = _any_existing(context["result_root"], ["material_view_manifest.json", "pbr_textures_specular_free/material_view_manifest.json"])
        required_artifacts = ["material_view_manifest.json", "render_eval_pairs/roughness_map"]
        if material_manifest and result_artifact:
            status = "plumbing_candidate"
            next_action = "connect material-view manifest with consistency metric"
        else:
            status = "blocked_missing_material_view_manifest"
            next_action = "define a material-view manifest before treating consistency as a metric"
    elif metric_id == "runtime/training_time":
        result_artifact = context["training_timing_available"]
        required_artifacts = ["train_timing.json", "runtime_summary.json"]
        status = "plumbing_candidate" if result_artifact else "blocked_missing_runtime_log"
        next_action = "write or collect train timing logs in a future bounded runtime"
    elif metric_id == "runtime/peak_memory":
        result_artifact = context["memory_log_available"]
        required_artifacts = ["gpu_memory_trace.csv", "runtime_summary.json"]
        status = "plumbing_candidate" if result_artifact else "blocked_missing_runtime_log"
        next_action = "write or collect peak-memory logs in a future bounded runtime"
    elif metric_id == "runtime/render_fps":
        result_artifact = context["render_timing_available"]
        required_artifacts = ["render_timing.json", "render_eval_pairs/render_timing.json"]
        status = "plumbing_candidate" if result_artifact else "blocked_missing_runtime_log"
        next_action = "write or collect render timing logs in a future bounded render pass"
    else:
        next_action = f"define artifact contract for unavailable reason: {reason or 'unknown'}"

    return {
        "category": category,
        "name": name,
        "not_available_reason": reason,
        "status": status,
        "required_artifacts": ";".join(required_artifacts),
        "render_pair_available": _as_bool_text(render_pair),
        "result_artifact_available": _as_bool_text(result_artifact),
        "source_artifact_available": _as_bool_text(source_artifact),
        "dependency_available": _as_bool_text(dependency),
        "next_action": next_action,
    }


def build_audit(metrics_rows, manifest, manifest_dir, result_root, source_path):
    source_path = Path(source_path)
    result_root = Path(result_root)
    context = {
        "manifest": manifest,
        "manifest_dir": Path(manifest_dir),
        "result_root": result_root,
        "render_pair_available": _render_pair_available(manifest, manifest_dir),
        "texture_highlight_artifact_available": _texture_artifact_available(result_root),
        "lpips_available": _lpips_dependency_available(),
        "gt_depth_available": _any_existing(source_path, ["gt_depth", "depth", "depths", "depth_maps"]),
        "gt_albedo_available": _any_existing(source_path, ["gt_albedo", "albedo", "base_color", "basecolor"]),
        "gt_roughness_available": _any_existing(source_path, ["gt_roughness", "roughness"]),
        "training_timing_available": _any_existing(result_root, ["train_timing.json", "runtime_summary.json"]),
        "memory_log_available": _any_existing(result_root, ["gpu_memory_trace.csv", "peak_memory.json", "runtime_summary.json"]),
        "render_timing_available": _any_existing(result_root, ["render_timing.json", "render_eval_pairs/render_timing.json"]),
    }
    unavailable_rows = [
        row
        for row in metrics_rows
        if (row.get("not_available_reason") or "").strip() or not (row.get("value") or "").strip()
    ]
    audit_rows = [_classify_unavailable_metric(row, context) for row in unavailable_rows]
    return audit_rows


def build_summary(audit_rows):
    status_counts = {}
    for row in audit_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    plumbing_candidates = [
        f"{row['category']}/{row['name']}"
        for row in audit_rows
        if row["status"] == "plumbing_candidate"
    ]
    return {
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "runtime_launched": False,
        "unavailable_metric_count": len(audit_rows),
        "plumbing_candidate_count": len(plumbing_candidates),
        "plumbing_candidates": plumbing_candidates,
        "status_counts": status_counts,
        "supported_conclusions": [
            "M35 maps existing unavailable metrics to artifact requirements and blocker classes.",
            "Existing texture export highlight-leakage artifacts can be bridged into eval reporting only as an export diagnostic.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Geometry superiority.",
            "PBR material accuracy.",
            "Paper-scale or multi-scene claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 36 should implement a read-only/dry-run-first highlight-leakage export diagnostic bridge "
            "from texture baking artifacts into eval/material summaries, keeping it separate from GT material accuracy."
        ),
    }


def write_report(path, audit_rows, summary):
    lines = [
        "# Milestone 35 eval/material artifact plumbing audit",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "No train/render/eval runtime launched.",
        "",
        "## Summary",
        "",
        f"- Unavailable metrics audited: {summary['unavailable_metric_count']}",
        f"- Plumbing candidates: {summary['plumbing_candidate_count']}",
        f"- Runtime launched: {summary['runtime_launched']}",
        "",
        "## Artifact Requirement Matrix",
        "",
        "| Metric | Status | Required artifacts | Next action |",
        "| --- | --- | --- | --- |",
    ]
    for row in audit_rows:
        metric = f"{row['category']}/{row['name']}"
        lines.append(
            f"| {metric} | {row['status']} | {row['required_artifacts']} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: artifact requirement and blocker classification for existing unavailable metrics.",
            "- Supported: highlight-leakage export artifacts are available as an eval-summary plumbing candidate.",
            "- Unsupported: GT PBR material accuracy, SRD-GS superiority, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Audit SRD-GS unavailable eval/material metric artifacts.")
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--failure_summary", required=False, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--source_path", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    manifest = _read_json_if_exists(args.manifest)
    audit_rows = build_audit(metrics_rows, manifest, args.manifest.parent, args.result_root, args.source_path)
    summary = build_summary(audit_rows)
    if args.failure_summary and args.failure_summary.exists():
        summary["failure_summary_path"] = str(args.failure_summary)
    summary["metrics_csv"] = str(args.metrics_csv)
    summary["manifest"] = str(args.manifest)
    summary["result_root"] = str(args.result_root)
    summary["source_path"] = str(args.source_path)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "eval_material_artifact_requirements.csv", audit_rows)
    _write_json(args.output_dir / "eval_material_artifact_plan.json", summary)
    write_report(args.output_dir / "eval_material_artifact_plan.md", audit_rows, summary)
    print(f"Wrote {args.output_dir / 'eval_material_artifact_requirements.csv'}")
    print(f"Wrote {args.output_dir / 'eval_material_artifact_plan.json'}")
    print(f"Wrote {args.output_dir / 'eval_material_artifact_plan.md'}")


if __name__ == "__main__":
    main()
