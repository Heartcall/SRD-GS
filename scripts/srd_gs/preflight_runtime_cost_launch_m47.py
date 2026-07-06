import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.srd_gs.preflight_instrumented_runtime import (
    collect_gpu_rows,
    collect_torch_cuda_probe,
    parse_nvidia_smi_gpu_rows,
)


PROCESS_PATTERN = (
    "external_repos/SRD-GS.*(train.py|render_eval_pairs.py|eval_reflective_assets.py|"
    "extract_surface_mesh.py|export_pbr_textures.py|run_branch_raster_smoke_one_scene.sh|"
    "run_single_scene_comparison.sh)"
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _bool_text(value):
    return "true" if value else "false"


def _run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode not in (0, 1):
        return ""
    return result.stdout


def collect_process_matches():
    text = _run_command(["pgrep", "-af", PROCESS_PATTERN])
    return [line for line in text.splitlines() if line.strip()]


def workspace_free_gb(path):
    usage = shutil.disk_usage(path)
    return usage.free / (1024.0 ** 3)


def _file_nonempty(path):
    candidate = Path(path)
    return candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0


def _command_text(path):
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8").strip()


def summarize_launch_gate(
    label,
    fresh_rows,
    collection_preflight,
    result_root,
    gpu_rows,
    torch_cuda_available,
    torch_device_count,
    training_gpu_index,
    max_gpu_utilization_percent,
    workspace_free_gb_value,
    min_workspace_free_gb,
    process_matches,
):
    blockers = []
    warnings = []
    metric_ids = {row.get("metric_id", "") for row in fresh_rows}
    required_metrics = {"runtime/training_time", "runtime/peak_memory", "runtime/render_fps"}
    if metric_ids != required_metrics:
        blockers.append("fresh_plan_metric_set_incomplete")

    unavailable_commands = [row.get("source_command_file", "") for row in fresh_rows if not _command_text(row.get("source_command_file", ""))]
    if unavailable_commands:
        blockers.append("fresh_command_missing_or_empty")

    not_ready_rows = [row.get("metric_id", "") for row in fresh_rows if row.get("wrapper_status") != "fresh_root_plan_ready"]
    if not_ready_rows:
        blockers.append("fresh_wrapper_not_ready")

    if not collection_preflight.get("collection_safe_to_launch"):
        blockers.append("collection_preflight_not_safe")
    if collection_preflight.get("overwrite_blocker_count", 0):
        blockers.append("existing_output_overwrite_blocker")

    runtime_cost_log_count = sum(1 for row in fresh_rows if _file_nonempty(row.get("required_log", "")))
    gpu_row = gpu_rows.get(training_gpu_index)
    torch_training_gpu_visible = bool(torch_cuda_available) and torch_device_count is not None and torch_device_count > training_gpu_index
    if not torch_training_gpu_visible:
        blockers.append("training_gpu_not_visible")
    if gpu_row is None and torch_training_gpu_visible:
        blockers.append("gpu_utilization_unavailable")
    elif gpu_row is not None and gpu_row["utilization_percent"] > max_gpu_utilization_percent:
        blockers.append("training_gpu_busy")

    if workspace_free_gb_value < min_workspace_free_gb:
        blockers.append("workspace_free_below_threshold")
    if process_matches:
        blockers.append("prohibited_processes_running")
    if workspace_free_gb_value < 30.0:
        warnings.append("workspace_storage_tight")

    return {
        "label": label,
        "milestone": "M47",
        "result_root": str(result_root),
        "paper_scale_gate": "NO-GO",
        "runtime_go": not blockers,
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "metrics_computed": False,
        "supports_paper_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_runtime_cost_claim": False,
        "supports_runtime_efficiency_claim": False,
        "fresh_wrapper_entry_count": len(fresh_rows),
        "runtime_cost_log_count": runtime_cost_log_count,
        "collection_preflight_safe": bool(collection_preflight.get("collection_safe_to_launch")),
        "collection_preflight_overwrite_blocker_count": collection_preflight.get("overwrite_blocker_count", 0),
        "torch_cuda_available": torch_cuda_available,
        "torch_device_count": torch_device_count,
        "torch_training_gpu_visible": torch_training_gpu_visible,
        "training_gpu_index": training_gpu_index,
        "training_gpu_memory_used_mb": None if gpu_row is None else gpu_row["memory_used_mb"],
        "training_gpu_utilization_percent": None if gpu_row is None else gpu_row["utilization_percent"],
        "max_gpu_utilization_percent": max_gpu_utilization_percent,
        "workspace_free_gb": workspace_free_gb_value,
        "min_workspace_free_gb": min_workspace_free_gb,
        "process_match_count": len(process_matches),
        "process_matches": process_matches,
        "blockers": blockers,
        "warnings": warnings,
        "supported_conclusions": [
            "The fresh M46 runtime-cost package can be checked for CUDA, storage, process, and overwrite readiness.",
            "A runtime GO/NO-GO decision can be made before launching any collection command.",
        ],
        "unsupported_conclusions": [
            "Runtime-cost metric values.",
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Runtime-cost logs are still unavailable until a future bounded collection is launched.",
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        ],
        "recommended_next_milestone": (
            "Milestone 48 should remain bounded: if M47 runtime_go is true, launch exactly one short "
            "runtime-cost collection for the fresh M46 package and parse only the resulting runtime logs."
        ),
    }


def _csv_row(summary):
    row = {}
    for key, value in summary.items():
        if isinstance(value, bool):
            row[key] = _bool_text(value)
        elif isinstance(value, list):
            row[key] = ";".join(str(item) for item in value)
        else:
            row[key] = value
    return row


def write_outputs(output_dir, summary):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "runtime_cost_launch_gate.csv"
    json_path = output_dir / "runtime_cost_launch_gate.json"
    md_path = output_dir / "runtime_cost_launch_gate.md"
    row = _csv_row(summary)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    _write_json(json_path, summary)
    lines = [
        "# Milestone 47 runtime-cost launch gate",
        "",
        f"Runtime GO: {summary['runtime_go']}",
        "Paper-scale gate: NO-GO",
        "Runtime-cost metric values: unavailable",
        "Metrics computed: false",
        "No train/render/eval runtime launched.",
        "",
        "## Gates",
        "",
        f"- Fresh wrapper entries: {summary['fresh_wrapper_entry_count']}",
        f"- Collection preflight safe: {summary['collection_preflight_safe']}",
        f"- Overwrite blockers: {summary['collection_preflight_overwrite_blocker_count']}",
        f"- Torch CUDA available: {summary['torch_cuda_available']}",
        f"- Torch device count: {summary['torch_device_count']}",
        f"- Torch training GPU visible: {summary['torch_training_gpu_visible']}",
        f"- Training GPU index: {summary['training_gpu_index']}",
        f"- Training GPU utilization: {summary['training_gpu_utilization_percent']}",
        f"- Workspace free GB: {summary['workspace_free_gb']:.2f}",
        f"- Process match count: {summary['process_match_count']}",
        f"- Blockers: {', '.join(summary['blockers']) or 'none'}",
        f"- Warnings: {', '.join(summary['warnings']) or 'none'}",
        "",
        "## Claim Boundary",
        "",
        "- Supported: bounded runtime-cost launch readiness gate.",
        "- Unsupported: runtime-cost values, runtime efficiency claims, SRD-GS superiority, or paper-scale claims.",
        "",
        "## Recommended Next Milestone",
        "",
        summary["recommended_next_milestone"],
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, json_path, md_path


def parse_args():
    parser = argparse.ArgumentParser(description="Preflight a fresh SRD-GS runtime-cost collection launch.")
    parser.add_argument("--fresh_plan_csv", required=True, type=Path)
    parser.add_argument("--collection_preflight_json", required=True, type=Path)
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--label", default="M47_runtime_cost_launch_gate")
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--training_gpu_index", type=int, default=2)
    parser.add_argument("--max_gpu_utilization_percent", type=int, default=50)
    parser.add_argument("--workspace_path", type=Path, default=Path("."))
    parser.add_argument("--min_workspace_free_gb", type=float, default=25.0)
    parser.add_argument("--gpu_rows_text", default="")
    parser.add_argument("--workspace_free_gb", type=float, default=None)
    parser.add_argument("--torch_cuda_available", choices=["true", "false"], default=None)
    parser.add_argument("--torch_device_count", type=int, default=None)
    parser.add_argument("--skip_process_scan", action="store_true", default=False)
    return parser.parse_args()


def main():
    args = parse_args()
    fresh_rows = _read_csv(args.fresh_plan_csv)
    collection_preflight = _read_json(args.collection_preflight_json)
    gpu_rows = parse_nvidia_smi_gpu_rows(args.gpu_rows_text) if args.gpu_rows_text else collect_gpu_rows()
    if args.torch_cuda_available is None or args.torch_device_count is None:
        torch_cuda_available, torch_device_count = collect_torch_cuda_probe()
    else:
        torch_cuda_available = args.torch_cuda_available == "true"
        torch_device_count = args.torch_device_count
    free_gb = args.workspace_free_gb
    if free_gb is None:
        free_gb = workspace_free_gb(args.workspace_path)
    process_matches = [] if args.skip_process_scan else collect_process_matches()
    summary = summarize_launch_gate(
        label=args.label,
        fresh_rows=fresh_rows,
        collection_preflight=collection_preflight,
        result_root=args.result_root,
        gpu_rows=gpu_rows,
        torch_cuda_available=torch_cuda_available,
        torch_device_count=torch_device_count,
        training_gpu_index=args.training_gpu_index,
        max_gpu_utilization_percent=args.max_gpu_utilization_percent,
        workspace_free_gb_value=free_gb,
        min_workspace_free_gb=args.min_workspace_free_gb,
        process_matches=process_matches,
    )
    csv_path, json_path, md_path = write_outputs(args.output_dir, summary)
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
