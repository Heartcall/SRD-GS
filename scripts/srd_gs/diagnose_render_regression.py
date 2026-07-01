import argparse
import csv
import json
import os
from pathlib import Path

import imageio.v2 as imageio
import numpy as np


METRIC_NAMES = [
    "psnr",
    "ssim",
    "refl_psnr",
    "refl_ssim",
    "chamfer_distance",
    "f_score",
    "normal_mae",
]

MAP_FIELDS = [
    "pred_rgb",
    "gt_rgb",
    "diffuse_rgb",
    "specular_rgb",
    "branch_gate_map",
    "roughness_map",
    "reflective_mask",
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


def _metric_values(metrics_path):
    if not metrics_path.exists():
        return {}, [f"missing:{metrics_path}"]
    payload = _read_json(metrics_path)
    values = {}
    for item in payload.get("metrics", []):
        name = item.get("name")
        if name:
            values[name] = item.get("value")
    return values, []


def _baking_values(report_path):
    if not report_path.exists():
        return {}, [f"missing:{report_path}"]
    payload = _read_json(report_path)
    return {
        "highlight_leakage_score": payload.get("highlight_leakage_score"),
        "valid_weight_fraction": payload.get("valid_weight_fraction"),
        "observation_count": payload.get("observation_count"),
    }, []


def _manifest_values(manifest_path):
    if not manifest_path.exists():
        return {}, [], [f"missing:{manifest_path}"]
    payload = _read_json(manifest_path)
    policy = payload.get("branch_map_policy", {})
    values = {
        "iteration": payload.get("iteration"),
        "frame_count": len(payload.get("frames", [])),
        "policy": policy.get("policy"),
        "gate_applied": policy.get("gate_applied"),
        "branch_gate_weight": policy.get("branch_gate_weight"),
        "render_gate_weight": policy.get("render_gate_weight"),
    }
    return values, payload.get("frames", []), []


def _read_image(path):
    array = imageio.imread(path)
    array = np.asarray(array)
    if array.dtype == np.uint8:
        return array.astype(np.float32) / 255.0
    return np.nan_to_num(array.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)


def _field_stats(pair_root, frames, field):
    values = []
    missing = []
    for frame in frames:
        rel_path = frame.get(field)
        if not rel_path:
            continue
        path = pair_root / rel_path
        if not path.exists():
            missing.append(f"missing:{path}")
            continue
        image = _read_image(path)
        values.append(image.reshape(-1))

    if not values:
        return {
            "field": field,
            "frame_count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
        }, missing

    vector = np.concatenate(values)
    return {
        "field": field,
        "frame_count": len(values),
        "mean": float(vector.mean()),
        "std": float(vector.std()),
        "min": float(vector.min()),
        "max": float(vector.max()),
    }, missing


def _residual_stats(pair_root, frames):
    residuals = []
    masked_residuals = []
    missing = []
    for frame in frames:
        pred_rel = frame.get("pred_rgb")
        gt_rel = frame.get("gt_rgb")
        if not pred_rel or not gt_rel:
            continue
        pred_path = pair_root / pred_rel
        gt_path = pair_root / gt_rel
        if not pred_path.exists() or not gt_path.exists():
            missing.append(f"missing:{pred_path if not pred_path.exists() else gt_path}")
            continue
        pred = _read_image(pred_path)
        gt = _read_image(gt_path)
        residual = np.abs(pred - gt).mean(axis=-1) if pred.ndim == 3 else np.abs(pred - gt)
        residuals.append(residual.reshape(-1))

        mask_rel = frame.get("reflective_mask")
        if mask_rel:
            mask_path = pair_root / mask_rel
            if mask_path.exists():
                mask = _read_image(mask_path)
                if mask.ndim == 3:
                    mask = mask.mean(axis=-1)
                selected = residual[mask > 0.5]
                if selected.size:
                    masked_residuals.append(selected.reshape(-1))

    stats = []
    if residuals:
        vector = np.concatenate(residuals)
        stats.append(
            {
                "field": "rgb_residual_l1",
                "frame_count": len(residuals),
                "mean": float(vector.mean()),
                "std": float(vector.std()),
                "min": float(vector.min()),
                "max": float(vector.max()),
            }
        )
    if masked_residuals:
        vector = np.concatenate(masked_residuals)
        stats.append(
            {
                "field": "reflective_rgb_residual_l1",
                "frame_count": len(masked_residuals),
                "mean": float(vector.mean()),
                "std": float(vector.std()),
                "min": float(vector.min()),
                "max": float(vector.max()),
            }
        )
    return stats, missing


def build_diagnosis(cases):
    case_rows = []
    map_rows = []
    for label, root in cases:
        result_root = Path(root)
        metrics, missing = _metric_values(result_root / "eval_with_gt_mesh" / "metrics.json")
        baking, baking_missing = _baking_values(result_root / "pbr_textures_specular_free" / "baking_report.json")
        manifest, frames, manifest_missing = _manifest_values(
            result_root / "render_eval_pairs" / "render_eval_manifest.json"
        )
        missing.extend(baking_missing)
        missing.extend(manifest_missing)

        row = {
            "label": label,
            "result_root": str(result_root),
            "missing_artifacts": ";".join(missing),
        }
        row.update({name: metrics.get(name) for name in METRIC_NAMES})
        row.update(baking)
        row.update(manifest)
        case_rows.append(row)

        pair_root = result_root / "render_eval_pairs"
        for field in MAP_FIELDS:
            stats, field_missing = _field_stats(pair_root, frames, field)
            missing.extend(field_missing)
            stats.update({"label": label, "result_root": str(result_root)})
            map_rows.append(stats)
        residual_stats, residual_missing = _residual_stats(pair_root, frames)
        missing.extend(residual_missing)
        for stats in residual_stats:
            stats.update({"label": label, "result_root": str(result_root)})
            map_rows.append(stats)
        row["missing_artifacts"] = ";".join(missing)

    delta_rows = _pairwise_deltas(case_rows)
    flags = _diagnosis_flags(case_rows)
    return {
        "case_rows": case_rows,
        "map_rows": map_rows,
        "delta_rows": delta_rows,
        "diagnosis_flags": flags,
    }


def _as_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _pairwise_deltas(case_rows):
    if not case_rows:
        return []
    baseline = case_rows[0]
    rows = []
    for row in case_rows[1:]:
        delta = {
            "baseline_label": baseline["label"],
            "comparison_label": row["label"],
        }
        for name in [
            "psnr",
            "refl_psnr",
            "chamfer_distance",
            "f_score",
            "normal_mae",
            "highlight_leakage_score",
        ]:
            base_value = _as_float(baseline.get(name))
            value = _as_float(row.get(name))
            delta[f"{name}_delta_vs_baseline"] = None if base_value is None or value is None else value - base_value
        rows.append(delta)
    return rows


def _diagnosis_flags(case_rows):
    flags = []
    if len(case_rows) < 2:
        return flags
    baseline = case_rows[0]
    baseline_psnr = _as_float(baseline.get("psnr"))
    baseline_refl = _as_float(baseline.get("refl_psnr"))
    degraded_rows = []
    for row in case_rows[1:]:
        psnr = _as_float(row.get("psnr"))
        refl = _as_float(row.get("refl_psnr"))
        if baseline_psnr is not None and baseline_refl is not None and psnr is not None and refl is not None:
            if psnr < baseline_psnr and refl < baseline_refl:
                degraded_rows.append(row)
    if degraded_rows:
        flags.append("rendering_regression_vs_baseline")
    if any(_as_float(row.get("render_gate_weight")) == 0.0 for row in degraded_rows):
        flags.append("render_gate_activation_not_sole_cause")

    baseline_chamfer = _as_float(baseline.get("chamfer_distance"))
    if baseline_chamfer is not None and degraded_rows:
        if any(_as_float(row.get("chamfer_distance")) is not None and _as_float(row.get("chamfer_distance")) < baseline_chamfer for row in degraded_rows):
            flags.append("geometry_can_improve_while_rendering_degrades")
    return flags


def _stringify(value):
    if value is None:
        return ""
    return str(value)


def write_csv(rows, path, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _stringify(row.get(field)) for field in fieldnames})


