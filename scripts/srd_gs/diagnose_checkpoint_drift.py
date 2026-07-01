import argparse
import csv
import json
import os
import re
from pathlib import Path

import numpy as np
from plyfile import PlyData


STAT_GROUPS = {
    "xyz": ["x", "y", "z"],
    "opacity_raw": ["opacity"],
    "opacity_activated": ["opacity"],
    "scale_raw": "scale_",
    "scale_exp": "scale_",
    "roughness_activated": "roughness_",
    "surface_roughness_activated": "surface_roughness_",
    "surface_albedo_raw": "surface_albedo_",
    "reflection_feature_abs": "reflection_feature_",
    "specular_weight_activated": "specular_weight_",
    "branch_gate_activated": "branch_gate_",
    "transport_feature_abs": "transport_feature_",
}

DELTA_GROUPS = [
    "opacity_activated",
    "scale_exp",
    "surface_roughness_activated",
    "reflection_feature_abs",
    "specular_weight_activated",
    "branch_gate_activated",
    "transport_feature_abs",
]


def parse_case(case_arg):
    if "=" not in case_arg:
        raise ValueError(f"Case must use LABEL=MODEL_ROOT format: {case_arg}")
    label, model_root = case_arg.split("=", 1)
    if not label:
        raise ValueError("Case label cannot be empty")
    return label, Path(model_root)


def sigmoid(values):
    values = np.asarray(values, dtype=np.float64)
    return 1.0 / (1.0 + np.exp(-values))


def safe_exp(values):
    values = np.asarray(values, dtype=np.float64)
    return np.exp(np.clip(values, -30.0, 30.0))


def _matching_names(names, spec):
    if isinstance(spec, list):
        return [name for name in spec if name in names]
    matched = [name for name in names if name.startswith(spec)]
    return sorted(matched, key=_natural_key)


def _natural_key(text):
    return [int(chunk) if chunk.isdigit() else chunk for chunk in re.split(r"(\d+)", text)]


def _extract_iteration(point_cloud_path):
    match = re.search(r"iteration_(\d+)", str(point_cloud_path))
    return int(match.group(1)) if match else None


def find_point_cloud(model_root):
    candidates = sorted(
        Path(model_root).glob("point_cloud/iteration_*/point_cloud.ply"),
        key=lambda path: _extract_iteration(path) or -1,
    )
    if candidates:
        return candidates[-1]
    direct = Path(model_root) / "point_cloud.ply"
    return direct if direct.exists() else None


def read_cfg_args(model_root):
    path = Path(model_root) / "cfg_args"
    if not path.exists():
        return {}, f"missing:{path}"
    text = path.read_text(encoding="utf-8")
    values = {}
    for key in [
        "enable_srd_gs",
        "eval",
        "srd_reflection_warmup",
        "srd_render_gate_start_iter",
        "srd_render_gate_ramp_iters",
        "srd_branch_gate_start_iter",
        "srd_branch_gate_ramp_iters",
        "srd_rasterize_branch_maps",
        "srd_use_branch_gate",
    ]:
        match = re.search(rf"{key}=([^,\)]+)", text)
        if match:
            values[key] = match.group(1).strip()
    return values, None


def _group_values(vertex, group_name, field_names):
    if not field_names:
        return None
    values = np.stack([np.asarray(vertex[name], dtype=np.float64) for name in field_names], axis=1)
    if group_name.endswith("_activated"):
        return sigmoid(values)
    if group_name.endswith("_exp"):
        return safe_exp(values)
    if group_name.endswith("_abs"):
        return np.abs(values)
    return values


def _stats(values):
    if values is None or values.size == 0:
        return {
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "p05": None,
            "p95": None,
        }
    flat = values.reshape(-1)
    return {
        "mean": float(np.mean(flat)),
        "std": float(np.std(flat)),
        "min": float(np.min(flat)),
        "max": float(np.max(flat)),
        "p05": float(np.percentile(flat, 5)),
        "p95": float(np.percentile(flat, 95)),
    }


