import argparse
import csv
import os
import shutil

import imageio.v2 as imageio
import numpy as np


DRY_RUN_MATRIX = [
    ("Shiny Blender Synthetic", "ball", "refgs_baseline", "completed_smoke", "20-iter engineering smoke only"),
    ("Shiny Blender Synthetic", "ball", "full_srd_gs", "completed_smoke", "20-iter engineering smoke only"),
    ("Shiny Blender Synthetic", "ball", "no_reflection_branch", "planned", "not executed"),
    ("Shiny Blender Synthetic", "ball", "no_branch_separation", "planned", "not executed"),
    ("Shiny Blender Synthetic", "ball", "no_geo_loss", "planned", "not executed"),
    ("Shiny Blender Synthetic", "ball", "all_branch_mesh", "planned", "not executed"),
    ("GlossySyntheticConverted", "teapot_blender", "refgs_baseline", "planned", "dry-run candidate"),
    ("GlossySyntheticConverted", "teapot_blender", "full_srd_gs", "planned", "dry-run candidate"),
    ("GlossySyntheticConverted", "bell_blender", "refgs_baseline", "planned", "dry-run candidate"),
    ("GlossySyntheticConverted", "bell_blender", "full_srd_gs", "planned", "dry-run candidate"),
]


def ensure_dirs(output_root):
    dirs = {
        "raw_logs": os.path.join(output_root, "raw_logs"),
        "metrics": os.path.join(output_root, "metrics"),
        "tables": os.path.join(output_root, "tables"),
        "figures": os.path.join(output_root, "figures"),
        "failure_cases": os.path.join(output_root, "failure_cases"),
    }
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
    return dirs


def read_smoke_metrics(smoke_root):
    metrics_path = os.path.join(smoke_root, "ball", "eval", "metrics_summary.csv")
    if not os.path.exists(metrics_path):
        return [], metrics_path
    with open(metrics_path, "r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle)), metrics_path


def write_matrix(path):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset", "scene", "variant", "status", "note"],
        )
        writer.writeheader()
        for dataset, scene, variant, status, note in DRY_RUN_MATRIX:
            writer.writerow({
                "dataset": dataset,
                "scene": scene,
                "variant": variant,
                "status": status,
                "note": note,
            })


