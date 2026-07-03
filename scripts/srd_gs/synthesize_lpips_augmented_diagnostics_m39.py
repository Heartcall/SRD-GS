import argparse
import csv
import json
from pathlib import Path


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


def _as_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_float(value):
    if value is None:
        return ""
    return "{:.12g}".format(float(value))


def _metric_id(row):
    return "{}/{}".format(row.get("category", ""), row.get("name", ""))


def _find_metric(rows, metric_id):
    for row in rows:
        if _metric_id(row) == metric_id:
            return row
    return {}


def _copy_metric_position_rows(rows):
    fieldnames = [
        "label",
        "psnr",
        "refl_psnr",
        "chamfer_distance",
        "f_score",
        "normal_mae",
        "highlight_leakage_score",
        "m39_role",
    ]
    output = []
    for row in rows:
        item = {field: row.get(field, "") for field in fieldnames}
        item["m39_role"] = "m32_current_position" if row.get("label") == "M32_instrumented_i30" else "prior_short_budget_control"
        output.append(item)
    return output, fieldnames


def _highlight_metric(diagnostic_rows):
    if not diagnostic_rows:
        return None
    row = diagnostic_rows[0]
    return _as_float(row.get("value"))


def build_synthesis(m33_summary, m33_metric_comparison, m36_summary, m36_diagnostic_rows, m37_gate, m38_summary, m38_augmented_rows):
    lpips = _as_float(m38_summary.get("lpips"))
    refl_lpips = _as_float(m38_summary.get("refl_lpips"))
    f_score_row = _find_metric(m38_augmented_rows, "geometry/f_score")
    f_score = _as_float(f_score_row.get("value"))
    f_score_blocker = bool(m33_summary.get("f_score_blocker")) or f_score is None or f_score <= 0.0
    highlight_value = _highlight_metric(m36_diagnostic_rows)
    metrics_integrated = [
        "rendering/lpips",
        "reflective_region/refl_lpips",
    ]
    if highlight_value is not None:
        metrics_integrated.append("texture_material_export_diagnostic/highlight_leakage_score")

    evidence_rows = [
        {
            "source_milestone": "M33",
            "evidence": "m32_short_budget_metric_position",
            "metric": "rank_summary",
            "value": "psnr_rank={};refl_psnr_rank={};chamfer_rank={};normal_mae_rank={}".format(
                m33_summary.get("m32_psnr_rank", ""),
                m33_summary.get("m32_refl_psnr_rank", ""),
                m33_summary.get("m32_chamfer_rank", ""),
                m33_summary.get("m32_normal_mae_rank", ""),
            ),
            "interpretation": "mixed_position",
            "claim_boundary": "diagnostic_only_not_superiority",
        },
        {
            "source_milestone": "M38",
            "evidence": "bounded_lpips_compute",
            "metric": "rendering/lpips",
            "value": _format_float(lpips),
            "interpretation": "high_lpips_does_not_support_rendering_recovery",
            "claim_boundary": "two_frame_ball_artifact_only",
        },
        {
            "source_milestone": "M38",
            "evidence": "bounded_refl_lpips_compute",
            "metric": "reflective_region/refl_lpips",
            "value": _format_float(refl_lpips),
            "interpretation": "high_refl_lpips_does_not_support_reflective_region_recovery",
            "claim_boundary": "two_frame_ball_artifact_only",
        },
        {
            "source_milestone": "M36",
            "evidence": "highlight_leakage_export_diagnostic",
            "metric": "texture_material_export_diagnostic/highlight_leakage_score",
            "value": _format_float(highlight_value),
            "interpretation": "export_diagnostic_not_gt_material_accuracy",
            "claim_boundary": "not_gt_pbr_material_accuracy",
        },
        {
            "source_milestone": "M37",
            "evidence": "lpips_dependency_gate",
            "metric": "rendering/lpips;reflective_region/refl_lpips",
            "value": str(m37_gate.get("dependency_gate_status", "")),
            "interpretation": "dependency_ready_before_m38_compute",
            "claim_boundary": "readiness_not_quality",
        },
        {
            "source_milestone": "M33/M38",
            "evidence": "geometry_blocker",
            "metric": "geometry/f_score",
            "value": _format_float(f_score),
            "interpretation": "F-score remains zero" if f_score_blocker else "f_score_nonzero",
            "claim_boundary": "geometry_superiority_unsupported",
        },
    ]

    summary = {
        "milestone": "M39",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_rendering_recovery": False,
        "supports_srd_gs_superiority": False,
        "supports_geometry_superiority": False,
        "supports_pbr_material_accuracy": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "source_metrics_overwritten": False,
        "quality_interpretation": "mixed_or_unresolved",
        "metrics_integrated": metrics_integrated,
        "lpips": lpips,
        "refl_lpips": refl_lpips,
        "frame_count": m38_summary.get("frame_count"),
        "highlight_leakage_export_diagnostic": highlight_value,
        "f_score": f_score,
        "f_score_blocker": f_score_blocker,
        "m32_psnr_rank": m33_summary.get("m32_psnr_rank"),
        "m32_refl_psnr_rank": m33_summary.get("m32_refl_psnr_rank"),
        "m32_chamfer_rank": m33_summary.get("m32_chamfer_rank"),
        "m32_normal_mae_rank": m33_summary.get("m32_normal_mae_rank"),
        "m33_unavailable_metric_count": m33_summary.get("unavailable_metric_count"),
        "m36_remaining_metric_blocker_count": m36_summary.get("remaining_metric_blocker_count"),
        "m37_dependency_gate_status": m37_gate.get("dependency_gate_status"),
        "m38_metrics_computed": bool(m38_summary.get("metrics_computed")),
        "supported_conclusions": [
            "M38 LPIPS/Refl-LPIPS values can be integrated with prior diagnostic evidence in a separate M39 artifact.",
            "The current evidence remains bounded to existing M32 ball artifacts and preserves source metrics.",
            "M36 highlight leakage remains an export diagnostic, not accepted GT material accuracy.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Stable geometry superiority.",
            "GT PBR material accuracy.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "LPIPS/Refl-LPIPS are available but high for the bounded two-frame artifact set.",
            "F-score remains zero in the M32 diagnostic evidence.",
            "Accepted GT depth/material artifacts are still missing.",
            "Material-view manifest and runtime-cost logs are still missing.",
            "The evidence is single-scene, short-budget, and non-comparative for paper-scale claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 40 should stay bounded and choose one remaining unavailable-metric contract, such as "
            "accepted GT depth/material artifact protocol, material-view manifest definition, or runtime-cost logging."
        ),
    }
    return evidence_rows, summary


