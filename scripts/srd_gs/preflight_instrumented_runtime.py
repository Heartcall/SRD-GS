import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path


NON_TRAIN_COMMANDS = [
    "mesh_command.txt",
    "texture_command.txt",
    "render_eval_pairs_command.txt",
    "eval_gt_mesh_command.txt",
]

PROCESS_PATTERN = (
    "train.py|render_eval_pairs.py|eval_reflective_assets.py|extract_surface_mesh.py|"
    "export_pbr_textures.py|run_branch_raster_smoke_one_scene.sh|run_single_scene_comparison.sh"
)


def parse_nvidia_smi_gpu_rows(text):
    rows = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            index = int(parts[0])
            memory_used_mb = int(parts[1].split()[0])
            utilization_percent = int(parts[2].split()[0])
        except (ValueError, IndexError):
            continue
        rows[index] = {
            "index": index,
            "memory_used_mb": memory_used_mb,
            "utilization_percent": utilization_percent,
        }
    return rows


def _run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode not in (0, 1):
        return ""
    return result.stdout


def collect_gpu_rows():
    text = _run_command(
        [
            "nvidia-smi",
            "--query-gpu=index,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    return parse_nvidia_smi_gpu_rows(text)


def collect_process_matches():
    text = _run_command(["pgrep", "-af", PROCESS_PATTERN])
    return [line for line in text.splitlines() if line.strip()]


def workspace_free_gb(path):
    usage = shutil.disk_usage(path)
    return usage.free / (1024.0 ** 3)


def _read_text(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def instrumentation_contract_ready(result_root):
    result_root = Path(result_root)
    train_command = _read_text(result_root / "train_command.txt")
    non_train_text = "\n".join(_read_text(result_root / name) for name in NON_TRAIN_COMMANDS)
    failure_dir = result_root / "eval_with_gt_mesh" / "failure_case_panels"
    return (
        "--srd_loss_log_path" in train_command
        and "loss_log.csv" in train_command
        and "--srd_loss_log_path" not in non_train_text
        and failure_dir.exists()
    )


def summarize_preflight(
    label,
    result_root,
    gpu_rows,
    training_gpu_index,
    min_workspace_free_gb,
    workspace_free_gb,
    process_matches,
    max_gpu_utilization_percent,
):
    result_root = Path(result_root)
    gpu_row = gpu_rows.get(training_gpu_index)
    blockers = []
    warnings = []
    contract_ready = instrumentation_contract_ready(result_root)
    if not contract_ready:
        blockers.append("instrumentation_contract_not_ready")
    if gpu_row is None:
        blockers.append("training_gpu_not_visible")
    elif gpu_row["utilization_percent"] > max_gpu_utilization_percent:
        blockers.append("training_gpu_busy")
    if workspace_free_gb < min_workspace_free_gb:
        blockers.append("workspace_free_below_threshold")
    if process_matches:
        blockers.append("prohibited_processes_running")
    if workspace_free_gb < 30.0:
        warnings.append("workspace_storage_tight")

    runtime_go = not blockers
    return {
        "label": label,
        "result_root": str(result_root),
        "runtime_go": runtime_go,
        "paper_scale_gate": "NO-GO",
        "supports_paper_claim": False,
        "instrumentation_contract_ready": contract_ready,
        "training_gpu_index": training_gpu_index,
        "training_gpu_memory_used_mb": None if gpu_row is None else gpu_row["memory_used_mb"],
        "training_gpu_utilization_percent": None if gpu_row is None else gpu_row["utilization_percent"],
        "max_gpu_utilization_percent": max_gpu_utilization_percent,
        "workspace_free_gb": workspace_free_gb,
        "min_workspace_free_gb": min_workspace_free_gb,
        "process_match_count": len(process_matches),
        "process_matches": process_matches,
        "blockers": blockers,
        "warnings": warnings,
        "supported_conclusions": [
            "Runtime launch readiness can be gated before starting a bounded instrumented run.",
            "A NO-GO preflight prevents launching into known GPU/storage/process blockers.",
        ],
        "unsupported_conclusions": [
            "SRD-GS superiority over Ref-GS.",
            "Runtime loss progression or failure-case behavior.",
            "Paper-scale rendering, geometry, or material claims.",
        ],
        "recommended_next_milestone": (
            "Rerun this preflight when the hardcoded training GPU is idle and storage budget "
            "is acceptable; only then launch one bounded instrumented ball run."
        ),
    }


def _bool_text(value):
    return "true" if value else "false"


def _csv_row(summary):
    row = {}
    for key, value in summary.items():
        if isinstance(value, bool):
            row[key] = _bool_text(value)
        elif isinstance(value, list):
            row[key] = ";".join(value)
        else:
            row[key] = value
    return row


def write_outputs(output_dir, summary):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "instrumented_runtime_preflight.csv"
    json_path = output_dir / "instrumented_runtime_preflight.json"
    md_path = output_dir / "instrumented_runtime_preflight.md"

    row = _csv_row(summary)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Milestone 30 instrumented runtime preflight",
        "",
        f"Runtime GO: {summary['runtime_go']}",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Gates",
        "",
        f"- Instrumentation contract ready: {summary['instrumentation_contract_ready']}",
        f"- Training GPU index: {summary['training_gpu_index']}",
        f"- Training GPU utilization: {summary['training_gpu_utilization_percent']}",
        f"- Workspace free GB: {summary['workspace_free_gb']:.2f}",
        f"- Process match count: {summary['process_match_count']}",
        f"- Blockers: {', '.join(summary['blockers']) or 'none'}",
        f"- Warnings: {', '.join(summary['warnings']) or 'none'}",
        "",
        "## Claim Boundary",
        "",
        "- Supported: bounded runtime-readiness gate.",
        "- Unsupported: runtime quality, root-cause proof, SRD-GS superiority, or paper-scale claims.",
        "",
        "## Recommended Next Milestone",
        "",
        summary["recommended_next_milestone"],
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, json_path, md_path


def parse_args():
    parser = argparse.ArgumentParser(description="Preflight a bounded SRD-GS instrumented runtime launch.")
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--label", default="M30_preflight")
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--training_gpu_index", type=int, default=2)
    parser.add_argument("--max_gpu_utilization_percent", type=int, default=50)
    parser.add_argument("--workspace_path", type=Path, default=Path("."))
    parser.add_argument("--min_workspace_free_gb", type=float, default=25.0)
    parser.add_argument("--gpu_rows_text", default="")
    parser.add_argument("--workspace_free_gb", type=float, default=None)
    parser.add_argument("--skip_process_scan", action="store_true", default=False)
    return parser.parse_args()


def main():
    args = parse_args()
    gpu_rows = parse_nvidia_smi_gpu_rows(args.gpu_rows_text) if args.gpu_rows_text else collect_gpu_rows()
    free_gb = args.workspace_free_gb
    if free_gb is None:
        free_gb = workspace_free_gb(args.workspace_path)
    process_matches = [] if args.skip_process_scan else collect_process_matches()
    summary = summarize_preflight(
        label=args.label,
        result_root=args.result_root,
        gpu_rows=gpu_rows,
        training_gpu_index=args.training_gpu_index,
        min_workspace_free_gb=args.min_workspace_free_gb,
        workspace_free_gb=free_gb,
        process_matches=process_matches,
        max_gpu_utilization_percent=args.max_gpu_utilization_percent,
    )
    csv_path, json_path, md_path = write_outputs(args.output_dir, summary)
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
