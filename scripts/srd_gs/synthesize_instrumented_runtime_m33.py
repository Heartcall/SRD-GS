import argparse
import csv
import json
from pathlib import Path


COMPARISON_METRICS = [
    ("psnr", True),
    ("refl_psnr", True),
    ("chamfer_distance", False),
    ("f_score", True),
    ("normal_mae", False),
    ("highlight_leakage_score", False),
]


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or list(rows[0].keys())
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


def _format_float(value):
    if value is None:
        return ""
    return f"{value:.6g}"


def _metrics_from_eval_csv(rows):
    values = {}
    unavailable = []
    for row in rows:
        name = row.get("name")
        if not name:
            continue
        value = _as_float(row.get("value"))
        reason = row.get("not_available_reason") or ""
        if value is None and reason:
            unavailable.append(
                {
                    "category": row.get("category", ""),
                    "name": name,
                    "not_available_reason": reason,
                    "source": "metrics_csv",
                }
            )
        values[name] = value
    return values, unavailable


def _parse_failure_summary(path):
    rows = []
    if not path.exists():
        return rows
    in_unavailable = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_unavailable = stripped == "## Unavailable Metrics"
            continue
        if not in_unavailable or not stripped.startswith("- "):
            continue
        body = stripped[2:]
        if ":" not in body or "/" not in body:
            continue
        metric, reason = body.split(":", 1)
        category, name = metric.split("/", 1)
        rows.append(
            {
                "category": category.strip(),
                "name": name.strip(),
                "not_available_reason": reason.strip(),
                "source": "failure_summary",
            }
        )
    return rows


def _unique_unavailable(metrics_rows, failure_rows):
    by_key = {}
    for row in metrics_rows + failure_rows:
        key = (row["category"], row["name"])
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = row
        elif existing["source"] != "failure_summary" and row["source"] == "failure_summary":
            by_key[key] = row
    return list(by_key.values())


def _metric_comparison_rows(prior_rows, m32_values):
    rows = []
    for row in prior_rows:
        item = {"label": row.get("label", "")}
        for name, _higher in COMPARISON_METRICS:
            item[name] = _format_float(_as_float(row.get(name)))
        rows.append(item)

    m32_row = {"label": "M32_instrumented_i30"}
    for name, _higher in COMPARISON_METRICS:
        m32_row[name] = _format_float(m32_values.get(name))
    rows.append(m32_row)
    return rows


def _rank(rows, label, metric_name, higher_is_better):
    candidates = []
    for row in rows:
        value = _as_float(row.get(metric_name))
        if value is not None:
            candidates.append((row["label"], value))
    candidates.sort(key=lambda item: item[1], reverse=higher_is_better)
    for index, (candidate_label, _value) in enumerate(candidates, start=1):
        if candidate_label == label:
            return index
    return None


def _loss_summary_rows(loss_rows):
    if not loss_rows:
        return [], {}
    numeric_rows = []
    for row in loss_rows:
        numeric_rows.append(
            {
                "iteration": int(float(row.get("iteration", 0))),
                "stage": row.get("stage", ""),
                "total_loss": _as_float(row.get("total_loss")),
                "loss_photo": _as_float(row.get("loss_photo")),
                "loss_geo": _as_float(row.get("loss_geo")),
                "surface_alpha_mean": _as_float(row.get("surface_alpha_mean")),
                "gaussian_count": _as_float(row.get("gaussian_count")),
            }
        )
    numeric_rows.sort(key=lambda row: row["iteration"])
    total_values = [row["total_loss"] for row in numeric_rows if row["total_loss"] is not None]
    monotonic = all(a >= b for a, b in zip(total_values, total_values[1:])) if len(total_values) > 1 else True
    first = numeric_rows[0]
    final = numeric_rows[-1]
    summary = {
        "loss_rows": len(numeric_rows),
        "first_iteration": first["iteration"],
        "final_iteration": final["iteration"],
        "final_stage": final["stage"],
        "first_total_loss": first["total_loss"],
        "final_total_loss": final["total_loss"],
        "final_minus_first_total_loss": (
            None
            if first["total_loss"] is None or final["total_loss"] is None
            else final["total_loss"] - first["total_loss"]
        ),
        "total_loss_monotonic_nonincreasing": monotonic,
        "final_surface_alpha_mean": final["surface_alpha_mean"],
        "final_gaussian_count": final["gaussian_count"],
    }
    rows = [
        {
            "name": key,
            "value": _format_float(value) if isinstance(value, float) else value,
        }
        for key, value in summary.items()
    ]
    return rows, summary


