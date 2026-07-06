import argparse
import csv
import json
import shlex
from pathlib import Path


FIELDS = [
    "metric_id",
    "collection_status",
    "source_command_file",
    "source_command_available",
    "required_log",
    "required_log_available",
    "immutable_root",
    "command_references_immutable_root",
    "log_references_immutable_root",
    "collection_safe_to_launch",
    "runtime_launched",
    "failure_condition",
    "next_action",
]


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_command(path):
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8").strip()


def _is_nonempty_file(path):
    candidate = Path(path)
    return candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0


def _path_contains_root(path, root):
    if not path or not root:
        return False
    path_text = str(path)
    root_text = str(root)
    try:
        resolved_path = Path(path_text).resolve()
        resolved_root = Path(root_text).resolve()
        return resolved_path == resolved_root or resolved_root in resolved_path.parents
    except OSError:
        return path_text == root_text or path_text.startswith(root_text.rstrip("/") + "/")


def _command_references_root(command_text, root):
    if not command_text or not root:
        return False
    root_text = str(root)
    if root_text in command_text:
        return True
    try:
        tokens = shlex.split(command_text)
    except ValueError:
        tokens = command_text.split()
    return any(_path_contains_root(token, root_text) for token in tokens)


def build_preflight_rows(wrapper_rows, immutable_root):
    rows = []
    for source in wrapper_rows:
        command_file = source.get("source_command_file", "")
        required_log = source.get("required_log", "")
        command_text = _read_command(command_file)
        command_available = bool(command_text)
        log_available = _is_nonempty_file(required_log)
        command_references_immutable = _command_references_root(command_text, immutable_root) or _path_contains_root(
            command_file, immutable_root
        )
        log_references_immutable = _path_contains_root(required_log, immutable_root)

        if not command_available:
            status = "blocked_missing_source_command"
            failure_condition = "source command is missing or empty"
            next_action = "recover source command before collection"
        elif command_references_immutable or log_references_immutable:
            status = "blocked_existing_output_target"
            failure_condition = "planned command or required log targets an existing immutable output root"
            next_action = "clone the bounded command into a fresh M46 output root before launching collection"
        elif log_available:
            status = "ready_existing_log_for_parser"
            failure_condition = "none"
            next_action = "parse existing runtime-cost log in a future bounded parser milestone"
        else:
            status = "ready_for_bounded_collection"
            failure_condition = "none"
            next_action = "run exactly one short preflight-gated collection in the prepared fresh output root"

        collection_safe = status in {"ready_existing_log_for_parser", "ready_for_bounded_collection"}
        rows.append(
            {
                "metric_id": source.get("metric_id", ""),
                "collection_status": status,
                "source_command_file": command_file,
                "source_command_available": "true" if command_available else "false",
                "required_log": required_log,
                "required_log_available": "true" if log_available else "false",
                "immutable_root": str(immutable_root),
                "command_references_immutable_root": "true" if command_references_immutable else "false",
                "log_references_immutable_root": "true" if log_references_immutable else "false",
                "collection_safe_to_launch": "true" if collection_safe else "false",
                "runtime_launched": "false",
                "failure_condition": failure_condition,
                "next_action": next_action,
            }
        )
    return rows


def build_summary(rows):
    safe_count = sum(1 for row in rows if row["collection_safe_to_launch"] == "true")
    overwrite_count = sum(1 for row in rows if row["collection_status"] == "blocked_existing_output_target")
    missing_command_count = sum(1 for row in rows if row["collection_status"] == "blocked_missing_source_command")
    existing_log_count = sum(1 for row in rows if row["required_log_available"] == "true")
    return {
        "milestone": "M45",
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_runtime_cost_claim": False,
        "supports_runtime_efficiency_claim": False,
        "supports_rendering_recovery": False,
        "metrics_computed": False,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "collection_safe_to_launch": safe_count == len(rows) and bool(rows),
        "manifest_entry_count": len(rows),
        "safe_collection_entry_count": safe_count,
        "overwrite_blocker_count": overwrite_count,
        "missing_source_command_count": missing_command_count,
        "existing_log_count": existing_log_count,
        "supported_conclusions": [
            "Runtime-cost collection safety can be preflighted from the M44 wrapper plan without launching runtime commands.",
            "The current wrapper plan can identify whether command/log targets risk overwriting existing artifacts.",
        ],
        "unsupported_conclusions": [
            "Runtime-cost metric values.",
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Runtime-cost logs are still unavailable unless existing logs are detected by this preflight.",
            "A fresh output root is required before launching any collection command that currently targets existing M32 artifacts.",
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 46 should remain bounded: clone the approved train/render runtime-cost commands into a fresh "
            "M46 output root, rerun this preflight, and only launch one short collection if all blockers clear."
        ),
    }


def write_report(path, rows, summary):
    lines = [
        "# Milestone 45 runtime-cost collection preflight",
        "",
        "Paper-scale gate: NO-GO",
        "Runtime-cost metric values: unavailable",
        "Metrics computed: false",
        "No train/render/eval runtime launched.",
        "",
        "## Collection Preflight",
        "",
        "| Metric | Status | Safe to launch | Required log available | Failure condition |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {metric_id} | {collection_status} | {collection_safe_to_launch} | {required_log_available} | {failure_condition} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Manifest entries: {summary['manifest_entry_count']}",
            f"- Safe collection entries: {summary['safe_collection_entry_count']}",
            f"- Existing-output overwrite blockers: {summary['overwrite_blocker_count']}",
            f"- Existing runtime-cost logs: {summary['existing_log_count']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: runtime-cost collection preflight and overwrite-risk classification.",
            "- Unsupported: runtime-cost values, runtime efficiency claims, SRD-GS superiority, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Preflight bounded SRD-GS runtime-cost collection safety.")
    parser.add_argument("--wrapper_plan_csv", required=True, type=Path)
    parser.add_argument("--immutable_root", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    wrapper_rows = _read_csv(args.wrapper_plan_csv)
    rows = build_preflight_rows(wrapper_rows, args.immutable_root)
    summary = build_summary(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "runtime_cost_collection_preflight.csv", rows)
    _write_json(args.output_dir / "runtime_cost_collection_preflight.json", summary)
    write_report(args.output_dir / "runtime_cost_collection_preflight.md", rows, summary)
    print(f"Wrote {args.output_dir / 'runtime_cost_collection_preflight.csv'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_collection_preflight.json'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_collection_preflight.md'}")


if __name__ == "__main__":
    main()
