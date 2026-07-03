import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image


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


def _format_float(value):
    return "{:.12g}".format(float(value))


def _load_image(path):
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def _mae(path_a, path_b):
    image_a = _load_image(path_a)
    image_b = _load_image(path_b)
    if image_a.shape != image_b.shape:
        raise ValueError(f"Image shape mismatch for material consistency: {path_a} {image_a.shape} vs {path_b} {image_b.shape}")
    return float(np.mean(np.abs(image_a - image_b)))


def _complete_views(manifest):
    return [
        view
        for view in manifest.get("material_views", [])
        if view.get("complete_required_material_fields") == "true"
    ]


def compute_pairwise_rows(manifest):
    required_fields = manifest.get("required_fields") or ["diffuse_rgb", "roughness_map"]
    complete_views = _complete_views(manifest)
    rows = []
    for view_a, view_b in itertools.combinations(complete_views, 2):
        field_values = {}
        for field in required_fields:
            path_a = view_a.get(f"{field}_path", "")
            path_b = view_b.get(f"{field}_path", "")
            if not path_a or not path_b:
                raise ValueError(f"Missing material-view artifact path for required field {field}")
            field_values[f"{field}_mae"] = _mae(path_a, path_b)
        material_mae = float(np.mean(list(field_values.values()))) if field_values else None
        row = {
            "view_a": view_a.get("view_index", ""),
            "view_b": view_b.get("view_index", ""),
            "image_a": view_a.get("image_name", ""),
            "image_b": view_b.get("image_name", ""),
            "material_consistency_mae": _format_float(material_mae),
        }
        for field in required_fields:
            row[f"{field}_mae"] = _format_float(field_values[f"{field}_mae"])
        rows.append(row)
    return rows, required_fields


def _mean_from_rows(rows, field):
    values = [float(row[field]) for row in rows if row.get(field) not in ("", None)]
    return float(np.mean(values)) if values else None


def build_outputs(manifest, metrics_rows):
    pairwise_rows, required_fields = compute_pairwise_rows(manifest)
    pair_count = len(pairwise_rows)
    material_consistency_mae = _mean_from_rows(pairwise_rows, "material_consistency_mae")
    field_means = {
        f"{field}_mae": _mean_from_rows(pairwise_rows, f"{field}_mae")
        for field in required_fields
    }
    diagnostic_rows = [
        {
            "category": "texture_material_diagnostic",
            "name": "material_consistency_mae",
            "value": _format_float(material_consistency_mae) if material_consistency_mae is not None else "",
            "supports_hypothesis": "material_view_consistency",
            "higher_is_better": "False",
            "not_available_reason": "",
            "metric_scope": "bounded_material_view_diagnostic",
            "claim_boundary": "not_gt_pbr_material_accuracy",
        }
    ]
    for field_name, value in field_means.items():
        diagnostic_rows.append(
            {
                "category": "texture_material_diagnostic",
                "name": field_name,
                "value": _format_float(value) if value is not None else "",
                "supports_hypothesis": "material_view_consistency",
                "higher_is_better": "False",
                "not_available_reason": "",
                "metric_scope": "bounded_material_view_diagnostic",
                "claim_boundary": "not_gt_pbr_material_accuracy",
            }
        )
    augmented_rows = []
    for row in metrics_rows:
        copied = dict(row)
        copied.setdefault("metric_scope", "source_metric")
        copied.setdefault("claim_boundary", "source_eval_metric")
        augmented_rows.append(copied)
    augmented_rows.extend(diagnostic_rows)
    source_material_row = next(
        (row for row in metrics_rows if _metric_id(row) == "texture_material/material_consistency"),
        {},
    )
    summary = {
        "milestone": "M41",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_pbr_material_accuracy": False,
        "supports_rendering_recovery": False,
        "material_consistency_diagnostic_computed": material_consistency_mae is not None,
        "material_consistency_mae": material_consistency_mae,
        "field_mae": field_means,
        "pair_count": pair_count,
        "material_view_count": len(_complete_views(manifest)),
        "source_metrics_overwritten": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "diagnostic_scope": "bounded_material_view_diagnostic",
        "source_material_consistency_reason": source_material_row.get("not_available_reason", ""),
        "supported_conclusions": [
            "A bounded material-consistency diagnostic can be computed from the existing M40 material-view manifest.",
            "The diagnostic is written separately and source M32 metrics remain unchanged.",
        ],
        "unsupported_conclusions": [
            "GT PBR material accuracy.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Stable geometry superiority.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "The material-consistency value is a bounded image-space diagnostic, not GT material accuracy.",
            "Accepted GT depth/material artifacts remain missing.",
            "Runtime-cost logs remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 42 should stay bounded and choose the next remaining contract: accepted GT depth/material "
            "artifact protocol or runtime-cost logging."
        ),
    }
    return pairwise_rows, diagnostic_rows, augmented_rows, summary


def write_report(path, summary, pairwise_rows):
    lines = [
        "# Milestone 41 material-consistency diagnostic",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "GT PBR material accuracy: unsupported",
        "Rendering recovery: unsupported",
        "Source metrics overwritten: false",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Diagnostic Summary",
        "",
        "- Material views: {}".format(summary["material_view_count"]),
        "- Pair count: {}".format(summary["pair_count"]),
        "- Material consistency MAE: {}".format(summary["material_consistency_mae"]),
        "- Diagnostic scope: {}".format(summary["diagnostic_scope"]),
        "",
        "## Pairwise Rows",
        "",
        "| View A | View B | Material MAE |",
        "| --- | --- | ---: |",
    ]
    for row in pairwise_rows:
        lines.append("| {view_a} | {view_b} | {material_consistency_mae} |".format(**row))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: bounded image-space material-consistency diagnostic for existing M40 material views.",
            "- Unsupported: GT material accuracy, SRD-GS superiority, rendering recovery, geometry superiority, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Compute a bounded SRD-GS material-consistency diagnostic.")
    parser.add_argument("--material_view_manifest", required=True, type=Path)
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = _read_json(args.material_view_manifest)
    metrics_rows = _read_csv(args.metrics_csv)
    pairwise_rows, diagnostic_rows, augmented_rows, summary = build_outputs(manifest, metrics_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "material_consistency_pairwise.csv", pairwise_rows)
    _write_csv(args.output_dir / "material_consistency_diagnostic.csv", diagnostic_rows)
    _write_json(args.output_dir / "material_consistency_summary.json", summary)
    _write_csv(args.output_dir / "eval_material_augmented_metrics.csv", augmented_rows)
    write_report(args.output_dir / "material_consistency_report.md", summary, pairwise_rows)
    print(f"Wrote {args.output_dir / 'material_consistency_pairwise.csv'}")
    print(f"Wrote {args.output_dir / 'material_consistency_diagnostic.csv'}")
    print(f"Wrote {args.output_dir / 'material_consistency_summary.json'}")
    print(f"Wrote {args.output_dir / 'eval_material_augmented_metrics.csv'}")
    print(f"Wrote {args.output_dir / 'material_consistency_report.md'}")


if __name__ == "__main__":
    main()
