#!/usr/bin/env python3
"""Collect lightweight metrics from existing Ref-GS experiment outputs."""

import argparse
import csv
import json
import re
from pathlib import Path


EVAL_RE = re.compile(r"\[ITER\s+(\d+)\]\s+Evaluating\s+(\w+):\s+L1\s+([0-9.eE+-]+)\s+PSNR\s+([0-9.eE+-]+)")


def collect_model(path: Path):
    rows = []
    cfg = path / "cfg_args"
    point_cloud = path / "point_cloud"
    iterations = sorted(point_cloud.glob("iteration_*")) if point_cloud.exists() else []
    logs = list(path.rglob("*.log")) + list(path.rglob("events.out.tfevents*"))
    row = {
        "model_path": str(path),
        "has_cfg_args": cfg.exists(),
        "checkpoint_iterations": ",".join(p.name.replace("iteration_", "") for p in iterations) or "NA",
        "has_light_mlp": any((p / "light_mlp.pt").exists() for p in iterations),
        "has_dir_encoding": any((p / "dir_encoding.pt").exists() for p in iterations),
        "has_point_cloud": any((p / "point_cloud.ply").exists() for p in iterations),
        "log_count": len(logs),
        "eval_split": "NA",
        "eval_iter": "NA",
        "l1": "NA",
        "psnr": "NA",
    }
    for log in path.rglob("*.log"):
        try:
            text = log.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in EVAL_RE.finditer(text):
            rows.append({**row, "eval_iter": match.group(1), "eval_split": match.group(2), "l1": match.group(3), "psnr": match.group(4)})
    return rows or [row]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", default=["output/ref_gs_limitation", "/tmp/ref_gs_limitation_sanity"])
    parser.add_argument("--out", default="experiments/ref_gs_limitation_analysis/metrics_summary.csv")
    args = parser.parse_args()

    all_rows = []
    for root in [Path(p) for p in args.roots]:
        if not root.exists():
            all_rows.append({
                "model_path": str(root),
                "has_cfg_args": False,
                "checkpoint_iterations": "NA",
                "has_light_mlp": False,
                "has_dir_encoding": False,
                "has_point_cloud": False,
                "log_count": 0,
                "eval_split": "NA",
                "eval_iter": "NA",
                "l1": "NA",
                "psnr": "NA",
            })
            continue
        candidates = [root] if (root / "cfg_args").exists() else [p for p in root.rglob("*") if p.is_dir() and (p / "cfg_args").exists()]
        if not candidates:
            candidates = [root]
        for candidate in candidates:
            all_rows.extend(collect_model(candidate))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(all_rows[0].keys())
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(json.dumps({"rows": len(all_rows), "out": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
