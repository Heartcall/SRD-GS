#!/usr/bin/env python3
"""Check real-scene environment sphere coverage without training."""

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def load_point_cloud(source_path):
    from plyfile import PlyData
    from scene.colmap_loader import read_points3D_binary, read_points3D_text

    source = Path(source_path)
    candidates = [
        source / "points3d.ply",
        source / "points3D.ply",
        source / "sparse" / "0" / "points3D.ply",
    ]
    for path in candidates:
        if path.exists():
            ply = PlyData.read(str(path))
            vertices = ply["vertex"]
            return np.vstack([vertices["x"], vertices["y"], vertices["z"]]).T.astype(np.float64), str(path)
    bin_path = source / "sparse" / "0" / "points3D.bin"
    txt_path = source / "sparse" / "0" / "points3D.txt"
    if bin_path.exists():
        xyz, _, _ = read_points3D_binary(str(bin_path))
        return np.asarray(xyz, dtype=np.float64), str(bin_path)
    if txt_path.exists():
        xyz, _, _ = read_points3D_text(str(txt_path))
        return np.asarray(xyz, dtype=np.float64), str(txt_path)
    raise FileNotFoundError(f"no point cloud found under {source}")


def coverage(points, center, radius):
    dist = np.linalg.norm(points - center[None, :], axis=1)
    inside = dist <= radius
    return {
        "num_points": int(points.shape[0]),
        "inside_count": int(inside.sum()),
        "outside_count": int((~inside).sum()),
        "inside_fraction": float(inside.mean()) if points.shape[0] else 0.0,
        "mean_distance": float(dist.mean()) if points.shape[0] else "NA",
        "min_distance": float(dist.min()) if points.shape[0] else "NA",
        "max_distance": float(dist.max()) if points.shape[0] else "NA",
    }


def bbox_summary(points, center, radius):
    bmin = points.min(axis=0)
    bmax = points.max(axis=0)
    diag = float(np.linalg.norm(bmax - bmin))
    return {
        "bbox_min": bmin.tolist(),
        "bbox_max": bmax.tolist(),
        "bbox_center": ((bmin + bmax) * 0.5).tolist(),
        "bbox_diag": diag,
        "sphere_center": center.tolist(),
        "sphere_radius": float(radius),
        "radius_over_bbox_diag": float(radius / diag) if diag > 0 else "NA",
    }


def make_rows(points, center, radius, xyz_axis):
    rows = []
    radius_scales = [0.8, 1.0, 1.2]
    offset_mag = 0.1 * radius if radius > 0 else 0.1
    for scale in radius_scales:
        row = {"case": f"radius_scale_{scale}", "axis_perm": "base", "center_offset": "0,0,0", "radius": radius * scale}
        row.update(coverage(points, center, radius * scale))
        rows.append(row)
    for axis in range(3):
        for sign in (-1, 1):
            offset = np.zeros(3)
            offset[axis] = sign * offset_mag
            row = {
                "case": f"center_axis{axis}_{sign:+d}",
                "axis_perm": "base",
                "center_offset": ",".join(str(float(v)) for v in offset),
                "radius": radius,
            }
            row.update(coverage(points, center + offset, radius))
            rows.append(row)
    for perm in itertools.permutations([0, 1, 2]):
        perm_points = points[:, list(perm)]
        perm_center = center[list(perm)]
        row = {
            "case": "axis_permutation",
            "axis_perm": ",".join(str(v) for v in perm),
            "center_offset": "0,0,0",
            "radius": radius,
        }
        row.update(coverage(perm_points, perm_center, radius))
        rows.append(row)
    base_perm = [int(float(v)) for v in xyz_axis]
    row = {
        "case": "requested_xyz_axis",
        "axis_perm": ",".join(str(v) for v in base_perm),
        "center_offset": "0,0,0",
        "radius": radius,
    }
    row.update(coverage(points[:, base_perm], center[base_perm], radius))
    rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_path", required=True)
    parser.add_argument("--center", nargs=3, type=float, required=True)
    parser.add_argument("--radius", type=float, required=True)
    parser.add_argument("--xyz_axis", nargs=3, type=float, default=[0, 1, 2])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    center = np.asarray(args.center, dtype=np.float64)
    payload = {
        "source_path": args.source_path,
        "center": center.tolist(),
        "radius": args.radius,
        "xyz_axis": args.xyz_axis,
        "status": "NA",
        "reason": "",
    }
    try:
        points, point_source = load_point_cloud(args.source_path)
        rows = make_rows(points, center, args.radius, args.xyz_axis)
        payload.update(
            {
                "status": "ok",
                "point_source": point_source,
                "bbox": bbox_summary(points, center, args.radius),
                "base_coverage": coverage(points, center, args.radius),
                "num_cases": len(rows),
            }
        )
        with (out / "coverage_table.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        lines = [
            "# Environment Sphere Coverage",
            "",
            f"Status: `{payload['status']}`",
            f"Point source: `{point_source}`",
            f"Points: {payload['base_coverage']['num_points']}",
            f"Base inside fraction: {payload['base_coverage']['inside_fraction']}",
            f"Radius / bbox diag: {payload['bbox']['radius_over_bbox_diag']}",
            "",
            "See `coverage_table.csv` for perturbation cases.",
        ]
    except Exception as exc:
        payload["reason"] = str(exc)
        lines = ["# Environment Sphere Coverage", "", "Status: `NA`", "", f"Reason: {exc}"]
    (out / "coverage_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (out / "coverage_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
