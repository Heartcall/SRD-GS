import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.srd_gs.preflight_instrumented_runtime import collect_gpu_rows, parse_nvidia_smi_gpu_rows


REQUIRED_METRICS = {"runtime/training_time", "runtime/peak_memory", "runtime/render_fps"}


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


def _command_text(path):
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8").strip()


def _utc_now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _metric_rows_by_id(rows):
    return {row.get("metric_id", ""): row for row in rows}


def _metric_log_path(rows_by_id, metric_id, fallback):
    value = rows_by_id.get(metric_id, {}).get("required_log", "")
    return Path(value) if value else fallback


def _run_timed_shell_command(command_text, cwd, stdout_path, stderr_path, gpu_trace_path=None, args=None):
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    started_at = _utc_now()
    samples = []
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open("w", encoding="utf-8") as stderr_handle:
        process = subprocess.Popen(
            command_text,
            cwd=str(cwd),
            shell=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            executable="/bin/bash",
        )
        if gpu_trace_path is not None and args is not None:
            samples = _collect_memory_samples_during_process(process, start, gpu_trace_path, args)
        returncode = process.wait()
    ended_at = _utc_now()
    wall_seconds = time.monotonic() - start
    return {
        "command": command_text,
        "returncode": returncode,
        "success": returncode == 0,
        "wall_seconds": wall_seconds,
        "started_at_utc": started_at,
        "ended_at_utc": ended_at,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "gpu_sample_count": len(samples),
    }, samples


def _collect_memory_samples_during_process(process, start_monotonic, gpu_trace_path, args):
    gpu_trace_path.parent.mkdir(parents=True, exist_ok=True)
    samples = []
    with gpu_trace_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "elapsed_seconds",
                "gpu_index",
                "memory_used_mb",
                "utilization_percent",
                "source",
            ],
        )
        writer.writeheader()
        if args.gpu_rows_text:
            for row in parse_nvidia_smi_gpu_rows(args.gpu_rows_text).values():
                sample = {
                    "elapsed_seconds": "{:.6f}".format(time.monotonic() - start_monotonic),
                    "gpu_index": row["index"],
                    "memory_used_mb": row["memory_used_mb"],
                    "utilization_percent": row["utilization_percent"],
                    "source": "provided_gpu_rows_text",
                }
                writer.writerow(sample)
                samples.append(sample)
            process.wait()
            return samples

        interval = max(args.gpu_sample_interval_seconds, 0.1)
        while process.poll() is None:
            _write_current_gpu_samples(writer, samples, start_monotonic, "nvidia-smi")
            time.sleep(interval)
        _write_current_gpu_samples(writer, samples, start_monotonic, "nvidia-smi_final")
    return samples


def _write_current_gpu_samples(writer, samples, start_monotonic, source):
    for row in collect_gpu_rows().values():
        sample = {
            "elapsed_seconds": "{:.6f}".format(time.monotonic() - start_monotonic),
            "gpu_index": row["index"],
            "memory_used_mb": row["memory_used_mb"],
            "utilization_percent": row["utilization_percent"],
            "source": source,
        }
        writer.writerow(sample)
        samples.append(sample)


def _peak_memory_mb(samples, training_gpu_index):
    values = [
        int(sample["memory_used_mb"])
        for sample in samples
        if int(sample["gpu_index"]) == training_gpu_index
    ]
    if not values:
        return None
    return max(values)


def _manifest_frame_count(result_root):
    manifest_path = Path(result_root) / "render_eval_pairs" / "render_eval_manifest.json"
    if not manifest_path.exists():
        return 0, manifest_path
    manifest = _read_json(manifest_path)
    return len(manifest.get("frames") or []), manifest_path


