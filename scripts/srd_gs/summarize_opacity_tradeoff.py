import argparse
import csv
import json
from pathlib import Path


METRIC_COLUMNS = [
    "psnr",
    "refl_psnr",
    "chamfer_distance",
    "f_score",
    "normal_mae",
    "highlight_leakage_score",
]

PARAMETER_DELTA_COLUMNS = [
    "opacity_activated_mean_delta_vs_baseline",
    "reflection_feature_abs_mean_delta_vs_baseline",
    "specular_weight_activated_mean_delta_vs_baseline",
]


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _as_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _milestone_number(label):
    if not label.startswith("M"):
        return None
    digits = []
    for char in label[1:]:
        if not char.isdigit():
            break
        digits.append(char)
    if not digits:
        return None
    return int("".join(digits))


def _merge_rows(case_rows, parameter_delta_rows):
    deltas_by_label = {row.get("comparison_label"): row for row in parameter_delta_rows}
    merged = []
    for row in case_rows:
        label = row.get("label", "")
        item = {
            "label": label,
            "milestone": _milestone_number(label),
        }
        for column in METRIC_COLUMNS:
            item[column] = _as_float(row.get(column))
        deltas = deltas_by_label.get(label, {})
        for column in PARAMETER_DELTA_COLUMNS:
            item[column] = _as_float(deltas.get(column))
        merged.append(item)
    return merged


def _best_label(rows, column, *, higher_is_better):
    candidates = [row for row in rows if row.get(column) is not None]
    if not candidates:
        return None
    key = lambda row: row[column]
    return (max if higher_is_better else min)(candidates, key=key)["label"]


def _closest_abs_label(rows, column):
    candidates = [row for row in rows if row.get(column) is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda row: abs(row[column]))["label"]


def _format_float(value):
    if value is None:
        return ""
    return f"{value:.6g}"


def _bool_text(value):
    return "true" if value else "false"


def build_summary(case_rows, parameter_delta_rows):
    rows = _merge_rows(case_rows, parameter_delta_rows)
    if not rows:
        raise ValueError("case_summary is empty")

    baseline_label = rows[0]["label"]
    control_rows = [row for row in rows if row["label"] != baseline_label]
    recent_control_rows = [row for row in control_rows if (row.get("milestone") or 0) >= 24]

    best_rendering_label = _best_label(control_rows, "psnr", higher_is_better=True)
    best_refl_rendering_label = _best_label(control_rows, "refl_psnr", higher_is_better=True)
    best_geometry_chamfer_label = _best_label(control_rows, "chamfer_distance", higher_is_better=False)
    best_normal_mae_label = _best_label(control_rows, "normal_mae", higher_is_better=False)
    best_leakage_label = _best_label(control_rows, "highlight_leakage_score", higher_is_better=False)
    closest_opacity_label = _closest_abs_label(control_rows, "opacity_activated_mean_delta_vs_baseline")

    f_score_candidates = recent_control_rows or control_rows
    f_score_values = [row["f_score"] for row in f_score_candidates if row.get("f_score") is not None]
    f_score_blocker = not f_score_values or max(f_score_values) <= 0.0

    baseline = rows[0]
    table_rows = []
    for row in rows:
        psnr = row.get("psnr")
        refl_psnr = row.get("refl_psnr")
        chamfer = row.get("chamfer_distance")
        f_score = row.get("f_score")
        normal_mae = row.get("normal_mae")
        leakage = row.get("highlight_leakage_score")
        opacity_delta = row.get("opacity_activated_mean_delta_vs_baseline")
        table_rows.append(
            {
                "label": row["label"],
                "psnr": _format_float(psnr),
                "refl_psnr": _format_float(refl_psnr),
                "chamfer_distance": _format_float(chamfer),
                "f_score": _format_float(f_score),
                "normal_mae": _format_float(normal_mae),
                "highlight_leakage_score": _format_float(leakage),
                "opacity_activated_mean_delta_vs_baseline": _format_float(opacity_delta),
                "reflection_feature_abs_mean_delta_vs_baseline": _format_float(
                    row.get("reflection_feature_abs_mean_delta_vs_baseline")
                ),
                "specular_weight_activated_mean_delta_vs_baseline": _format_float(
                    row.get("specular_weight_activated_mean_delta_vs_baseline")
                ),
                "psnr_delta_vs_baseline": _format_float(None if psnr is None else psnr - baseline.get("psnr")),
                "refl_psnr_delta_vs_baseline": _format_float(
                    None if refl_psnr is None else refl_psnr - baseline.get("refl_psnr")
                ),
                "chamfer_delta_vs_baseline": _format_float(
                    None if chamfer is None else chamfer - baseline.get("chamfer_distance")
                ),
                "is_best_rendering": _bool_text(row["label"] == best_rendering_label),
                "is_best_refl_rendering": _bool_text(row["label"] == best_refl_rendering_label),
                "is_best_chamfer": _bool_text(row["label"] == best_geometry_chamfer_label),
                "is_best_normal_mae": _bool_text(row["label"] == best_normal_mae_label),
                "is_best_leakage": _bool_text(row["label"] == best_leakage_label),
                "is_closest_opacity_to_baseline": _bool_text(row["label"] == closest_opacity_label),
            }
        )

    summary = {
        "baseline_label": baseline_label,
        "best_rendering_label": best_rendering_label,
        "best_reflective_rendering_label": best_refl_rendering_label,
        "best_geometry_chamfer_label": best_geometry_chamfer_label,
        "best_normal_mae_label": best_normal_mae_label,
        "best_leakage_label": best_leakage_label,
        "closest_opacity_label": closest_opacity_label,
        "f_score_blocker": f_score_blocker,
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supported_conclusions": [
            "The existing ball artifacts support a bounded opacity-control tradeoff summary.",
            "M25 is the strongest rendering-recovery point among the compared controls.",
            "M24 is the strongest Chamfer point among the compared controls.",
            "M26 is the strongest Normal-MAE and closest-opacity point among the compared controls.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Full rendering recovery.",
            "Stable geometry improvement across metrics.",
            "PBR material accuracy.",
            "Multi-scene paper-scale claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 28 should remain bounded: either one dry-run-first opacity-scale "
            "control such as 0.125 on ball, or a read-only failure-panel/loss-log "
            "synthesis if no additional runtime is approved."
        ),
    }
    return table_rows, summary


