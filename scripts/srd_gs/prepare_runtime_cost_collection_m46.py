import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


FIELDS = [
    "metric_id",
    "wrapper_status",
    "source_command_file",
    "source_command_available",
    "required_log",
    "required_log_available",
    "runtime_launch_required_for_m46",
    "runtime_launched",
    "planned_wrapper_mode",
    "collection_method",
    "failure_condition",
    "next_action",
    "source_result_root",
    "target_result_root",
    "source_model_root",
    "target_model_root",
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


def _read_text(path):
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8")


def _replace_path(text, old_path, new_path):
    old_text = str(old_path)
    new_text = str(new_path)
    return text.replace(old_text, new_text)


def _rewrite_command(command_text, source_result_root, target_result_root, source_model_root, target_model_root):
    updated = _replace_path(command_text, source_result_root, target_result_root)
    updated = _replace_path(updated, source_model_root, target_model_root)
    return updated


def _rewrite_required_log(path, source_result_root, target_result_root):
    return _replace_path(str(path), source_result_root, target_result_root)


def build_fresh_plan(wrapper_rows, source_result_root, target_result_root, source_model_root, target_model_root):
    target_result_root.mkdir(parents=True, exist_ok=True)
    target_model_root.mkdir(parents=True, exist_ok=True)
    command_map = {}
    rows = []
    for source in wrapper_rows:
        old_command_file = Path(source.get("source_command_file", ""))
        command_name = old_command_file.name
        new_command_file = target_result_root / command_name
        if command_name not in command_map:
            command_text = _read_text(old_command_file)
            rewritten_command = _rewrite_command(
                command_text,
                source_result_root,
                target_result_root,
                source_model_root,
                target_model_root,
            )
            if rewritten_command:
                new_command_file.write_text(rewritten_command, encoding="utf-8")
            command_map[command_name] = new_command_file

        required_log = _rewrite_required_log(source.get("required_log", ""), source_result_root, target_result_root)
        log_available = Path(required_log).exists() and Path(required_log).is_file() and Path(required_log).stat().st_size > 0
        command_available = new_command_file.exists() and new_command_file.read_text(encoding="utf-8").strip() != ""
        rows.append(
            {
                "metric_id": source.get("metric_id", ""),
                "wrapper_status": "fresh_root_plan_ready" if command_available else "blocked_missing_cloned_command",
                "source_command_file": str(new_command_file),
                "source_command_available": "true" if command_available else "false",
                "required_log": required_log,
                "required_log_available": "true" if log_available else "false",
                "runtime_launch_required_for_m46": "false",
                "runtime_launched": "false",
                "planned_wrapper_mode": "fresh_root_no_launch_package",
                "collection_method": source.get("collection_method", ""),
                "failure_condition": "none" if command_available else "cloned command is missing or empty",
                "next_action": "rerun collection preflight before any bounded runtime-cost launch",
                "source_result_root": str(source_result_root),
                "target_result_root": str(target_result_root),
                "source_model_root": str(source_model_root),
                "target_model_root": str(target_model_root),
            }
        )
    return rows


def run_preflight(preflight_script, fresh_plan_csv, immutable_root, output_dir):
    subprocess.run(
        [
            sys.executable,
            str(preflight_script),
            "--wrapper_plan_csv",
            str(fresh_plan_csv),
            "--immutable_root",
            str(immutable_root),
            "--output_dir",
            str(output_dir),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads((output_dir / "runtime_cost_collection_preflight.json").read_text(encoding="utf-8"))


def build_summary(rows, preflight_summary):
    return {
        "milestone": "M46",
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
        "fresh_wrapper_entry_count": len(rows),
        "cloned_command_count": len({row["source_command_file"] for row in rows if row["source_command_available"] == "true"}),
        "fresh_required_log_available_count": sum(1 for row in rows if row["required_log_available"] == "true"),
        "preflight_collection_safe_to_launch": bool(preflight_summary.get("collection_safe_to_launch")),
        "preflight_safe_collection_entry_count": preflight_summary.get("safe_collection_entry_count", 0),
        "preflight_overwrite_blocker_count": preflight_summary.get("overwrite_blocker_count", 0),
        "preflight_existing_log_count": preflight_summary.get("existing_log_count", 0),
        "supported_conclusions": [
            "Runtime-cost train/render command artifacts can be cloned into a fresh M46 output root.",
            "The cloned M46 wrapper plan can be checked with the existing M45 collection preflight.",
        ],
        "unsupported_conclusions": [
            "Runtime-cost metric values.",
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Runtime-cost logs are still unavailable until a future bounded runtime-cost collection is launched.",
            "CUDA/storage/process runtime gates must be checked immediately before any collection launch.",
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 47 should remain bounded: run CUDA/storage/process preflight for the fresh M46 package, "
            "then launch at most one short runtime-cost collection only if every gate passes."
        ),
    }


def write_report(path, rows, summary):
    lines = [
        "# Milestone 46 fresh-root runtime-cost collection package",
        "",
        "Paper-scale gate: NO-GO",
        "Runtime-cost metric values: unavailable",
        "Metrics computed: false",
        "No train/render/eval runtime launched.",
        "",
        "## Fresh Wrapper Plan",
        "",
        "| Metric | Status | Command available | Required log available |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {metric_id} | {wrapper_status} | {source_command_available} | {required_log_available} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Fresh wrapper entries: {summary['fresh_wrapper_entry_count']}",
            f"- Cloned command files: {summary['cloned_command_count']}",
            f"- Preflight safe to launch: {str(summary['preflight_collection_safe_to_launch']).lower()}",
            f"- Preflight overwrite blockers: {summary['preflight_overwrite_blocker_count']}",
            "",
            "## Claim Boundary",
            "",
            "- Supported: fresh-root runtime-cost command packaging and preflight readiness.",
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
    parser = argparse.ArgumentParser(description="Prepare a fresh-root SRD-GS runtime-cost collection package.")
    parser.add_argument("--wrapper_plan_csv", required=True, type=Path)
    parser.add_argument("--source_result_root", required=True, type=Path)
    parser.add_argument("--source_model_root", required=True, type=Path)
    parser.add_argument("--target_result_root", required=True, type=Path)
    parser.add_argument("--target_model_root", required=True, type=Path)
    parser.add_argument("--immutable_root", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--preflight_script", default=Path("scripts/srd_gs/preflight_runtime_cost_collection_m45.py"), type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    wrapper_rows = _read_csv(args.wrapper_plan_csv)
    rows = build_fresh_plan(
        wrapper_rows,
        args.source_result_root,
        args.target_result_root,
        args.source_model_root,
        args.target_model_root,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fresh_plan_csv = args.output_dir / "fresh_runtime_cost_wrapper_plan.csv"
    _write_csv(fresh_plan_csv, rows)
    preflight_summary = run_preflight(
        args.preflight_script,
        fresh_plan_csv,
        args.immutable_root,
        args.output_dir / "preflight",
    )
    summary = build_summary(rows, preflight_summary)
    _write_json(args.output_dir / "fresh_runtime_cost_wrapper_plan.json", summary)
    write_report(args.output_dir / "fresh_runtime_cost_wrapper_plan.md", rows, summary)
    print(f"Wrote {fresh_plan_csv}")
    print(f"Wrote {args.output_dir / 'fresh_runtime_cost_wrapper_plan.json'}")
    print(f"Wrote {args.output_dir / 'fresh_runtime_cost_wrapper_plan.md'}")
    print(f"Wrote {args.output_dir / 'preflight' / 'runtime_cost_collection_preflight.json'}")


if __name__ == "__main__":
    main()