def summarize_case(label, model_root):
    point_cloud_path = find_point_cloud(model_root)
    missing = []
    cfg, cfg_missing = read_cfg_args(model_root)
    if cfg_missing:
        missing.append(cfg_missing)

    if point_cloud_path is None:
        row = {
            "label": label,
            "model_root": str(model_root),
            "point_cloud_path": "",
            "iteration": "",
            "gaussian_count": "0",
            "missing_artifacts": f"missing:{Path(model_root) / 'point_cloud'}",
        }
        row.update(cfg)
        return row, []

    ply = PlyData.read(point_cloud_path)
    vertex = ply["vertex"].data
    names = vertex.dtype.names or []
    row = {
        "label": label,
        "model_root": str(model_root),
        "point_cloud_path": str(point_cloud_path),
        "iteration": _extract_iteration(point_cloud_path),
        "gaussian_count": len(vertex),
        "missing_artifacts": ";".join(missing),
    }
    row.update(cfg)

    stat_rows = []
    for group_name, spec in STAT_GROUPS.items():
        field_names = _matching_names(names, spec)
        values = _group_values(vertex, group_name, field_names)
        stats = _stats(values)
        stat_rows.append(
            {
                "label": label,
                "group": group_name,
                "attribute_count": len(field_names),
                "field_names": ";".join(field_names),
                **stats,
            }
        )
    return row, stat_rows


def _row_mean(stat_rows, label, group):
    for row in stat_rows:
        if row.get("label") == label and row.get("group") == group:
            value = row.get("mean")
            return None if value in (None, "") else float(value)
    return None


def build_diagnosis(cases):
    checkpoint_rows = []
    parameter_rows = []
    for label, model_root in cases:
        checkpoint_row, stat_rows = summarize_case(label, model_root)
        checkpoint_rows.append(checkpoint_row)
        parameter_rows.extend(stat_rows)

    delta_rows = build_delta_rows(checkpoint_rows, parameter_rows)
    flags = build_flags(checkpoint_rows, delta_rows)
    return {
        "checkpoint_rows": checkpoint_rows,
        "parameter_rows": parameter_rows,
        "delta_rows": delta_rows,
        "diagnosis_flags": flags,
    }


def build_delta_rows(checkpoint_rows, parameter_rows):
    if not checkpoint_rows:
        return []
    baseline_label = checkpoint_rows[0]["label"]
    rows = []
    for checkpoint_row in checkpoint_rows[1:]:
        label = checkpoint_row["label"]
        row = {
            "baseline_label": baseline_label,
            "comparison_label": label,
            "gaussian_count_delta_vs_baseline": int(checkpoint_row.get("gaussian_count") or 0)
            - int(checkpoint_rows[0].get("gaussian_count") or 0),
        }
        for group in DELTA_GROUPS:
            baseline_mean = _row_mean(parameter_rows, baseline_label, group)
            comparison_mean = _row_mean(parameter_rows, label, group)
            key = f"{group}_mean_delta_vs_baseline"
            row[key] = None if baseline_mean is None or comparison_mean is None else comparison_mean - baseline_mean
        rows.append(row)
    return rows


def build_flags(checkpoint_rows, delta_rows):
    flags = []
    if delta_rows and all(int(row.get("gaussian_count_delta_vs_baseline") or 0) == 0 for row in delta_rows):
        flags.append("no_gaussian_count_growth")
    if any(row.get("missing_artifacts") for row in checkpoint_rows):
        flags.append("missing_checkpoint_or_config_artifacts")
    if not any("train" in str(row.get("model_root", "")).lower() and row.get("missing_artifacts") == "" for row in checkpoint_rows):
        flags.append("training_loss_logs_unavailable")

    drift_groups = [
        "specular_weight_activated_mean_delta_vs_baseline",
        "branch_gate_activated_mean_delta_vs_baseline",
        "reflection_feature_abs_mean_delta_vs_baseline",
        "transport_feature_abs_mean_delta_vs_baseline",
    ]
    for row in delta_rows:
        for key in drift_groups:
            value = row.get(key)
            if value not in (None, "") and abs(float(value)) > 1e-3:
                flags.append("branch_or_specular_parameter_drift_present")
                return flags
    return flags


def stringify(value):
    if value is None:
        return ""
    return str(value)


def write_csv(rows, path, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: stringify(row.get(field)) for field in fieldnames})


