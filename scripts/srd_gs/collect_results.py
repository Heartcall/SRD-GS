import argparse
import csv
import json
import os


def infer_scene_variant(metrics_path, results_root):
    rel = os.path.relpath(metrics_path, results_root)
    parts = rel.split(os.sep)
    if len(parts) >= 4 and parts[-2] == "eval":
        return parts[-4], parts[-3]
    if len(parts) >= 3:
        return parts[-3], parts[-2]
    if len(parts) == 2:
        return "unknown_scene", parts[0]
    return "unknown_scene", "unknown_variant"


def collect_metric_rows(results_root):
    rows = []
    for current_root, _, files in os.walk(results_root):
        if "metrics.json" not in files:
            continue
        metrics_path = os.path.join(current_root, "metrics.json")
        scene, variant = infer_scene_variant(metrics_path, results_root)
        with open(metrics_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for metric in payload.get("metrics", []):
            row = {
                "scene": scene,
                "variant": variant,
                "category": metric.get("category"),
                "name": metric.get("name"),
                "value": "" if metric.get("value") is None else str(metric.get("value")),
                "supports_hypothesis": metric.get("supports_hypothesis"),
                "higher_is_better": metric.get("higher_is_better"),
                "not_available_reason": metric.get("not_available_reason"),
                "metrics_path": metrics_path,
            }
            rows.append(row)
    return rows


def write_rows(rows, output_csv):
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    fieldnames = [
        "scene",
        "variant",
        "category",
        "name",
        "value",
        "supports_hypothesis",
        "higher_is_better",
        "not_available_reason",
        "metrics_path",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Collect SRD-GS one-scene ablation metrics")
    parser.add_argument("--results_root", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    rows = collect_metric_rows(args.results_root)
    write_rows(rows, args.output_csv)
    print("Wrote rows:", len(rows))
    print("Output CSV:", args.output_csv)


if __name__ == "__main__":
    main()