def _manifest_summary(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy = payload.get("branch_map_policy", {})
    fields = payload.get("fields", {})
    available_fields = [name for name, item in fields.items() if item.get("available")]
    summary = {
        "render_eval_iteration": payload.get("iteration"),
        "render_eval_frames": len(payload.get("frames", [])),
        "branch_map_policy": policy.get("policy"),
        "branch_gate_weight": policy.get("branch_gate_weight"),
        "render_gate_weight": policy.get("render_gate_weight"),
        "gate_applied": policy.get("gate_applied"),
        "available_field_count": len(available_fields),
        "available_fields": ",".join(sorted(available_fields)),
    }
    rows = [{"name": key, "value": value} for key, value in summary.items()]
    return rows, summary


def build_synthesis(prior_case_summary, m32_metrics, m32_loss_log, m32_manifest, m32_failure_summary):
    prior_rows = _read_csv(prior_case_summary)
    metric_rows = _read_csv(m32_metrics)
    m32_values, unavailable_from_metrics = _metrics_from_eval_csv(metric_rows)
    unavailable_rows = _unique_unavailable(unavailable_from_metrics, _parse_failure_summary(m32_failure_summary))

    comparison_rows = _metric_comparison_rows(prior_rows, m32_values)
    loss_rows, loss_summary = _loss_summary_rows(_read_csv(m32_loss_log))
    manifest_rows, manifest_summary = _manifest_summary(m32_manifest)

    summary = {
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "m32_psnr_rank": _rank(comparison_rows, "M32_instrumented_i30", "psnr", True),
        "m32_refl_psnr_rank": _rank(comparison_rows, "M32_instrumented_i30", "refl_psnr", True),
        "m32_chamfer_rank": _rank(comparison_rows, "M32_instrumented_i30", "chamfer_distance", False),
        "m32_normal_mae_rank": _rank(comparison_rows, "M32_instrumented_i30", "normal_mae", False),
        "f_score_blocker": (m32_values.get("f_score") is None or m32_values.get("f_score") <= 0.0),
        "unavailable_metric_count": len(unavailable_rows),
        "supported_conclusions": [
            "M32 loss, failure-summary, manifest, and metric artifacts can be read and summarized.",
            "M32 can be positioned against prior short-budget controls for diagnostics only.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Full rendering recovery.",
            "Stable geometry superiority.",
            "PBR material accuracy.",
            "Multi-scene paper-scale claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 34 should remain bounded and choose one diagnostic direction: "
            "Stage B/C activation, opacity schedule, or eval/material artifact plumbing."
        ),
    }
    summary.update(loss_summary)
    summary.update(manifest_summary)
    return comparison_rows, loss_rows, unavailable_rows, manifest_rows, summary


def write_report(path, comparison_rows, loss_rows, unavailable_rows, manifest_rows, summary):
    lines = [
        "# Milestone 33 instrumented runtime diagnostic synthesis",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Metric Position",
        "",
        "| Label | PSNR | Refl-PSNR | Chamfer | F-score | Normal MAE | Leakage |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in comparison_rows:
        lines.append(
            "| {label} | {psnr} | {refl_psnr} | {chamfer_distance} | {f_score} | {normal_mae} | {highlight_leakage_score} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Loss Progression",
            "",
        ]
    )
    for row in loss_rows:
        lines.append(f"- {row['name']}: {row['value']}")
    lines.extend(
        [
            "",
            "## Render Manifest",
            "",
        ]
    )
    for row in manifest_rows:
        lines.append(f"- {row['name']}: {row['value']}")
    lines.extend(
        [
            "",
            "## Unavailable Metrics",
            "",
        ]
    )
    for row in unavailable_rows:
        lines.append(f"- {row['category']}/{row['name']}: {row['not_available_reason']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: read-only M32 diagnostic synthesis against prior short-budget controls.",
            "- Unsupported: rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Synthesize M32 instrumented runtime diagnostics.")
    parser.add_argument("--prior_case_summary", required=True, type=Path)
    parser.add_argument("--m32_metrics", required=True, type=Path)
    parser.add_argument("--m32_loss_log", required=True, type=Path)
    parser.add_argument("--m32_manifest", required=True, type=Path)
    parser.add_argument("--m32_failure_summary", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    comparison_rows, loss_rows, unavailable_rows, manifest_rows, summary = build_synthesis(
        args.prior_case_summary,
        args.m32_metrics,
        args.m32_loss_log,
        args.m32_manifest,
        args.m32_failure_summary,
    )
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(output_dir / "m32_metric_comparison.csv", comparison_rows)
    _write_csv(output_dir / "m32_loss_progression_summary.csv", loss_rows, ["name", "value"])
    _write_csv(
        output_dir / "m32_unavailable_metrics.csv",
        unavailable_rows,
        ["category", "name", "not_available_reason", "source"],
    )
    _write_csv(output_dir / "m32_manifest_summary.csv", manifest_rows, ["name", "value"])
    _write_json(output_dir / "m33_synthesis_summary.json", summary)
    write_report(
        output_dir / "m33_synthesis_report.md",
        comparison_rows,
        loss_rows,
        unavailable_rows,
        manifest_rows,
        summary,
    )

    print(f"Wrote {output_dir / 'm32_metric_comparison.csv'}")
    print(f"Wrote {output_dir / 'm33_synthesis_summary.json'}")
    print(f"Wrote {output_dir / 'm33_synthesis_report.md'}")


if __name__ == "__main__":
    main()
