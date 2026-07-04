import argparse
import csv
import json
from pathlib import Path


TARGETS = [
    {
        "metric_id": "runtime/training_time",
        "source_reason": "training_time_not_available",
        "command_file": "train_command.txt",
        "required_log": "runtime_cost/train_timing.json",
        "collection_method": "wrap train command with wall-clock timer and write start/end/duration seconds",
    },
    {
        "metric_id": "runtime/peak_memory",
        "source_reason": "peak_memory_not_available",
        "command_file": "train_command.txt",
        "required_log": "runtime_cost/gpu_memory_trace.csv",
        "collection_method": "sample nvidia-smi during train command and report max used memory",
    },
    {
        "metric_id": "runtime/render_fps",
        "source_reason": "render_fps_not_available",
        "command_file": "render_eval_pairs_command.txt",
        "required_log": "runtime_cost/render_timing.json",
        "collection_method": "wrap render-eval-pairs command and divide rendered frame count by elapsed seconds",
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


def _command_available(result_root, command_file):
    path = Path(result_root) / command_file
    return path.exists() and path.read_text(encoding="utf-8").strip() != ""


def _log_available(result_root, required_log):
    path = Path(result_root) / required_log
    return path.exists() and path.stat().st_size > 0


def build_contract(result_root, metrics_rows):
    rows = []
    manifest_entries = []
    for target in TARGETS:
        source_metric = _find_metric(metrics_rows, target["metric_id"])
        command_available = _command_available(result_root, target["command_file"])
        log_available = _log_available(result_root, target["required_log"])
        if log_available:
            status = "log_available_ready_for_metric_parse"
            next_action = "parse runtime-cost log in a future bounded metric pass"
        elif command_available:
            status = "contract_defined_needs_future_runtime"
            next_action = "run a future bounded command through the runtime-cost logger"
        else:
            status = "blocked_missing_source_command"
            next_action = "write or recover the source command before runtime-cost logging"
        rows.append(
            {
                "metric_id": target["metric_id"],
                "source_metric_reason": source_metric.get("not_available_reason", target["source_reason"]),
                "status": status,
                "source_command_file": target["command_file"],
                "source_command_available": "true" if command_available else "false",
                "required_log": target["required_log"],
                "required_log_available": "true" if log_available else "false",
                "metrics_computed": "false",
                "collection_method": target["collection_method"],
                "next_action": next_action,
            }
        )
        manifest_entries.append(
            {
                "metric_id": target["metric_id"],
                "command_file": str(Path(result_root) / target["command_file"]),
                "required_log": str(Path(result_root) / target["required_log"]),
                "collection_method": target["collection_method"],
                "expected_parser": "future_bounded_runtime_cost_parser",
            }
        )
    return rows, manifest_entries


def build_summary(result_root, rows):
    instrumentable = sum(1 for row in rows if row["status"] in {"contract_defined_needs_future_runtime", "log_available_ready_for_metric_parse"})
    logged = sum(1 for row in rows if row["required_log_available"] == "true")
    blocked = len(rows) - instrumentable
    return {
        "milestone": "M43",
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
        "result_root": str(result_root),
        "contract_count": len(rows),
        "instrumentable_contract_count": instrumentable,
        "logged_metric_count": logged,
        "blocked_contract_count": blocked,
        "supported_conclusions": [
            "Runtime-cost logging contract paths can be defined for training time, peak memory, and render FPS.",
            "Existing command files are sufficient to instrument a future bounded runtime-cost collection pass.",
        ],
        "unsupported_conclusions": [
            "Runtime-cost metric values.",
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Runtime-cost logs have not been collected yet.",
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 44 should remain bounded and either run a dry-run wrapper validation for runtime-cost logging "
            "or execute one short bounded runtime-cost collection only after preflight gates pass."
        ),
    }


def write_report(path, rows, summary):
    lines = [
        "# Milestone 43 runtime-cost logging contract",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "Runtime-cost metric values: unavailable",
        "Metrics computed: false",
        "No train/render/eval runtime launched.",
        "",
        "## Contract Matrix",
        "",
        "| Metric | Status | Command | Required log | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {metric_id} | {status} | {source_command_available} | {required_log} | {next_action} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Contract count: {summary['contract_count']}",
            f"- Instrumentable contracts: {summary['instrumentable_contract_count']}",
            f"- Logs currently available: {summary['logged_metric_count']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: runtime-cost logging contract definition for a future bounded run.",
            "- Unsupported: runtime-cost values, efficiency claims, SRD-GS superiority, or paper-scale claims.",
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
    parser = argparse.ArgumentParser(description="Define SRD-GS runtime-cost logging contract paths.")
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--metrics_csv", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics_rows = _read_csv(args.metrics_csv)
    rows, manifest_entries = build_contract(args.result_root, metrics_rows)
    summary = build_summary(args.result_root, rows)
    manifest_template = {
        "schema_version": 1,
        "milestone": "M43",
        "paper_scale_gate": "NO-GO",
        "runtime_launched": False,
        "metrics_computed": False,
        "entries": manifest_entries,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "runtime_cost_logging_contract.csv", rows)
    _write_json(args.output_dir / "runtime_cost_logging_contract.json", summary)
    write_report(args.output_dir / "runtime_cost_logging_contract.md", rows, summary)
    _write_json(args.output_dir / "runtime_cost_manifest_template.json", manifest_template)
    print(f"Wrote {args.output_dir / 'runtime_cost_logging_contract.csv'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_logging_contract.json'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_logging_contract.md'}")
    print(f"Wrote {args.output_dir / 'runtime_cost_manifest_template.json'}")


if __name__ == "__main__":
    main()
