import argparse
import csv
import json
from pathlib import Path


REQUIRED_VIEW_FIELDS = ["diffuse_rgb", "roughness_map"]
OPTIONAL_VIEW_FIELDS = ["surface_normal", "pred_rgb", "gt_rgb", "specular_rgb", "branch_gate_map"]


def _read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _metric_id(row):
    return "{}/{}".format(row.get("category", ""), row.get("name", ""))


def _find_metric(rows, metric_id):
    for row in rows:
        if _metric_id(row) == metric_id:
            return row
    return {}


def _resolve_artifact(eval_pairs_dir, relative_path):
    if not relative_path:
        return ""
    return str(Path(eval_pairs_dir) / relative_path)


def _artifact_exists(eval_pairs_dir, relative_path):
    return bool(relative_path) and (Path(eval_pairs_dir) / relative_path).exists()


def _frame_to_material_view(frame, eval_pairs_dir):
    row = {
        "view_index": str(frame.get("index", "")),
        "image_name": frame.get("image_name", ""),
        "complete_required_material_fields": "true",
    }
    missing = []
    for field in REQUIRED_VIEW_FIELDS + OPTIONAL_VIEW_FIELDS:
        relative = frame.get(field, "")
        exists = _artifact_exists(eval_pairs_dir, relative)
        row[field] = relative
        row[f"{field}_exists"] = "true" if exists else "false"
        row[f"{field}_path"] = _resolve_artifact(eval_pairs_dir, relative) if relative else ""
        if field in REQUIRED_VIEW_FIELDS and not exists:
            missing.append(field)
    if missing:
        row["complete_required_material_fields"] = "false"
    row["missing_required_fields"] = ";".join(missing)
    return row


def build_manifest(render_manifest, eval_pairs_dir, metrics_rows):
    material_views = [_frame_to_material_view(frame, eval_pairs_dir) for frame in render_manifest.get("frames", [])]
    complete_views = [
        view
        for view in material_views
        if view.get("complete_required_material_fields") == "true"
    ]
    material_metric = _find_metric(metrics_rows, "texture_material/material_consistency")
    source_metric_reason = material_metric.get("not_available_reason", "")
    contract_ready = len(complete_views) >= 2
    contract_status = (
        "ready_for_future_material_consistency_compute"
        if contract_ready
        else "blocked_missing_material_views"
    )
    payload = {
        "schema_version": 1,
        "metric_scope": "material_view_manifest_only",
        "source_manifest_split": render_manifest.get("split", ""),
        "source_path": render_manifest.get("source_path", ""),
        "required_fields": REQUIRED_VIEW_FIELDS,
        "optional_fields": OPTIONAL_VIEW_FIELDS,
        "material_views": material_views,
        "complete_material_view_count": len(complete_views),
        "contract_status": contract_status,
        "source_material_consistency_reason": source_metric_reason,
        "material_consistency_computed": False,
        "source_metrics_overwritten": False,
        "paper_scale_gate": "NO-GO",
    }
    summary = {
        "milestone": "M40",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_pbr_material_accuracy": False,
        "supports_rendering_recovery": False,
        "material_consistency_computed": False,
        "source_metrics_overwritten": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "material_view_count": len(complete_views),
        "total_manifest_frame_count": len(material_views),
        "contract_status": contract_status,
        "source_material_consistency_reason": source_metric_reason,
        "supported_conclusions": [
            "Existing render-eval artifacts can define a material-view manifest for future bounded material-consistency computation.",
            "M40 removes the missing material-view-manifest contract for the existing M32 artifact set only.",
        ],
        "unsupported_conclusions": [
            "Material consistency metric values.",
            "GT PBR material accuracy.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Material consistency is not computed in M40.",
            "Accepted GT depth/material artifacts remain missing.",
            "Runtime-cost logs remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 41 can stay bounded and compute a material-consistency diagnostic from the M40 manifest, "
            "or choose accepted GT depth/material protocol or runtime-cost logging instead."
        ),
    }
    return payload, summary


def write_report(path, manifest_payload, summary):
    lines = [
        "# Milestone 40 material-view manifest contract",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "GT PBR material accuracy: unsupported",
        "Material consistency computed: false",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Contract Summary",
        "",
        "- Contract status: {}".format(summary["contract_status"]),
        "- Complete material views: {}".format(summary["material_view_count"]),
        "- Total manifest frames: {}".format(summary["total_manifest_frame_count"]),
        "- Source material-consistency reason: {}".format(summary["source_material_consistency_reason"] or "none"),
        "",
        "## Material Views",
        "",
        "| View | Image | Diffuse | Roughness | Normal | Complete required fields |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for view in manifest_payload["material_views"]:
        lines.append(
            "| {view_index} | {image_name} | {diffuse_rgb_exists} | {roughness_map_exists} | {surface_normal_exists} | {complete_required_material_fields} |".format(
                **view
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: material-view manifest definition for existing M32 render-eval artifacts.",
            "- Unsupported: material consistency value, GT material accuracy, SRD-GS superiority, or paper-scale claims.",
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    for blocker in summary["remaining_blockers"]:
        lines.append("- {}".format(blocker))
    lines.extend(
        [
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
    parser = argparse.ArgumentParser(description="Build a bounded SRD-GS material-view manifest contract.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--eval_pairs_dir", required=True, type=Path)
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    render_manifest = _read_json(args.manifest)
    metrics_rows = _read_csv(args.metrics_csv)
    manifest_payload, summary = build_manifest(render_manifest, args.eval_pairs_dir, metrics_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "material_view_manifest.json", manifest_payload)
    _write_csv(args.output_dir / "material_view_manifest.csv", manifest_payload["material_views"])
    _write_json(args.output_dir / "material_view_contract_summary.json", summary)
    write_report(args.output_dir / "material_view_contract_report.md", manifest_payload, summary)
    print(f"Wrote {args.output_dir / 'material_view_manifest.json'}")
    print(f"Wrote {args.output_dir / 'material_view_manifest.csv'}")
    print(f"Wrote {args.output_dir / 'material_view_contract_summary.json'}")
    print(f"Wrote {args.output_dir / 'material_view_contract_report.md'}")


if __name__ == "__main__":
    main()