def write_report(diagnosis, path):
    case_rows = diagnosis["case_rows"]
    delta_rows = diagnosis["delta_rows"]
    flags = diagnosis["diagnosis_flags"]

    lines = [
        "# Milestone 22 Render Regression Artifact Diagnosis",
        "",
        "Scope: read-only comparison over existing M18/M20/M21 `ball` artifacts.",
        "",
        "Paper-scale gate: NO-GO",
        "SRD-GS superiority: unsupported",
        "",
        "## Diagnosis Flags",
    ]
    if flags:
        lines.extend([f"- {flag}" for flag in flags])
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            "| Label | Iter | Render Gate | PSNR | Refl-PSNR | Chamfer | F-score | Leakage |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in case_rows:
        lines.append(
            "| {label} | {iteration} | {render_gate_weight} | {psnr} | {refl_psnr} | {chamfer_distance} | {f_score} | {highlight_leakage_score} |".format(
                **{key: _stringify(row.get(key)) for key in row}
            )
        )

    lines.extend(["", "## Pairwise Deltas"])
    for row in delta_rows:
        lines.append(
            "- {comparison_label} vs {baseline_label}: PSNR {psnr_delta_vs_baseline}, Refl-PSNR {refl_psnr_delta_vs_baseline}, Chamfer {chamfer_distance_delta_vs_baseline}, leakage {highlight_leakage_score_delta_vs_baseline}".format(
                **{key: _stringify(row.get(key)) for key in row}
            )
        )

    lines.extend(
        [
            "",
            "## Supported Conclusions",
            "",
            "- This artifact diagnosis can identify metric and diagnostic-map differences among the supplied completed runs.",
            "- If `render_gate_activation_not_sole_cause` is present, at least one degraded comparison has `render_gate_weight=0.0`, so rendered gate activation alone does not explain the rendering drop.",
            "",
            "## Unsupported Conclusions",
            "",
            "- No multi-scene or paper-scale quality claim is supported.",
            "- No stable SRD-GS superiority claim is supported.",
            "- No PBR material accuracy claim is supported without GT albedo/roughness.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(diagnosis, output_dir):
    output_dir = Path(output_dir)
    case_fields = [
        "label",
        "result_root",
        "iteration",
        "policy",
        "gate_applied",
        "branch_gate_weight",
        "render_gate_weight",
        "frame_count",
        *METRIC_NAMES,
        "highlight_leakage_score",
        "valid_weight_fraction",
        "observation_count",
        "missing_artifacts",
    ]
    map_fields = ["label", "result_root", "field", "frame_count", "mean", "std", "min", "max"]
    delta_fields = [
        "baseline_label",
        "comparison_label",
        "psnr_delta_vs_baseline",
        "refl_psnr_delta_vs_baseline",
        "chamfer_distance_delta_vs_baseline",
        "f_score_delta_vs_baseline",
        "normal_mae_delta_vs_baseline",
        "highlight_leakage_score_delta_vs_baseline",
    ]
    write_csv(diagnosis["case_rows"], output_dir / "case_summary.csv", case_fields)
    write_csv(diagnosis["map_rows"], output_dir / "map_stats.csv", map_fields)
    write_csv(diagnosis["delta_rows"], output_dir / "pairwise_deltas.csv", delta_fields)
    summary = {
        "diagnosis_flags": diagnosis["diagnosis_flags"],
        "case_count": len(diagnosis["case_rows"]),
        "map_stat_count": len(diagnosis["map_rows"]),
        "paper_scale_gate": "NO-GO",
        "srd_gs_superiority": "unsupported",
    }
    (output_dir / "diagnosis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(diagnosis, output_dir / "diagnosis_report.md")


def main():
    parser = argparse.ArgumentParser(description="Read-only SRD-GS render-regression artifact diagnosis")
    parser.add_argument("--case", action="append", required=True, help="LABEL=RESULT_ROOT; repeat in comparison order")
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    cases = [parse_case(case_arg) for case_arg in args.case]
    diagnosis = build_diagnosis(cases)
    write_outputs(diagnosis, args.output_dir)
    print("Wrote diagnosis outputs:", os.path.abspath(args.output_dir))
    print("Diagnosis flags:", ",".join(diagnosis["diagnosis_flags"]) or "none")


if __name__ == "__main__":
    main()