def _build_metric_rows(train_timing, render_timing, peak_memory_mb, frame_count, log_paths):
    rows = []
    train_success = bool(train_timing and train_timing.get("success"))
    render_success = bool(render_timing and render_timing.get("success"))
    rows.append(
        {
            "metric_id": "runtime/training_time",
            "status": "measured" if train_success else "failed",
            "value": "" if train_timing is None else "{:.6f}".format(train_timing["wall_seconds"]),
            "unit": "seconds",
            "source_log": str(log_paths["train_timing"]),
            "frame_count": "",
            "failure_condition": "" if train_success else "train_command_failed_or_not_run",
        }
    )
    rows.append(
        {
            "metric_id": "runtime/peak_memory",
            "status": "measured" if peak_memory_mb is not None else "not_available",
            "value": "" if peak_memory_mb is None else str(peak_memory_mb),
            "unit": "MB",
            "source_log": str(log_paths["gpu_trace"]),
            "frame_count": "",
            "failure_condition": "" if peak_memory_mb is not None else "gpu_memory_trace_missing_training_gpu",
        }
    )
    render_fps = None
    if render_success and frame_count > 0 and render_timing["wall_seconds"] > 0:
        render_fps = frame_count / render_timing["wall_seconds"]
    rows.append(
        {
            "metric_id": "runtime/render_fps",
            "status": "measured" if render_fps is not None else "failed",
            "value": "" if render_fps is None else "{:.6f}".format(render_fps),
            "unit": "frames_per_second",
            "source_log": str(log_paths["render_timing"]),
            "frame_count": str(frame_count),
            "failure_condition": "" if render_fps is not None else "render_command_failed_or_manifest_missing",
        }
    )
    return rows, render_fps


def _write_metric_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _csv_safe_summary(summary):
    row = {}
    for key, value in summary.items():
        if key == "metric_rows":
            continue
        if isinstance(value, bool):
            row[key] = _bool_text(value)
        elif isinstance(value, list):
            row[key] = ";".join(str(item) for item in value)
        elif isinstance(value, dict):
            row[key] = json.dumps(value, sort_keys=True)
        else:
            row[key] = value
    return row


