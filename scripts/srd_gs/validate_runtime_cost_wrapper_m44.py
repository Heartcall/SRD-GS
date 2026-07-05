import argparse
import csv
import json
from pathlib import Path


PLAN_FIELDS = [
    "metric_id",
    "wrapper_status",
    "source_command_file",
    "source_command_available",
    "required_log",
    "required_log_available",
    "runtime_launch_required_for_m44",
    "planned_wrapper_mode",
    "collection_method",
    "failure_condition",
    "next_action",
]


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _file_available(path):
    candidate = Path(path)
    return candidate.exists() and candidate.is_file() and candidate.read_text(encoding="utf-8").strip() != ""


def _artifact_available(path):
    candidate = Path(path)
    return candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0


def build_wrapper_plan(manifest):
    rows = []
    for entry in manifest.get("entries", []):
        command_file = entry.get("command_file", "")
        required_log = entry.get("required_log", "")
        command_available = _file_available(command_file)
        log_available = _artifact_available(required_log)
        if not command_available:
            status = "blocked_missing_source_command"
            failure_condition = "source command is missing or empty"
            next_action = "recover the command artifact before any bounded runtime-cost collection"
        elif log_available:
            status = "wrapper_plan_ready_existing_log"
            failure_condition = "none"
            next_action = "parse existing runtime-cost log in a future bounded parser milestone"
        else:
            status = "wrapper_plan_ready"
            failure_condition = "future runtime collection must write the required log path"
            next_action = "use this dry-run plan for a future preflight-gated bounded collection"
        rows.append(
            {
                "metric_id": entry.get("metric_id", ""),
                "wrapper_status": status,
                "source_command_file": command_file,
                "source_command_available": "true" if command_available else "false",
                "required_log": required_log,
                "required_log_available": "true" if log_available else "false",
                "runtime_launch_required_for_m44": "false",
                "planned_wrapper_mode": "dry_run_validation_only",
                "collection_method": entry.get("collection_method", ""),
                "failure_condition": failure_condition,
                "next_action": next_action,
            }
        )
    return rows


def build_summary(contract, manifest, rows):
    ready_statuses = {"wrapper_plan_ready", "wrapper_plan_ready_existing_log"}
    ready_count = sum(1 for row in rows if row["wrapper_status"] in ready_statuses)
    log_count = sum(1 for row in rows if row["required_log_available"] == "true")
    blocked_count = len(rows) - ready_count
    return {
        "milestone": "M44",
        "source_milestone": manifest.get("milestone", "M43"),
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_runtime_cost_claim": False,
        "supports_rendering_recovery": False,
        "metrics_computed": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "contract_paper_scale_gate": contract.get("paper_scale_gate", "NO-GO"),
        "manifest_entry_count": len(rows),
        "wrapper_plan_ready_count": ready_count,
        "logged_metric_count": log_count,
        "blocked_wrapper_count": blocked_count,
        "supported_conclusions": [
            "Runtime-cost wrapper readiness can be validated from the M43 manifest without launching runtime commands.",
            "Existing command artifacts can be classified as ready or blocked for a future bounded collection pass.",
        ],
        "unsupported_conclusions": [
            "Runtime-cost metric values.",
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Runtime-cost logs have not been collected in this milestone.",
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 45 should remain bounded: either add a runtime-cost parser for existing logs if logs appear, "
            "or run exactly one short preflight-gated runtime-cost collection before parsing values."
        ),
    }


def write_report(path, rows, summary):
    lines = [
        "# Milestone 44 runtime-cost wrapper validation",
        "",
        "Paper-scale gate: NO-GO",
        "Runtime-cost metric values: unavailable",
        "Metrics computed: false",
        "No train/render/eval runtime launched.",
        "",
        "## Wrapper Plan",
        "",
        "| Metric | Status | Command available | Required log available | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {metric_id} | {wrapper_status} | {source_command_available} | {required_log_available} | {next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Manifest entries: {summary['manifest_entry_count']}",
            f"- Wrapper plans ready: {summary['wrapper_plan_ready_count']}",
            f"- Blocked wrappers: {summary['blocked_wrapper_count']}",
            f"- Logs currently available: {summary['logged_metric_count']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: dry-run wrapper validation for future bounded runtime-cost collection.",
            "- Unsupported: runtime-cost values, runtime efficiency claims, SRD-GS superiority, or paper-scale claims.",
            "",
            "## Failure Conditions",
            "",
            "- If this milestone launches training, rendering, evaluation, mesh extraction, texture export, or multi-scene experiments, it fails.",
            "- If wrapper readiness is treated as runtime-cost measurement, it fails.",
            "- If runtime efficiency, SRD-GS superiority, rendering recovery, GT material accuracy, or paper-scale claims are upgraded, it fails.",
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
    parser = argparse.ArgumentParser(description="Validate dry-run SRD-GS runtime-cost wrapper readiness.")
    parser.add_argument("--contract_json", required=True, type=Path)
    parser.add_argument("--manifest_template", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    contract = _read_json(args.contract_json)
    manifest = _read_json(args.manifest_template)
    rows = build_wrapper_plan(manifest)
    summary = build_summary(contract, manifest, rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "runtime_cost_wrapper_plan.csv", rows)
    _write_json(args.output_dir / "runtime_cost_wrapper_plan.json", summary)
    write_report(args.output_dir / "runtime_cost_wrapper_plan.md", rows, summary)
    print(f"Wrote {args.output_dir / 'runtime_cost_wrapper_plan.csv'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_wrapper_plan.json'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_wrapper_plan.md'}")


if __name__ == "__main__":
    main()
