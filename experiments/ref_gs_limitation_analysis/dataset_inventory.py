#!/usr/bin/env python3
"""Inventory local 3DGS datasets without assuming one fixed layout."""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".JPG", ".PNG"}
MESH_EXTS = {".ply", ".obj", ".stl"}
MARKERS = {
    "depth": ("depth", "disp"),
    "normal": ("normal",),
    "roughness": ("rough",),
    "albedo": ("albedo", "diffuse"),
    "mask": ("mask", "alpha"),
}


def count_files(path: Path, exts: Iterable[str], recursive: bool = False) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    iterator = path.rglob("*") if recursive else path.iterdir()
    return sum(1 for p in iterator if p.is_file() and p.suffix in exts)


def safe_json_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        frames = data.get("frames", [])
        return len(frames) if isinstance(frames, list) else 0
    except Exception:
        return 0


def marker_counts(scene: Path) -> Dict[str, int]:
    counts = {key: 0 for key in MARKERS}
    for p in scene.rglob("*"):
        if not p.is_file():
            continue
        name = p.name.lower()
        for key, tokens in MARKERS.items():
            if any(token in name for token in tokens):
                counts[key] += 1
    return counts


def scene_layout(scene: Path) -> Dict:
    train_json = scene / "transforms_train.json"
    test_json = scene / "transforms_test.json"
    sparse0 = scene / "sparse" / "0"
    sparse = scene / "sparse"
    images_dir = scene / "images"
    train_dir = scene / "train"
    test_dir = scene / "test"
    mask_dir = scene / "mask"
    masks_dir = scene / "masks"
    files = list(scene.iterdir()) if scene.exists() and scene.is_dir() else []

    meshes = sorted(
        str(p.relative_to(scene))
        for p in scene.glob("*")
        if p.is_file() and p.suffix.lower() in MESH_EXTS
    )
    has_colmap = sparse.exists()
    has_blender = train_json.exists() or test_json.exists()
    image_count = (
        count_files(images_dir, IMAGE_EXTS)
        + count_files(train_dir, IMAGE_EXTS)
        + count_files(test_dir, IMAGE_EXTS)
        + sum(1 for p in files if p.is_file() and p.suffix in IMAGE_EXTS)
    )
    counts = marker_counts(scene)

    return {
        "path": str(scene),
        "relative_path": "",
        "layout": (
            "blender_transforms"
            if has_blender
            else "colmap_direct"
            if has_colmap
            else "image_or_auxiliary"
            if image_count or meshes
            else "unknown"
        ),
        "stock_loader_compatible": bool(has_blender or (sparse0.exists() and images_dir.exists())),
        "has_transforms_train": train_json.exists(),
        "has_transforms_test": test_json.exists(),
        "train_frame_count": safe_json_count(train_json),
        "test_frame_count": safe_json_count(test_json),
        "has_sparse": sparse.exists(),
        "has_sparse_0": sparse0.exists(),
        "has_cameras": any((sparse0 / name).exists() for name in ("cameras.bin", "cameras.txt")),
        "has_images_bin_or_txt": any((sparse0 / name).exists() for name in ("images.bin", "images.txt")),
        "has_points3d": any(
            (sparse0 / name).exists()
            for name in ("points3D.bin", "points3D.txt", "points3D.ply")
        )
        or (scene / "points3d.ply").exists()
        or (scene / "points3D.ply").exists(),
        "image_count": image_count,
        "images_dir_count": count_files(images_dir, IMAGE_EXTS),
        "train_dir_count": count_files(train_dir, IMAGE_EXTS),
        "test_dir_count": count_files(test_dir, IMAGE_EXTS),
        "has_mask_dir": mask_dir.exists() or masks_dir.exists(),
        "mask_count": count_files(mask_dir, IMAGE_EXTS) + count_files(masks_dir, IMAGE_EXTS) + counts["mask"],
        "depth_count": counts["depth"],
        "normal_count": counts["normal"],
        "roughness_count": counts["roughness"],
        "albedo_count": counts["albedo"],
        "mesh_files": meshes[:20],
        "mesh_count": len(meshes),
        "has_eval_pts": (scene / "eval_pts.ply").exists(),
        "size_mb": round(sum(p.stat().st_size for p in scene.rglob("*") if p.is_file()) / 1024 / 1024, 2),
    }