def write_report(diagnosis, output_path):
    checkpoint_rows = diagnosis["checkpoint_rows"]
    delta_rows = diagnosis["delta_rows"]
    flags = diagnosis["diagnosis_flags"]
    lines = [
        "# Milestone 23 Checkpoint Drift Diagnosis",
        "",
        "Scope: read-only checkpoint/config diagnosis over completed M18/M20/M21 `ball` model artifacts.",
        "",
        "Paper-scale gate: NO-GO",
        "Complete root cause: unsupported",
        "SRD-GS superiority: unsupported",
        "",
        "## Diagnosis Flags",
    ]
    lines.extend([f"- {flag}" for flag in flags] or ["- none"])
    lines.extend(
        [
            "",
            "## Checkpoint Summary",
            "",
            "| Label | Iteration | Gaussian Count | eval | SRD enabled | Render Gate Start | Render Gate Ramp |",
            "| --- | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for row in checkpoint_rows:
        lines.append(
            "| {label} | {iteration} | {gaussian_count} | {eval} | {enable_srd_gs} | {srd_render_gate_start_iter} | {srd_render_gate_ramp_iters} |".format(
                label=stringify(row.get("label")),
                iteration=stringify(row.get("iteration")),
                gaussian_count=stringify(row.get("gaussian_count")),
                eval=stringify(row.get("eval")),
                enable_srd_gs=stringify(row.get("enable_srd_gs")),
                srd_render_gate_start_iter=stringify(row.get("srd_render_gate_start_iter")),
                srd_render_gate_ramp_iters=stringify(row.get("srd_render_gate_ramp_iters")),
            )
        )
    lines.extend(["", "## Deltas Versus Baseline"])
    for row in delta_rows:
        lines.append(
            "- {comparison_label} vs {baseline_label}: gaussian_count {gaussian_count_delta_vs_baseline}, opacity {opacity_activated_mean_delta_vs_baseline}, scale {scale_exp_mean_delta_vs_baseline}, specular_weight {specular_weight_activated_mean_delta_vs_baseline}, branch_gate {branch_gate_activated_mean_delta_vs_baseline}".format(
                **{key: stringify(row.get(key)) for key in row}
            )
        )
    lines.extend(
        [
            "",
            "## Supported Conclusions",
            "",
            "- This diagnosis can compare checkpoint-level Gaussian count and saved SRD parameter statistics across supplied completed runs.",
            "- If `no_gaussian_count_growth` is present, the compared checkpoints have the same Gaussian count, so count growth alone does not explain the rendering drop.",
            "- If `branch_or_specular_parameter_drift_present` is present, saved branch/specular parameters changed across checkpoints and are plausible targets for the next bounded investigation.",
            "",
            "## Unsupported Conclusions",
            "",
            "- This does not prove a complete rendering-regression root cause.",
            "- This does not support broad multi-scene or paper-scale claims.",
            "- This does not support stable SRD-GS superiority or PBR material quality claims.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(diagnosis, output_dir):
    output_dir = Path(output_dir)
    checkpoint_fields = [
        "label",
        "model_root",
        "point_cloud_path",
        "iteration",
        "gaussian_count",
        "enable_srd_gs",
        "eval",
        "srd_reflection_warmup",
        "srd_render_gate_start_iter",
        "srd_render_gate_ramp_iters",
        "srd_branch_gate_start_iter",
        "srd_branch_gate_ramp_iters",
        "srd_rasterize_branch_maps",
        "srd_use_branch_gate",
        "missing_artifacts",
    ]
    parameter_fields = [
        "label",
        "group",
        "attribute_count",
        "field_names",
        "mean",
        "std",
        "min",
        "max",
        "p05",
        "p95",
    ]
    delta_fields = [
        "baseline_label",
        "comparison_label",
        "gaussian_count_delta_vs_baseline",
        *[f"{group}_mean_delta_vs_baseline" for group in DELTA_GROUPS],
    ]
    write_csv(diagnosis["checkpoint_rows"], output_dir / "checkpoint_summary.csv", checkpoint_fields)
    write_csv(diagnosis["parameter_rows"], output_dir / "parameter_stats.csv", parameter_fields)
    write_csv(diagnosis["delta_rows"], output_dir / "parameter_deltas.csv", delta_fields)
    summary = {
        "diagnosis_flags": diagnosis["diagnosis_flags"],
        "case_count": len(diagnosis["checkpoint_rows"]),
        "parameter_stat_count": len(diagnosis["parameter_rows"]),
        "paper_scale_gate": "NO-GO",
        "complete_root_cause": "unsupported",
        "srd_gs_superiority": "unsupported",
    }
    (output_dir / "checkpoint_diagnosis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(diagnosis, output_dir / "checkpoint_diagnosis_report.md")


def main():
    parser = argparse.ArgumentParser(description="Read-only SRD-GS checkpoint drift diagnosis")
    parser.add_argument("--case", action="append", required=True, help="LABEL=MODEL_ROOT; repeat in comparison order")
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    cases = [parse_case(case_arg) for case_arg in args.case]
    diagnosis = build_diagnosis(cases)
    write_outputs(diagnosis, args.output_dir)
    print("Wrote checkpoint diagnosis outputs:", os.path.abspath(args.output_dir))
    print("Diagnosis flags:", ",".join(diagnosis["diagnosis_flags"]) or "none")


if __name__ == "__main__":
    main()