def write_report(path, evidence_rows, summary):
    lines = [
        "# Milestone 39 LPIPS augmented diagnostic synthesis",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "Rendering recovery: unsupported",
        "GT PBR material accuracy: unsupported",
        "No train/render/mesh/texture/eval runtime launched.",
        "",
        "## Integrated Evidence",
        "",
        "| Source | Metric | Value | Interpretation | Claim boundary |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in evidence_rows:
        lines.append(
            "| {source_milestone} | {metric} | {value} | {interpretation} | {claim_boundary} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Diagnostic Position",
            "",
            "- LPIPS: {}".format(summary["lpips"]),
            "- Refl-LPIPS: {}".format(summary["refl_lpips"]),
            "- M32 PSNR/Refl-PSNR ranks: {}/{}".format(summary["m32_psnr_rank"], summary["m32_refl_psnr_rank"]),
            "- M32 Chamfer/Normal MAE ranks: {}/{}".format(summary["m32_chamfer_rank"], summary["m32_normal_mae_rank"]),
            "- F-score remains zero: {}".format(str(summary["f_score_blocker"]).lower()),
            "- Highlight leakage export diagnostic: {}".format(summary["highlight_leakage_export_diagnostic"]),
            "",
            "## Claim Boundary",
            "",
            "- Supported: bounded read-only synthesis of M33/M36/M37/M38 evidence.",
            "- Supported: LPIPS metric availability is improved for the existing two-frame M32 artifact set.",
            "- Unsupported: SRD-GS superiority, rendering recovery, geometry superiority, GT material accuracy, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Synthesize M38 LPIPS augmented metrics with prior SRD-GS diagnostics.")
    parser.add_argument("--m33_summary", required=True, type=Path)
    parser.add_argument("--m33_metric_comparison", required=True, type=Path)
    parser.add_argument("--m36_summary", required=True, type=Path)
    parser.add_argument("--m36_diagnostic_csv", required=True, type=Path)
    parser.add_argument("--m37_gate_json", required=True, type=Path)
    parser.add_argument("--m38_summary", required=True, type=Path)
    parser.add_argument("--m38_augmented_metrics", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    m33_summary = _read_json(args.m33_summary)
    m33_metric_comparison = _read_csv(args.m33_metric_comparison)
    m36_summary = _read_json(args.m36_summary)
    m36_diagnostic_rows = _read_csv(args.m36_diagnostic_csv)
    m37_gate = _read_json(args.m37_gate_json)
    m38_summary = _read_json(args.m38_summary)
    m38_augmented_rows = _read_csv(args.m38_augmented_metrics)

    evidence_rows, summary = build_synthesis(
        m33_summary,
        m33_metric_comparison,
        m36_summary,
        m36_diagnostic_rows,
        m37_gate,
        m38_summary,
        m38_augmented_rows,
    )
    metric_position_rows, metric_position_fieldnames = _copy_metric_position_rows(m33_metric_comparison)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "lpips_augmented_diagnostic_summary.csv",
        evidence_rows,
        ["source_milestone", "evidence", "metric", "value", "interpretation", "claim_boundary"],
    )
    _write_json(args.output_dir / "lpips_augmented_diagnostic_summary.json", summary)
    _write_csv(args.output_dir / "m39_metric_position.csv", metric_position_rows, metric_position_fieldnames)
    write_report(args.output_dir / "lpips_augmented_diagnostic_report.md", evidence_rows, summary)

    print("Wrote {}".format(args.output_dir / "lpips_augmented_diagnostic_summary.csv"))
    print("Wrote {}".format(args.output_dir / "lpips_augmented_diagnostic_summary.json"))
    print("Wrote {}".format(args.output_dir / "lpips_augmented_diagnostic_report.md"))
    print("Wrote {}".format(args.output_dir / "m39_metric_position.csv"))


if __name__ == "__main__":
    main()
