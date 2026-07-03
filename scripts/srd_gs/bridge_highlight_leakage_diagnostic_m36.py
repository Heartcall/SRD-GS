import argparse
import csv
import json
import math
from pathlib import Path


DIAGNOSTIC_CATEGORY = "texture_material_export_diagnostic"
DIAGNOSTIC_NAME = "highlight_leakage_score"


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _as_float(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _metric_key(row):
    return "{}/{}".format(row.get("category", ""), row.get("name", ""))


def _unavailable_count(rows):
    count = 0
    for row in rows:
        value = row.get("value")
        reason = row.get("not_available_reason")
        if reason or value in (None, ""):
            count += 1
    return count


def _load_highlight_diagnostic(texture_dir):
    texture_dir = Path(texture_dir)
    report_path = texture_dir / "baking_report.json"
    mask_path = texture_dir / "highlight_leakage_mask.png"
    report = _read_json(report_path)
    value = _as_float(report.get("highlight_leakage_score"))
    if value is None or not mask_path.exists():
        return None
    return {
        "category": DIAGNOSTIC_CATEGORY,
        "name": DIAGNOSTIC_NAME,
        "value": "{:.12g}".format(value),
        "supports_hypothesis": "export_artifact_plumbing",
        "higher_is_better": "False",
        "not_available_reason": "",
        "diagnostic_scope": "export_diagnostic",
        "source_artifact": "{};{}".format(report_path, mask_path),
        "claim_boundary": "not_gt_pbr_material_accuracy",
    }


def _augment_metric_rows(metric_rows, diagnostic_row):
    fieldnames = [
        "category",
        "name",
        "value",
        "supports_hypothesis",
        "higher_is_better",
        "not_available_reason",
        "diagnostic_scope",
        "source_artifact",
        "claim_boundary",
    ]
    augmented = []
    for row in metric_rows:
        augmented.append({field: row.get(field, "") for field in fieldnames})
    if diagnostic_row is not None:
        augmented.append({field: diagnostic_row.get(field, "") for field in fieldnames})
    return augmented, fieldnames


def _augment_metrics_json(metrics_json, diagnostic_row):
    payload = _read_json(metrics_json)
    metrics = list(payload.get("metrics") or [])
    if diagnostic_row is not None:
        metrics.append(
            {
                "category": diagnostic_row["category"],
                "name": diagnostic_row["name"],
                "value": float(diagnostic_row["value"]),
                "supports_hypothesis": diagnostic_row["supports_hypothesis"],
                "higher_is_better": False,
                "not_available_reason": None,
                "diagnostic_scope": diagnostic_row["diagnostic_scope"],
                "source_artifact": diagnostic_row["source_artifact"],
                "claim_boundary": diagnostic_row["claim_boundary"],
            }
        )
    payload["metrics"] = metrics
    payload["m36_diagnostic_bridge"] = {
        "paper_scale_gate": "NO-GO",
        "diagnostic_scope": "export_diagnostic",
        "supports_pbr_material_accuracy": False,
        "runtime_launched": False,
    }
    return payload


def build_bridge(metrics_rows, metrics_json, failure_summary, m35_plan, texture_dir):
    plan = _read_json(m35_plan)
    diagnostic_row = _load_highlight_diagnostic(texture_dir)
    source_unavailable = _unavailable_count(metrics_rows)
    candidate_id = "texture_material/highlight_leakage_score"
    m35_candidates = set(plan.get("plumbing_candidates") or [])
    candidate_from_m35 = candidate_id in m35_candidates
    bridged_count = 1 if diagnostic_row is not None and candidate_from_m35 else 0
    if bridged_count == 0:
        diagnostic_row = None

    summary = {
        "milestone": "M36",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_pbr_material_accuracy": False,
        "runtime_launched": False,
        "diagnostic_scope": "export_diagnostic",
        "source_unavailable_metric_count": source_unavailable,
        "bridged_diagnostic_count": bridged_count,
        "remaining_metric_blocker_count": max(source_unavailable - bridged_count, 0),
        "source_metrics_csv": str(metrics_json).replace("metrics.json", "metrics.csv"),
        "source_metrics_json": str(metrics_json),
        "failure_summary": str(failure_summary),
        "m35_plan": str(m35_plan),
        "texture_dir": str(texture_dir),
        "supported_conclusions": [
            "Existing texture-export highlight-leakage artifacts are surfaced as a separate export diagnostic.",
            "The original eval/material unavailable metric remains visible and is not overwritten.",
        ],
        "unsupported_conclusions": [
            "GT PBR material accuracy.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Geometry superiority.",
            "Paper-scale or multi-scene claims.",
        ],
        "recommended_next_milestone": (
            "Use M36 outputs to decide whether the next bounded step should target another unavailable metric "
            "contract, such as LPIPS dependency gating or accepted GT material/depth artifacts."
        ),
    }
    diagnostic_rows = []
    if diagnostic_row is not None:
        diagnostic_rows.append(
            {
                "category": diagnostic_row["category"],
                "name": diagnostic_row["name"],
                "value": diagnostic_row["value"],
                "diagnostic_scope": diagnostic_row["diagnostic_scope"],
                "source_artifact": diagnostic_row["source_artifact"],
                "claim_boundary": diagnostic_row["claim_boundary"],
            }
        )
    return diagnostic_row, diagnostic_rows, summary, _augment_metrics_json(metrics_json, diagnostic_row)


def write_report(path, diagnostic_rows, summary):
    lines = [
        "# Milestone 36 highlight-leakage export diagnostic bridge",
        "",
        "Paper-scale gate: NO-GO",
        "GT PBR material accuracy: unsupported",
        "SRD-GS superiority: unsupported",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Summary",
        "",
        "- Source unavailable metrics: {}".format(summary["source_unavailable_metric_count"]),
        "- Bridged export diagnostics: {}".format(summary["bridged_diagnostic_count"]),
        "- Remaining metric blockers: {}".format(summary["remaining_metric_blocker_count"]),
        "",
        "## Diagnostic Rows",
        "",
        "| Metric | Value | Scope | Claim boundary |",
        "| --- | ---: | --- | --- |",
    ]
    if diagnostic_rows:
        for row in diagnostic_rows:
            lines.append(
                "| {}/{} | {} | {} | {} |".format(
                    row["category"],
                    row["name"],
                    row["value"],
                    row["diagnostic_scope"],
                    row["claim_boundary"],
                )
            )
    else:
        lines.append("| none |  |  |  |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: highlight leakage from texture export is visible in an eval/material summary artifact.",
            "- Supported: the original unavailable eval metric is preserved and not treated as solved GT material accuracy.",
            "- Unsupported: SRD-GS superiority, rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Bridge texture highlight leakage into eval/material summaries as an export diagnostic.")
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--metrics_json", required=True, type=Path)
    parser.add_argument("--failure_summary", required=True, type=Path)
    parser.add_argument("--m35_plan", required=True, type=Path)
    parser.add_argument("--texture_dir", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    diagnostic_row, diagnostic_rows, summary, augmented_json = build_bridge(
        metrics_rows,
        args.metrics_json,
        args.failure_summary,
        args.m35_plan,
        args.texture_dir,
    )
    augmented_rows, augmented_fieldnames = _augment_metric_rows(metrics_rows, diagnostic_row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "highlight_leakage_diagnostic_summary.csv",
        diagnostic_rows,
        ["category", "name", "value", "diagnostic_scope", "source_artifact", "claim_boundary"],
    )
    _write_json(args.output_dir / "highlight_leakage_diagnostic_summary.json", summary)
    write_report(args.output_dir / "highlight_leakage_diagnostic_summary.md", diagnostic_rows, summary)
    _write_csv(args.output_dir / "eval_material_augmented_metrics.csv", augmented_rows, augmented_fieldnames)
    _write_json(args.output_dir / "eval_material_augmented_metrics.json", augmented_json)

    print(f"Wrote {args.output_dir / 'highlight_leakage_diagnostic_summary.csv'}")
    print(f"Wrote {args.output_dir / 'highlight_leakage_diagnostic_summary.json'}")
    print(f"Wrote {args.output_dir / 'highlight_leakage_diagnostic_summary.md'}")
    print(f"Wrote {args.output_dir / 'eval_material_augmented_metrics.csv'}")
    print(f"Wrote {args.output_dir / 'eval_material_augmented_metrics.json'}")


if __name__ == "__main__":
    main()