def copy_smoke_metrics(rows, source_path, metrics_dir, tables_dir):
    if rows and os.path.exists(source_path):
        metrics_copy = os.path.join(metrics_dir, "smoke_metrics_summary.csv")
        tables_copy = os.path.join(tables_dir, "smoke_metrics_summary.csv")
        shutil.copyfile(source_path, metrics_copy)
        shutil.copyfile(source_path, tables_copy)
        return metrics_copy, tables_copy
    empty_path = os.path.join(tables_dir, "smoke_metrics_summary.csv")
    with open(empty_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scene", "variant", "category", "name", "value", "not_available_reason"])
        writer.writeheader()
    return None, empty_path


def extract_highlight_leakage(rows):
    values = {}
    for row in rows:
        if row.get("name") != "highlight_leakage_score":
            continue
        value = row.get("value")
        if value in ("", None):
            continue
        values[row.get("scene", "unknown")] = float(value)
    return values


def save_bar_png(values, path, title_value=1.0):
    width, height = 420, 220
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    if not values:
        image[80:140, 80:340] = np.array([220, 220, 220], dtype=np.uint8)
    else:
        items = list(values.items())
        max_value = max(max(v for _, v in items), 1e-6, title_value)
        bar_width = max(30, (width - 80) // max(len(items), 1))
        for idx, (_, value) in enumerate(items):
            x0 = 40 + idx * bar_width
            x1 = min(x0 + bar_width - 10, width - 20)
            bar_height = int((height - 70) * (value / max_value))
            y0 = height - 30 - bar_height
            image[y0:height - 30, x0:x1] = np.array([40, 120, 200], dtype=np.uint8)
    imageio.imwrite(path, image)


def save_claim_gate_png(path):
    image = np.full((180, 420, 3), 255, dtype=np.uint8)
    image[40:140, 60:360] = np.array([220, 60, 60], dtype=np.uint8)
    imageio.imwrite(path, image)


def write_summary(path, matrix_path, smoke_table_path, highlight_values):
    baseline = highlight_values.get("refgs_baseline")
    srd = highlight_values.get("full_srd_gs")
    leakage_answer = "Needs Verification"
    if baseline is not None and srd is not None:
        leakage_answer = (
            "engineering smoke diagnostic: SRD-GS {} vs Ref-GS {}; not a paper-scale claim".format(
                srd, baseline
            )
        )

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# SRD-GS Paper-scale Experiment Expansion Summary\n\n")
        handle.write("Paper-scale claim gate: NO-GO\n\n")
        handle.write("This package expands the experiment structure after the Milestone 9 smoke, but it does not claim paper-scale superiority. Current evidence is a 20-iteration engineering smoke on one scene.\n\n")
        handle.write("## Inputs\n\n")
        handle.write("- Dry-run matrix: `{}`\n".format(matrix_path))
        handle.write("- Smoke metrics table: `{}`\n\n".format(smoke_table_path))
        handle.write("## Required Questions\n\n")
        handle.write("1. SRD-GS 是否降低 reflective-region normal MAE？\n")
        handle.write("   - Answer: NO-GO. Reflective-region normal MAE is unavailable because GT normal/render-region evaluation is not integrated.\n")
        handle.write("2. SRD-GS 是否降低 reflective-region mesh Chamfer / 提高 F-score？\n")
        handle.write("   - Answer: NO-GO. GT geometry loading/evaluation is not integrated for the smoke outputs.\n")
        handle.write("3. SRD-GS 是否降低 albedo highlight leakage？\n")
        handle.write("   - Answer: {}.\n".format(leakage_answer))
        handle.write("4. SRD-GS 是否保持接近 Ref-GS 的 PSNR/SSIM/LPIPS？\n")
        handle.write("   - Answer: NO-GO. Saved pred/GT render pairs and LPIPS are not integrated in the smoke eval.\n")
        handle.write("5. 哪个消融最关键？\n")
        handle.write("   - Answer: Needs Verification. Ablation configs exist, but no paper-scale ablation runs have been executed.\n")
        handle.write("6. 有没有反驳主假设的结果？\n")
        handle.write("   - Answer: No claim-bearing refutation can be assessed yet; missing GT/render metrics dominate the current gate.\n")
        handle.write("7. 下一步该改代码还是改论文 claim？\n")
        handle.write("   - Answer: 改代码优先。需要 render/GT export、accepted GT geometry loader、真实 SRD branch-map rasterization，再决定论文 claim。\n\n")
        handle.write("## Claim Boundary\n\n")
        handle.write("- Engineering pipeline: GO for one-scene 20-iteration smoke.\n")
        handle.write("- Paper-scale quality claim: NO-GO.\n")
        handle.write("- Stable mesh/material improvement claim: NO-GO.\n")


def main():
    parser = argparse.ArgumentParser(description="Generate SRD-GS paper-scale dry-run package")
    parser.add_argument("--smoke_root", default="outputs/srd_gs_smoke")
    parser.add_argument("--output_root", default="outputs/srd_gs_experiments")
    args = parser.parse_args()

    dirs = ensure_dirs(args.output_root)
    rows, smoke_metrics_path = read_smoke_metrics(args.smoke_root)

    matrix_path = os.path.join(dirs["tables"], "paper_scale_dry_run_matrix.csv")
    write_matrix(matrix_path)
    _, smoke_table_path = copy_smoke_metrics(rows, smoke_metrics_path, dirs["metrics"], dirs["tables"])

    highlight_values = extract_highlight_leakage(rows)
    save_bar_png(highlight_values, os.path.join(dirs["figures"], "smoke_highlight_leakage.png"))
    save_claim_gate_png(os.path.join(dirs["failure_cases"], "claim_gate_status.png"))

    raw_log_path = os.path.join(dirs["raw_logs"], "paper_scale_gate.txt")
    with open(raw_log_path, "w", encoding="utf-8") as handle:
        handle.write("Paper-scale claim gate: NO-GO\n")
        handle.write("Reason: only one 20-iteration smoke scene has completed; render/GT and GT geometry metrics are not integrated.\n")

    summary_path = os.path.join(args.output_root, "experiment_summary.md")
    write_summary(summary_path, matrix_path, smoke_table_path, highlight_values)
    print("Wrote paper-scale package:", args.output_root)


if __name__ == "__main__":
    main()
