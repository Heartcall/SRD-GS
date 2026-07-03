import argparse
import csv
import json
from pathlib import Path


TARGETS = [
    {
        "metric_id": "geometry/depth_error",
        "gt_kind": "depth",
        "source_reason": "gt_depth_not_available",
        "prediction_candidates": [
            "render_eval_pairs/surface_depth",
        ],
        "gt_patterns": [
            "**/*_depth.png",
            "**/*_depth.tiff",
            "**/*_depth.exr",
            "**/*_depth.npy",
            "**/depth/*.png",
            "**/depth/*.tiff",
            "**/depth/*.exr",
            "**/depths/*.png",
            "**/depth_maps/*.png",
        ],
    },
    {
        "metric_id": "texture_material/albedo_error",
        "gt_kind": "albedo",
        "source_reason": "gt_albedo_not_available",
        "prediction_candidates": [
            "pbr_textures_specular_free/albedo.png",
        ],
        "gt_patterns": [
            "**/*_albedo.png",
            "**/*_basecolor.png",
            "**/*_base_color.png",
            "**/albedo/*.png",
            "**/base_color/*.png",
            "**/basecolor/*.png",
        ],
    },
    {
        "metric_id": "texture_material/roughness_error",
        "gt_kind": "roughness",
        "source_reason": "gt_roughness_not_available",
        "prediction_candidates": [
            "pbr_textures_specular_free/roughness.png",
        ],
        "gt_patterns": [
            "**/*_roughness.png",
            "**/*_rough.png",
            "**/roughness/*.png",
            "**/roughness_maps/*.png",
        ],
    },
]


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


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _metric_id(row):
    return "{}/{}".format(row.get("category", ""), row.get("name", ""))


def _find_metric(rows, metric_id):
    for row in rows:
        if _metric_id(row) == metric_id:
            return row
    return {}


def _candidate_files(source_path, patterns, limit=50):
    source_path = Path(source_path)
    candidates = []
    if not source_path.exists():
        return candidates
    for pattern in patterns:
        for path in source_path.glob(pattern):
            if path.is_file():
                candidates.append(str(path))
            if len(candidates) >= limit:
                return sorted(set(candidates))
    return sorted(set(candidates))


def _prediction_available(result_root, candidates):
    root = Path(result_root)
    for relative in candidates:
        path = root / relative
        if path.is_dir() and any(item.is_file() for item in path.iterdir()):
            return True, str(path)
        if path.is_file():
            return True, str(path)
    return False, ""


def build_protocol(source_path, result_root, metrics_rows):
    protocol_rows = []
    candidate_rows = []
    for target in TARGETS:
        metric = _find_metric(metrics_rows, target["metric_id"])
        gt_candidates = _candidate_files(source_path, target["gt_patterns"])
        prediction_available, prediction_path = _prediction_available(result_root, target["prediction_candidates"])
        gt_available = len(gt_candidates) > 0
        if gt_available and prediction_available:
            status = "ready_for_future_metric_compute"
            next_action = "compute metric in a future bounded pass after confirming GT semantic alignment"
        elif gt_available:
            status = "blocked_missing_prediction_artifact"
            next_action = "export prediction artifact before metric computation"
        else:
            status = "blocked_missing_accepted_gt"
            next_action = "add or approve accepted GT artifact contract before metric computation"
        protocol_rows.append(
            {
                "metric_id": target["metric_id"],
                "gt_kind": target["gt_kind"],
                "source_metric_reason": metric.get("not_available_reason", target["source_reason"]),
                "status": status,
                "accepted_gt_candidate_available": "true" if gt_available else "false",
                "accepted_gt_candidate_count": str(len(gt_candidates)),
                "prediction_artifact_available": "true" if prediction_available else "false",
                "prediction_artifact_path": prediction_path,
                "metrics_computed": "false",
                "next_action": next_action,
            }
        )
        for candidate in gt_candidates:
            candidate_rows.append(
                {
                    "metric_id": target["metric_id"],
                    "gt_kind": target["gt_kind"],
                    "candidate_path": candidate,
                    "candidate_status": "candidate_not_validated_as_accepted_gt",
                }
            )
    return protocol_rows, candidate_rows


def build_summary(protocol_rows, candidate_rows, source_path, result_root):
    ready_count = sum(1 for row in protocol_rows if row["status"] == "ready_for_future_metric_compute")
    blocked_count = len(protocol_rows) - ready_count
    return {
        "milestone": "M42",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_pbr_material_accuracy": False,
        "supports_rendering_recovery": False,
        "metrics_computed": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "source_path": str(source_path),
        "result_root": str(result_root),
        "ready_contract_count": ready_count,
        "blocked_contract_count": blocked_count,
        "gt_candidate_count": len(candidate_rows),
        "supported_conclusions": [
            "Accepted-GT depth/material artifact candidates can be inventoried without computing metrics.",
            "Future metric computation readiness can be classified per target metric.",
        ],
        "unsupported_conclusions": [
            "Accepted GT semantic correctness.",
            "Depth/albedo/roughness metric values.",
            "GT PBR material accuracy.",
            "SRD-GS superiority over Ref-GS.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Accepted GT depth/material artifacts are absent or still need semantic acceptance before claim-bearing metrics.",
            "Runtime-cost logs remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 43 should remain bounded: either validate one accepted-GT artifact contract for depth/material "
            "or implement runtime-cost logging as the next remaining contract."
        ),
    }


def write_report(path, protocol_rows, summary):
    lines = [
        "# Milestone 42 accepted-GT depth/material protocol audit",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "GT PBR material accuracy: unsupported",
        "Metrics computed: false",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Protocol Matrix",
        "",
        "| Metric | Status | GT candidates | Prediction artifact | Next action |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in protocol_rows:
        lines.append(
            "| {metric_id} | {status} | {accepted_gt_candidate_count} | {prediction_artifact_available} | {next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Ready contracts: {summary['ready_contract_count']}",
            f"- Blocked contracts: {summary['blocked_contract_count']}",
            f"- GT candidates inventoried: {summary['gt_candidate_count']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: accepted-GT candidate inventory and per-metric readiness classification.",
            "- Unsupported: accepted GT semantic correctness, metric values, GT PBR material accuracy, SRD-GS superiority, or paper-scale claims.",
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    for blocker in summary["remaining_blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Recommended Next Milestone", "", summary["recommended_next_milestone"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Audit accepted-GT depth/material artifact protocol readiness.")
    parser.add_argument("--source_path", required=True, type=Path)
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    protocol_rows, candidate_rows = build_protocol(args.source_path, args.result_root, metrics_rows)
    summary = build_summary(protocol_rows, candidate_rows, args.source_path, args.result_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "gt_depth_material_protocol.csv", protocol_rows)
    _write_csv(
        args.output_dir / "gt_depth_material_candidates.csv",
        candidate_rows,
        fieldnames=["metric_id", "gt_kind", "candidate_path", "candidate_status"],
    )
    _write_json(args.output_dir / "gt_depth_material_protocol.json", summary)
    write_report(args.output_dir / "gt_depth_material_protocol.md", protocol_rows, summary)
    print(f"Wrote {args.output_dir / 'gt_depth_material_protocol.csv'}")
    print(f"Wrote {args.output_dir / 'gt_depth_material_candidates.csv'}")
    print(f"Wrote {args.output_dir / 'gt_depth_material_protocol.json'}")
    print(f"Wrote {args.output_dir / 'gt_depth_material_protocol.md'}")


if __name__ == "__main__":
    main()