def write_report(path, rows, summary):
    lines = [
        "# Milestone 27 opacity-control tradeoff summary",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Tradeoff Winners",
        "",
        f"- Best PSNR control: {summary['best_rendering_label']}",
        f"- Best Refl-PSNR control: {summary['best_reflective_rendering_label']}",
        f"- Best Chamfer control: {summary['best_geometry_chamfer_label']}",
        f"- Best Normal-MAE control: {summary['best_normal_mae_label']}",
        f"- Closest opacity delta to baseline: {summary['closest_opacity_label']}",
        f"- F-score blocker: {summary['f_score_blocker']}",
        "",
        "## Metrics",
        "",
        "| Label | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage | Opacity delta | Flags |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        flags = []
        if row["is_best_rendering"] == "true":
            flags.append("best_psnr")
        if row["is_best_refl_rendering"] == "true":
            flags.append("best_refl_psnr")
        if row["is_best_chamfer"] == "true":
            flags.append("best_chamfer")
        if row["is_best_normal_mae"] == "true":
            flags.append("best_normal_mae")
        if row["is_closest_opacity_to_baseline"] == "true":
            flags.append("closest_opacity")
        lines.append(
            "| {label} | {psnr} | {refl_psnr} | {chamfer_distance} | {f_score} | "
            "{normal_mae} | {highlight_leakage_score} | "
            "{opacity_activated_mean_delta_vs_baseline} | {flags} |".format(
                flags=", ".join(flags),
                **row,
            )
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: bounded single-scene opacity-control tradeoff over completed artifacts.",
            "- Unsupported: full rendering recovery, stable geometry superiority, PBR material accuracy, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Summarize bounded SRD-GS opacity-control tradeoffs.")
    parser.add_argument("--case_summary", required=True, type=Path)
    parser.add_argument("--parameter_deltas", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    case_rows = _read_csv(args.case_summary)
    parameter_delta_rows = _read_csv(args.parameter_deltas)
    table_rows, summary = build_summary(case_rows, parameter_delta_rows)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "opacity_tradeoff_summary.csv"
    summary_path = output_dir / "opacity_tradeoff_summary.json"
    report_path = output_dir / "opacity_tradeoff_summary.md"

    _write_csv(table_path, table_rows, list(table_rows[0].keys()))
    _write_json(summary_path, summary)
    write_report(report_path, table_rows, summary)

    print(f"Wrote {table_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