def find_scene_roots(root: Path) -> List[Path]:
    scenes = []
    for dirpath, dirnames, filenames in os.walk(root):
        path = Path(dirpath)
        names = set(filenames)
        child_dirs = set(dirnames)
        if {
            "transforms_train.json",
            "transforms_test.json",
        } & names or "sparse" in child_dirs or "images" in child_dirs or {"train", "test"} <= child_dirs:
            scenes.append(path)
            dirnames[:] = [d for d in dirnames if d not in {"images", "train", "test", "mask", "masks", "sparse"}]
    return sorted(set(scenes), key=lambda p: str(p).lower())


def summarize(scenes: List[Dict]) -> Dict:
    by_layout: Dict[str, int] = {}
    by_dataset: Dict[str, int] = {}
    for scene in scenes:
        by_layout[scene["layout"]] = by_layout.get(scene["layout"], 0) + 1
        rel = scene["relative_path"]
        dataset = rel.split(os.sep)[0] if rel else "."
        by_dataset[dataset] = by_dataset.get(dataset, 0) + 1
    sanity = [
        s
        for s in scenes
        if s["stock_loader_compatible"]
        and (s["train_frame_count"] or s["images_dir_count"] or s["train_dir_count"])
    ]
    sanity = sorted(
        sanity,
        key=lambda s: (
            0 if "Shiny Blender Synthetic/ball" in s["relative_path"] else 1,
            s["size_mb"],
            s["relative_path"],
        ),
    )
    return {
        "scene_count": len(scenes),
        "by_layout": by_layout,
        "by_dataset": by_dataset,
        "stock_loader_compatible_count": sum(1 for s in scenes if s["stock_loader_compatible"]),
        "with_mesh_or_eval_pts": sum(1 for s in scenes if s["mesh_count"] or s["has_eval_pts"]),
        "with_depth_like_files": sum(1 for s in scenes if s["depth_count"]),
        "small_sanity_candidates": [
            {
                "relative_path": s["relative_path"],
                "layout": s["layout"],
                "image_count": s["image_count"],
                "train_frames": s["train_frame_count"],
                "test_frames": s["test_frame_count"],
                "size_mb": s["size_mb"],
                "has_eval_pts": s["has_eval_pts"],
                "mesh_count": s["mesh_count"],
            }
            for s in sanity[:12]
        ],
    }


def write_markdown(out_json: Path, payload: Dict) -> None:
    md_path = out_json.with_suffix(".md")
    lines = [
        "# Ref-GS Dataset Inventory",
        "",
        f"Root: `{payload['root']}`",
        f"Scene candidates: {payload['summary']['scene_count']}",
        f"Stock-loader compatible: {payload['summary']['stock_loader_compatible_count']}",
        "",
        "## Layout Counts",
        "",
    ]
    for key, value in sorted(payload["summary"]["by_layout"].items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Dataset Counts", ""]
    for key, value in sorted(payload["summary"]["by_dataset"].items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Small Sanity Candidates", ""]
    for item in payload["summary"]["small_sanity_candidates"]:
        lines.append(
            "- `{relative_path}` ({layout}), images={image_count}, train={train_frames}, "
            "test={test_frames}, size_mb={size_mb}, eval_pts={has_eval_pts}, meshes={mesh_count}".format(
                **item
            )
        )
    lines += ["", "## Scenes", ""]
    for scene in payload["scenes"]:
        lines.append(
            "- `{relative_path}`: layout={layout}, compatible={stock_loader_compatible}, "
            "images={image_count}, train={train_frame_count}, test={test_frame_count}, "
            "sparse={has_sparse_0}, masks={mask_count}, depth={depth_count}, normal={normal_count}, "
            "meshes={mesh_count}, eval_pts={has_eval_pts}".format(**scene)
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/data/liuly/dataset/3DGS")
    parser.add_argument("--out", default="experiments/ref_gs_limitation_analysis/dataset_inventory.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out)
    if not root.exists():
        raise SystemExit(f"Dataset root not found: {root}")

    scenes = []
    for scene_root in find_scene_roots(root):
        item = scene_layout(scene_root)
        item["relative_path"] = str(scene_root.relative_to(root))
        scenes.append(item)

    payload = {"root": str(root), "summary": summarize(scenes), "scenes": scenes}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(out, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print(f"Wrote {out}")
    print(f"Wrote {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
