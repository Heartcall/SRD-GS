import argparse
import csv
import json
from pathlib import Path


DIRECTIONS = [
    {
        "direction": "stage_bc_activation",
        "scope": "single_scene_runtime_or_dry_run",
        "targets": "probe whether Stage B/C loss activation changes the rendering/geometry tradeoff",
    },
    {
        "direction": "opacity_schedule",
        "scope": "single_scene_runtime_or_dry_run",
        "targets": "probe whether opacity schedule changes the M25/M26 rendering/geometry tradeoff",
    },
    {
        "direction": "eval_material_artifact_plumbing",
        "scope": "read_only_or_dry_run_first",
        "targets": "reduce unavailable metric blockers before another runtime claim",
    },
]


def _read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
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


def _score_directions(summary):
    unavailable_count = int(summary.get("unavailable_metric_count") or 0)
    f_score_blocker = bool(summary.get("f_score_blocker"))
    geometry_worst = (summary.get("m32_chamfer_rank") or 0) >= 7 or (summary.get("m32_normal_mae_rank") or 0) >= 7
    rendering_rank_good = (summary.get("m32_psnr_rank") == 1 and summary.get("m32_refl_psnr_rank") == 1)
    loss_rows = int(summary.get("loss_rows") or 0)
    loss_short_or_unstable = loss_rows <= 3 or not bool(summary.get("total_loss_monotonic_nonincreasing"))

    rows = []
    for item in DIRECTIONS:
        direction = item["direction"]
        score = 0
        reasons = []
        blockers = []
        if direction == "eval_material_artifact_plumbing":
            if unavailable_count:
                score += 4
                reasons.append(f"{unavailable_count}_unavailable_metrics")
            if rendering_rank_good and geometry_worst:
                score += 1
                reasons.append("quality_tradeoff_needs_metric_plumbing")
            if f_score_blocker:
                score += 1
                reasons.append("f_score_blocker_requires_eval_context")
            blockers.append("does_not_test_training_dynamics")
        elif direction == "stage_bc_activation":
            if geometry_worst or f_score_blocker:
                score += 2
                reasons.append("geometry_blocker_present")
            if loss_short_or_unstable:
                score += 1
                reasons.append("loss_signal_short_or_unstable")
            blockers.extend(["requires_runtime", "does_not_reduce_unavailable_metrics_first"])
        elif direction == "opacity_schedule":
            if rendering_rank_good and geometry_worst:
                score += 2
                reasons.append("render_geometry_tradeoff_present")
            if f_score_blocker:
                score += 1
                reasons.append("f_score_blocker_present")
            blockers.extend(["requires_runtime", "may_repeat_known_m25_m26_tradeoff"])

        rows.append(
            {
                "direction": direction,
                "scope": item["scope"],
                "score": score,
                "reasons": ";".join(reasons),
                "blockers": ";".join(blockers),
                "targets": item["targets"],
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["direction"]))
    return rows


def build_decision(summary):
    rows = _score_directions(summary)
    recommended = rows[0]["direction"]
    deferred = [row["direction"] for row in rows[1:]]
    decision = {
        "recommended_direction": recommended,
        "deferred_directions": deferred,
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "decision_basis": {
            "m32_psnr_rank": summary.get("m32_psnr_rank"),
            "m32_refl_psnr_rank": summary.get("m32_refl_psnr_rank"),
            "m32_chamfer_rank": summary.get("m32_chamfer_rank"),
            "m32_normal_mae_rank": summary.get("m32_normal_mae_rank"),
            "f_score_blocker": summary.get("f_score_blocker"),
            "loss_rows": summary.get("loss_rows"),
            "total_loss_monotonic_nonincreasing": summary.get("total_loss_monotonic_nonincreasing"),
            "unavailable_metric_count": summary.get("unavailable_metric_count"),
        },
        "supported_conclusions": [
            "A bounded next diagnostic direction can be selected from existing M33 evidence.",
            "Eval/material artifact plumbing is the least runtime-expanding next step when unavailable metrics dominate the blocker list.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Stable geometry superiority.",
            "PBR material accuracy.",
            "Multi-scene paper-scale claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 35 should implement the selected eval/material artifact plumbing "
            "as a read-only or dry-run-first bounded milestone."
        ),
    }
    return rows, decision


def write_report(path, matrix_rows, decision):
    lines = [
        "# Milestone 34 diagnostic direction decision",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Recommended Direction",
        "",
        f"`{decision['recommended_direction']}`",
        "",
        "## Decision Matrix",
        "",
        "| Direction | Score | Scope | Reasons | Blockers |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in matrix_rows:
        lines.append(
            "| {direction} | {score} | {scope} | {reasons} | {blockers} |".format(**row)
        )
    basis = decision["decision_basis"]
    lines.extend(
        [
            "",
            "## Evidence Basis",
            "",
            f"- M32 PSNR/Refl-PSNR ranks: {basis.get('m32_psnr_rank')} / {basis.get('m32_refl_psnr_rank')}",
            f"- M32 Chamfer/Normal-MAE ranks: {basis.get('m32_chamfer_rank')} / {basis.get('m32_normal_mae_rank')}",
            f"- F-score blocker: {basis.get('f_score_blocker')}",
            f"- Loss rows: {basis.get('loss_rows')}",
            f"- Total loss monotonic non-increasing: {basis.get('total_loss_monotonic_nonincreasing')}",
            f"- Unavailable metric count: {basis.get('unavailable_metric_count')}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: bounded diagnostic-direction selection from existing M33 evidence.",
            "- Unsupported: runtime quality improvement, geometry superiority, material accuracy, or paper-scale claims.",
            "",
            "## Recommended Next Milestone",
            "",
            decision["recommended_next_milestone"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Choose the next bounded SRD-GS diagnostic direction.")
    parser.add_argument("--m33_summary", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    summary = _read_json(args.m33_summary)
    matrix_rows, decision = build_decision(summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "diagnostic_direction_matrix.csv", matrix_rows)
    _write_json(args.output_dir / "diagnostic_direction_decision.json", decision)
    write_report(args.output_dir / "diagnostic_direction_decision.md", matrix_rows, decision)
    print(f"Wrote {args.output_dir / 'diagnostic_direction_matrix.csv'}")
    print(f"Wrote {args.output_dir / 'diagnostic_direction_decision.json'}")
    print(f"Wrote {args.output_dir / 'diagnostic_direction_decision.md'}")


if __name__ == "__main__":
    main()