def _write_summary_csv(path, summary):
    row = _csv_safe_summary(summary)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def _write_report(path, summary):
    metric_lines = [
        "| Metric | Status | Value | Unit | Frames |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    for row in summary["metric_rows"]:
        metric_lines.append(
            "| {metric_id} | {status} | {value} | {unit} | {frame_count} |".format(**row)
        )
    lines = [
        "# Milestone 48 runtime-cost collection",
        "",
        "Paper-scale gate: NO-GO",
        "Runtime launched: {}".format(summary["runtime_launched"]),
        "Metrics computed: {}".format(summary["metrics_computed"]),
        "SRD-GS superiority: unsupported",
        "Runtime efficiency claim: unsupported",
        "",
        "## Metrics",
        "",
    ] + metric_lines + [
        "",
        "## Claim Boundary",
        "",
        "- Supported: bounded runtime-cost values for one short ball run, if all three metrics are measured.",
        "- Unsupported: runtime efficiency, rendering recovery, GT PBR material accuracy, SRD-GS superiority, or paper-scale claims.",
        "",
        "## Blockers",
        "",
        "- {}".format("; ".join(summary["remaining_blockers"]) or "none"),
        "",
        "## Recommended Next Milestone",
        "",
        summary["recommended_next_milestone"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_without_launch(args, fresh_rows, launch_gate, blockers):
    result_root = Path(args.result_root)
    runtime_dir = result_root / "runtime_cost"
    rows_by_id = _metric_rows_by_id(fresh_rows)
    log_paths = {
        "train_timing": _metric_log_path(rows_by_id, "runtime/training_time", runtime_dir / "train_timing.json"),
        "gpu_trace": _metric_log_path(rows_by_id, "runtime/peak_memory", runtime_dir / "gpu_memory_trace.csv"),
        "render_timing": _metric_log_path(rows_by_id, "runtime/render_fps", runtime_dir / "render_timing.json"),
    }
    metric_rows, _ = _build_metric_rows(None, None, None, 0, log_paths)
    summary = _base_summary(args, fresh_rows, launch_gate, metric_rows, log_paths, blockers)
    summary["supported_conclusions"] = [
        "The bounded M48 collection correctly refused to launch because the immediate prelaunch gate was NO-GO.",
    ]
    summary["remaining_blockers"] = [
        "Immediate prelaunch gate is NO-GO: {}.".format(", ".join(launch_gate.get("blockers", [])) or "unknown"),
        "Runtime-cost logs and values remain unavailable.",
        "Accepted GT depth/material artifacts remain missing.",
        "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
        "Paper-scale validation remains blocked by single-scene short-budget evidence.",
    ]
    summary["recommended_next_milestone"] = (
        "Milestone 49 should remain bounded: rerun the M47/M48 prelaunch gate when training GPU "
        "utilization is below threshold, then launch the same single short runtime-cost collection only if "
        "runtime_go becomes true."
    )
    return summary


def _base_summary(args, fresh_rows, launch_gate, metric_rows, log_paths, blockers):
    measured_count = sum(1 for row in metric_rows if row["status"] == "measured")
    metrics_computed = measured_count == 3 and not blockers
    return {
        "label": args.label,
        "milestone": "M48",
        "result_root": str(args.result_root),
        "paper_scale_gate": "NO-GO",
        "runtime_launched": False,
        "training_launched": False,
        "rendering_launched": False,
        "mesh_texture_eval_launched": False,
        "metrics_computed": metrics_computed,
        "supports_bounded_runtime_cost_measurement": metrics_computed,
        "supports_runtime_efficiency_claim": False,
        "supports_srd_gs_superiority": False,
        "supports_paper_claim": False,
        "launch_gate_runtime_go": bool(launch_gate.get("runtime_go")),
        "launch_gate_blockers": launch_gate.get("blockers", []),
        "fresh_wrapper_entry_count": len(fresh_rows),
        "training_gpu_index": args.training_gpu_index,
        "training_time_seconds": None,
        "peak_memory_mb": None,
        "render_fps": None,
        "frame_count": 0,
        "train_timing_log": str(log_paths["train_timing"]),
        "gpu_memory_trace_log": str(log_paths["gpu_trace"]),
        "render_timing_log": str(log_paths["render_timing"]),
        "metric_rows": metric_rows,
        "blockers": blockers,
        "supported_conclusions": [
            "M48 can launch exactly one bounded train/render runtime-cost collection when the launch gate is GO.",
        ],
        "unsupported_conclusions": [
            "Runtime efficiency claims.",
            "SRD-GS superiority over Ref-GS.",
            "Rendering recovery.",
            "GT PBR material accuracy.",
            "Paper-scale or multi-scene quality claims.",
        ],
        "remaining_blockers": [
            "Accepted GT depth/material artifacts remain missing.",
            "F-score remains zero and LPIPS/Refl-LPIPS remain high in prior diagnostics.",
            "Paper-scale validation remains blocked by single-scene short-budget evidence.",
        ],
        "recommended_next_milestone": (
            "Milestone 49 should remain bounded: synthesize M48 runtime-cost values with the existing M32-M47 "
            "diagnostic table and decide whether the next single action should be a retry/debug if any runtime "
            "metric failed, or a one-scene metric-availability bridge if runtime collection succeeded."
        ),
    }


def collect_runtime_cost(args, fresh_rows, launch_gate):
    result_root = Path(args.result_root)
    runtime_dir = result_root / "runtime_cost"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    rows_by_id = _metric_rows_by_id(fresh_rows)
    blockers = []
    if set(rows_by_id.keys()) != REQUIRED_METRICS:
        blockers.append("fresh_plan_metric_set_incomplete")
    if not launch_gate.get("runtime_go"):
        blockers.append("launch_gate_not_go")
    for metric_id in REQUIRED_METRICS:
        if rows_by_id.get(metric_id, {}).get("wrapper_status") != "fresh_root_plan_ready":
            blockers.append("fresh_wrapper_not_ready")
            break

    log_paths = {
        "train_timing": _metric_log_path(rows_by_id, "runtime/training_time", runtime_dir / "train_timing.json"),
        "gpu_trace": _metric_log_path(rows_by_id, "runtime/peak_memory", runtime_dir / "gpu_memory_trace.csv"),
        "render_timing": _metric_log_path(rows_by_id, "runtime/render_fps", runtime_dir / "render_timing.json"),
    }
    train_command_file = rows_by_id.get("runtime/training_time", {}).get("source_command_file", "")
    render_command_file = rows_by_id.get("runtime/render_fps", {}).get("source_command_file", "")
    train_command = _command_text(train_command_file)
    render_command = _command_text(render_command_file)
    if not train_command:
        blockers.append("train_command_missing_or_empty")
    if not render_command:
        blockers.append("render_command_missing_or_empty")
    for path in log_paths.values():
        if path.exists():
            blockers.append("runtime_cost_log_already_exists")
            break

    if blockers:
        return summarize_without_launch(args, fresh_rows, launch_gate, blockers)

    train_timing, gpu_samples = _run_timed_shell_command(
        train_command,
        args.cwd,
        runtime_dir / "train_stdout.log",
        runtime_dir / "train_stderr.log",
        gpu_trace_path=log_paths["gpu_trace"],
        args=args,
    )
    train_timing["command_file"] = str(train_command_file)
    _write_json(log_paths["train_timing"], train_timing)
    peak_memory = _peak_memory_mb(gpu_samples, args.training_gpu_index)

    render_timing = None
    frame_count = 0
    render_manifest_path = result_root / "render_eval_pairs" / "render_eval_manifest.json"
    if train_timing["success"]:
        render_timing, _ = _run_timed_shell_command(
            render_command,
            args.cwd,
            runtime_dir / "render_stdout.log",
            runtime_dir / "render_stderr.log",
        )
        render_timing["command_file"] = str(render_command_file)
        frame_count, render_manifest_path = _manifest_frame_count(result_root)
        render_timing["frame_count"] = frame_count
        render_timing["render_eval_manifest"] = str(render_manifest_path)
        _write_json(log_paths["render_timing"], render_timing)
    else:
        blockers.append("train_command_failed")

    metric_rows, render_fps = _build_metric_rows(train_timing, render_timing, peak_memory, frame_count, log_paths)
    if not train_timing["success"]:
        blockers.append("training_runtime_failed")
    if render_timing is None or not render_timing["success"]:
        blockers.append("render_runtime_failed")
    if peak_memory is None:
        blockers.append("peak_memory_unavailable")
    if render_fps is None:
        blockers.append("render_fps_unavailable")

    summary = _base_summary(args, fresh_rows, launch_gate, metric_rows, log_paths, blockers)
    summary.update(
        {
            "runtime_launched": True,
            "training_launched": True,
            "rendering_launched": render_timing is not None,
            "metrics_computed": not blockers,
            "supports_bounded_runtime_cost_measurement": not blockers,
            "training_time_seconds": train_timing["wall_seconds"],
            "peak_memory_mb": peak_memory,
            "render_fps": render_fps,
            "frame_count": frame_count,
            "render_eval_manifest": str(render_manifest_path),
        }
    )
    if not blockers:
        summary["supported_conclusions"] = [
            "One bounded short-budget ball runtime-cost collection produced training time, peak GPU memory, and render FPS values.",
        ]
    return summary


def write_outputs(output_dir, summary):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metric_csv = output_dir / "runtime_cost_metrics.csv"
    summary_csv = output_dir / "runtime_cost_summary.csv"
    summary_json = output_dir / "runtime_cost_metrics.json"
    summary_md = output_dir / "runtime_cost_metrics.md"
    _write_metric_csv(metric_csv, summary["metric_rows"])
    _write_summary_csv(summary_csv, summary)
    _write_json(summary_json, summary)
    _write_report(summary_md, summary)
    return metric_csv, summary_csv, summary_json, summary_md


def parse_args():
    parser = argparse.ArgumentParser(description="Collect one bounded SRD-GS runtime-cost run after M47 GO.")
    parser.add_argument("--fresh_plan_csv", required=True, type=Path)
    parser.add_argument("--launch_gate_json", required=True, type=Path)
    parser.add_argument("--result_root", required=True, type=Path)
    parser.add_argument("--label", default="M48_runtime_cost_collection")
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--training_gpu_index", type=int, default=2)
    parser.add_argument("--gpu_sample_interval_seconds", type=float, default=1.0)
    parser.add_argument("--gpu_rows_text", default="")
    parser.add_argument("--cwd", type=Path, default=REPO_ROOT)
    return parser.parse_args()


def main():
    args = parse_args()
    fresh_rows = _read_csv(args.fresh_plan_csv)
    launch_gate = _read_json(args.launch_gate_json)
    summary = collect_runtime_cost(args, fresh_rows, launch_gate)
    metric_csv, summary_csv, summary_json, summary_md = write_outputs(args.output_dir, summary)
    print(f"Wrote {metric_csv}")
    print(f"Wrote {summary_csv}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {summary_md}")


if __name__ == "__main__":
    main()
