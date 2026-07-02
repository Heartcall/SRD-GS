import argparse
import csv
import json
from pathlib import Path


NON_TRAIN_COMMANDS = [
    "mesh_command.txt",
    "texture_command.txt",
    "render_eval_pairs_command.txt",
    "eval_gt_mesh_command.txt",
]


def _read_text(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _bool_text(value):
    return "true" if value else "false"


def inspect_result_root(result_root, label):
    result_root = Path(result_root)
    train_command_path = result_root / "train_command.txt"
    train_command = _read_text(train_command_path)
    non_train_text = "\n".join(_read_text(result_root / name) for name in NON_TRAIN_COMMANDS)
    expected_loss_log = result_root / "loss_log.csv"
    failure_panel_dir = result_root / "eval_with_gt_mesh" / "failure_case_panels"

    return {
        "label": label,
        "result_root": str(result_root),
        "train_command_available": train_command_path.exists() and train_command_path.stat().st_size > 0,
        "loss_log_path_in_train_command": "--srd_loss_log_path" in train_command and "loss_log.csv" in train_command,
        "expected_loss_log_path": str(expected_loss_log),
        "loss_log_path_leaks_to_non_train_commands": "--srd_loss_log_path" in non_train_text,
        "failure_panel_output_dir_expected": failure_panel_dir.exists(),
        "expected_failure_panel_dir": str(failure_panel_dir),
        "dry_run_contract_ready": (
            train_command_path.exists()
            and "--srd_loss_log_path" in train_command
            and "loss_log.csv" in train_command
            and "--srd_loss_log_path" not in non_train_text
            and failure_panel_dir.exists()
        ),
    }


def write_csv(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = {key: _bool_text(value) if isinstance(value, bool) else value for key, value in row.items()}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serialized.keys()))
        writer.writeheader()
        writer.writerow(serialized)


def build_summary(row):
    return {
        "label": row["label"],
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "dry_run_contract_ready": row["dry_run_contract_ready"],
        "supported_conclusions": [
            "Future bounded runs can write a train-only SRD loss CSV when the dry-run contract is ready.",
            "Future eval outputs have a concrete failure-panel directory target.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Root-cause proof from dry-run instrumentation alone.",
            "Paper-scale rendering, geometry, or material claims.",
        ],
        "recommended_next_milestone": (
            "Run one bounded single-scene instrumented smoke/control only after the dry-run "
            "contract is verified and GPU/storage gates are explicit."
        ),
    }


def write_report(path, row, summary):
    lines = [
        "# Milestone 29 failure/loss instrumentation contract",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Dry-run Contract",
        "",
        f"- Label: {row['label']}",
        f"- Train command available: {row['train_command_available']}",
        f"- Loss log path in train command: {row['loss_log_path_in_train_command']}",
        f"- Loss log path leaks to non-train commands: {row['loss_log_path_leaks_to_non_train_commands']}",
        f"- Failure-panel output directory expected: {row['failure_panel_output_dir_expected']}",
        f"- Dry-run contract ready: {row['dry_run_contract_ready']}",
        "",
        "## Claim Boundary",
        "",
        "- Supported: dry-run instrumentation readiness for future bounded runs.",
        "- Unsupported: runtime quality, root-cause proof, SRD-GS superiority, or paper-scale claims.",
        "",
        "## Recommended Next Milestone",
        "",
        summary["recommended_next_milestone"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect SRD-GS loss/failure instrumentation dry-run readiness.")
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--label", default="M29_dryrun")
    parser.add_argument("--output_dir", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    row = inspect_result_root(args.result_root, args.label)
    summary = build_summary(row)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "failure_loss_instrumentation.csv"
    json_path = output_dir / "failure_loss_instrumentation.json"
    report_path = output_dir / "failure_loss_instrumentation.md"
    write_csv(csv_path, row)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_report(report_path, row, summary)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
