import argparse
import csv
import json
from pathlib import Path


RENDER_FIELDS = [
    "pred_rgb",
    "gt_rgb",
    "diffuse_rgb",
    "specular_rgb",
    "branch_gate_map",
    "roughness_map",
    "surface_depth",
    "surface_normal",
    "reflective_mask",
]

CORE_ARTIFACTS = {
    "train_command": "train_command.txt",
    "mesh_surface": "mesh_surface.ply",
    "baking_report": "pbr_textures_specular_free/baking_report.json",
    "render_eval_manifest": "render_eval_pairs/render_eval_manifest.json",
    "metrics_json": "eval_with_gt_mesh/metrics.json",
}

LOSS_LOG_PATTERNS = [
    "loss*.csv",
    "*loss*.json",
    "*loss*.txt",
    "events.out.tfevents*",
]

FAILURE_PANEL_PATTERNS = [
    "failure_cases/*",
    "failure_panels/*",
    "qualitative_panels/*failure*",
]


def parse_case(case_arg):
    if "=" not in case_arg:
        raise ValueError(f"Case must use LABEL=RESULT_ROOT format: {case_arg}")
    label, root = case_arg.split("=", 1)
    if not label:
        raise ValueError("Case label cannot be empty")
    return label, Path(root)


def _read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _exists_nonempty(path):
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _glob_any(root, patterns):
    matches = []
    for pattern in patterns:
        matches.extend(path for path in root.glob(pattern) if path.is_file() and path.stat().st_size > 0)
    return sorted(set(matches))


def _manifest_frame_status(root):
    manifest_path = root / CORE_ARTIFACTS["render_eval_manifest"]
    if not manifest_path.exists():
        return 0, 0, [f"missing:{manifest_path}"]

    missing = []
    try:
        manifest = _read_json(manifest_path)
    except json.JSONDecodeError as exc:
        return 0, 0, [f"invalid_json:{manifest_path}:{exc}"]

    frames = manifest.get("frames", [])
    expected = len(frames) * len(RENDER_FIELDS)
    present = 0
    pair_root = root / "render_eval_pairs"
    for frame_index, frame in enumerate(frames):
        for field in RENDER_FIELDS:
            rel_path = frame.get(field)
            if not rel_path:
                missing.append(f"missing_manifest_field:frame{frame_index}:{field}")
                continue
            path = pair_root / rel_path
            if _exists_nonempty(path):
                present += 1
            else:
                missing.append(f"missing_render_field:{path}")
    return expected, present, missing


def build_matrix(cases):
    rows = []
    for label, root in cases:
        root = Path(root)
        missing = []
        artifact_flags = {}
        for key, rel_path in CORE_ARTIFACTS.items():
            path = root / rel_path
            exists = _exists_nonempty(path)
            artifact_flags[f"{key}_available"] = exists
            if not exists:
                missing.append(f"missing:{path}")

        expected_render_refs, present_render_refs, manifest_missing = _manifest_frame_status(root)
        missing.extend(manifest_missing)
        render_fields_complete = expected_render_refs > 0 and present_render_refs == expected_render_refs

        loss_logs = _glob_any(root, LOSS_LOG_PATTERNS)
        failure_panels = _glob_any(root, FAILURE_PANEL_PATTERNS)
        core_artifact_chain_complete = all(artifact_flags.values()) and render_fields_complete

        row = {
            "label": label,
            "result_root": str(root),
            "core_artifact_chain_complete": core_artifact_chain_complete,
            "render_fields_complete": render_fields_complete,
            "expected_render_field_refs": expected_render_refs,
            "present_render_field_refs": present_render_refs,
            "loss_log_available": bool(loss_logs),
            "loss_log_count": len(loss_logs),
            "failure_panel_available": bool(failure_panels),
            "failure_panel_count": len(failure_panels),
            "missing_artifacts": ";".join(missing),
        }
        row.update(artifact_flags)
        rows.append(row)
    return rows


def _bool_text(value):
    return "true" if value else "false"


def _csv_rows(rows):
    serialized = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, bool):
                item[key] = _bool_text(value)
            else:
                item[key] = value
        serialized.append(item)
    return serialized


def build_summary(rows):
    complete_core_cases = [row["label"] for row in rows if row["core_artifact_chain_complete"]]
    loss_cases = [row["label"] for row in rows if row["loss_log_available"]]
    failure_panel_cases = [row["label"] for row in rows if row["failure_panel_available"]]
    incomplete_cases = [row["label"] for row in rows if not row["core_artifact_chain_complete"]]
    return {
        "case_count": len(rows),
        "complete_core_artifact_cases": complete_core_cases,
        "incomplete_core_artifact_cases": incomplete_cases,
        "loss_log_cases": loss_cases,
        "failure_panel_cases": failure_panel_cases,
        "needs_loss_log_instrumentation": len(loss_cases) == 0,
        "needs_failure_panel_generation": len(failure_panel_cases) == 0,
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supported_conclusions": [
            "The existing cases can be audited for artifact-chain completeness.",
            "Loss-log and failure-panel availability can be treated as explicit blockers when absent.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Root-cause proof for the opacity/rendering tradeoff.",
            "Paper-scale rendering, geometry, or material claims.",
        ],
        "recommended_next_milestone": (
            "Milestone 29 should remain bounded: either add loss/failure-panel "
            "instrumentation in dry-run-first form or run one explicitly approved "
            "single-scene opacity-scale control."
        ),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_rows = _csv_rows(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_report(path, rows, summary):
    lines = [
        "# Milestone 28 failure/loss artifact synthesis",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Artifact Matrix",
        "",
        "| Label | Core chain | Render fields | Loss logs | Failure panels | Missing artifacts |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {label} | {core} | {render} | {loss} | {failure} | {missing} |".format(
                label=row["label"],
                core=_bool_text(row["core_artifact_chain_complete"]),
                render=f"{row['present_render_field_refs']}/{row['expected_render_field_refs']}",
                loss=row["loss_log_count"],
                failure=row["failure_panel_count"],
                missing=row["missing_artifacts"] or "",
            )
        )

    lines.extend(
        [
            "",
            "## Synthesis",
            "",
            f"- Complete core artifact cases: {', '.join(summary['complete_core_artifact_cases']) or 'none'}",
            f"- Incomplete core artifact cases: {', '.join(summary['incomplete_core_artifact_cases']) or 'none'}",
            f"- Loss-log cases: {', '.join(summary['loss_log_cases']) or 'none'}",
            f"- Failure-panel cases: {', '.join(summary['failure_panel_cases']) or 'none'}",
            f"- Needs loss-log instrumentation: {summary['needs_loss_log_instrumentation']}",
            f"- Needs failure-panel generation: {summary['needs_failure_panel_generation']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: read-only artifact availability audit for completed bounded cases.",
            "- Unsupported: root-cause proof, rendering recovery, geometry superiority, PBR material accuracy, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Summarize SRD-GS failure-panel and loss-log artifact availability.")
    parser.add_argument("--case", action="append", required=True, help="LABEL=RESULT_ROOT")
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    cases = [parse_case(case_arg) for case_arg in args.case]
    rows = build_matrix(cases)
    summary = build_summary(rows)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = output_dir / "failure_loss_artifact_matrix.csv"
    summary_path = output_dir / "failure_loss_synthesis.json"
    report_path = output_dir / "failure_loss_synthesis.md"
    write_csv(matrix_path, rows)
    write_json(summary_path, summary)
    write_report(report_path, rows, summary)

    print(f"Wrote {matrix_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
