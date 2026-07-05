#!/usr/bin/env python3
"""Generate a dry-run Ref-GS limitation experiment matrix."""

import argparse
import csv
import json
from pathlib import Path


def load_inventory(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def has_scene(inv, rel):
    if not inv:
        return False
    return any(scene["relative_path"] == rel for scene in inv["scenes"])


def first_scene(inv, contains, fallback):
    if inv:
        for scene in inv["scenes"]:
            if contains in scene["relative_path"] and scene["stock_loader_compatible"]:
                return scene["relative_path"]
    return fallback


def build_matrix(inv):
    root = inv["root"] if inv else "/data/liuly/dataset/3DGS"
    ball = "Shiny Blender Synthetic/ball" if has_scene(inv, "Shiny Blender Synthetic/ball") else first_scene(inv, "Shiny Blender Synthetic", "Shiny Blender Synthetic/ball")
    toaster = "Shiny Blender Synthetic/toaster" if has_scene(inv, "Shiny Blender Synthetic/toaster") else ball
    glossy = first_scene(inv, "GlossySyntheticConverted/bell_blender", "GlossySyntheticConverted/bell_blender")
    garden = "Shiny Blender Real/gardenspheres" if has_scene(inv, "Shiny Blender Real/gardenspheres") else first_scene(inv, "Shiny Blender Real", "Shiny Blender Real/gardenspheres")
    nerf = "NeRF Synthetic/materials" if has_scene(inv, "NeRF Synthetic/materials") else first_scene(inv, "NeRF Synthetic", "NeRF Synthetic/materials")

    return [
        {
            "id": "E1",
            "limitation": "Evaluation/export gap for the main PBR output and component buffers",
            "dataset_scene": ball,
            "settings": "stock training checkpoint; render pbr_rgb/render/normal/depth/spec/diff via helper exporter (requires implementation)",
            "metrics": "PSNR/SSIM/LPIPS on pbr_rgb and SH render; component availability; normal MAE if GT normals are available",
            "dry_run": f"python train.py -s '{root}/{ball}' --eval --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e1_dry --help",
            "small_sanity": f"RUN_TRAIN=1 SANITY_SCENE='{root}/{ball}' bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh",
            "full_run": f"python train.py -s '{root}/{ball}' --eval --run_dim 256 --albedo_bias 0 --model_path output/ref_gs_limitation/e1_ball_full",
            "expected": "If stock reports miss pbr_rgb/component metrics, claims about reflection and components require an extra exporter before validation.",
        },
        {
            "id": "E2",
            "limitation": "Geometry recovery depends on self-derived deferred normals and TSDF extraction settings",
            "dataset_scene": toaster,
            "settings": "full model; depth_ratio in {0, 0.5, 1}; depth_trunc/voxel_size sweep for mesh extraction (export requires implementation)",
            "metrics": "normal MAE where GT normal exists; Chamfer/F-score to *_gt_mesh.ply; mesh completeness; PSNR/SSIM/LPIPS",
            "dry_run": f"python train.py -s '{root}/{toaster}' --eval --depth_ratio 0 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e2_dry --help",
            "small_sanity": f"python experiments/ref_gs_limitation_analysis/make_experiment_matrix.py --dry-run --inventory experiments/ref_gs_limitation_analysis/dataset_inventory.json",
            "full_run": f"python train.py -s '{root}/{toaster}' --eval --run_dim 256 --albedo_bias 0 --model_path output/ref_gs_limitation/e2_toaster_depth0",
            "expected": "If rendering remains stable but raw-coordinate mesh/normal metrics swing with depth settings, geometry recovery is less robust than NVS metrics suggest.",
        },
        {
            "id": "E3",
            "limitation": "Roughness-aware Sph-Mip behavior may be sensitive to material diversity and capacity",
            "dataset_scene": glossy,
            "settings": "run_dim in {64, 256}; roughness_lr in {0, 0.002}; rand_init on/off; no-mipmap ablation requires implementation",
            "metrics": "PSNR/SSIM/LPIPS; roughness-map variance; spec/diff leakage proxy from exported components; eval_pts mesh metric if exporter exists",
            "dry_run": f"python train-NeRO.py -s '{root}/{glossy}' --eval --run_dim 64 --albedo_bias 2 --albedo_lr 0.0005 --init_until_iter 2 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e3_dry --help",
            "small_sanity": f"RUN_TRAIN=1 SANITY_SCRIPT=train-NeRO.py SANITY_SCENE='{root}/{glossy}' SANITY_EXTRA='--albedo_bias 2 --albedo_lr 0.0005 --init_until_iter 1' bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh",
            "full_run": f"python train-NeRO.py -s '{root}/{glossy}' --eval --run_dim 256 --albedo_bias 2 --albedo_lr 0.0005 --init_until_iter 3000 --model_path output/ref_gs_limitation/e3_glossy_full",
            "expected": "If glossy scenes degrade sharply under reduced capacity or roughness freezing, the factorization is capacity/material dependent.",
        },
        {
            "id": "E4",
            "limitation": "Real-scene results depend on manually specified environment sphere, axis order, and warm-up schedule",
            "dataset_scene": garden,
            "settings": "train.sh default env_scope; center/radius perturbations; init_until_iter in {0, 700, 1500}",
            "metrics": "PSNR/SSIM/LPIPS; ref_w/out_w coverage; component artifacts; convergence stability",
            "dry_run": f"python train-real.py -s '{root}/{garden}' -r 6 --eval --run_dim 256 --albedo_bias 2 --albedo_lr 0.0005 --env_scope_center -0.2270 1.9700 1.7740 --env_scope_radius 0.974 --init_until_iter 1 --xyz_axis 2.0 1.0 0.0 --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e4_dry --help",
            "small_sanity": f"RUN_TRAIN=1 SANITY_SCRIPT=train-real.py SANITY_SCENE='{root}/{garden}' SANITY_EXTRA='-r 16 --albedo_bias 2 --albedo_lr 0.0005 --env_scope_center -0.2270 1.9700 1.7740 --env_scope_radius 0.974 --init_until_iter 1 --xyz_axis 2.0 1.0 0.0' bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh",
            "full_run": f"python train-real.py -s '{root}/{garden}' -r 6 --eval --run_dim 256 --albedo_bias 2 --albedo_lr 0.0005 --env_scope_center -0.2270 1.9700 1.7740 --env_scope_radius 0.974 --init_until_iter 700 --xyz_axis 2.0 1.0 0.0 --model_path output/ref_gs_limitation/e4_garden_default",
            "expected": "If small perturbations change ref_w/out_w coverage or NVS metrics substantially, real-scene performance is hand-configuration sensitive.",
        },
        {
            "id": "E5",
            "limitation": "General non-reflective scenes may pay overhead or quality tradeoffs for reflection modeling",
            "dataset_scene": nerf,
            "settings": "train-NeRF with gsrgb_loss on/off; run_dim {64, 256}; compare to external 2DGS/3DGS baseline if available",
            "metrics": "PSNR/SSIM/LPIPS; train time; point count; GPU memory; component leakage",
            "dry_run": f"python train-NeRF.py -s '{root}/{nerf}' --eval --run_dim 64 --albedo_bias 0 --gsrgb_loss --iterations 1 --save_iterations 1 --test_iterations 1 --model_path /tmp/ref_gs_e5_dry --help",
            "small_sanity": f"RUN_TRAIN=1 SANITY_SCRIPT=train-NeRF.py SANITY_SCENE='{root}/{nerf}' SANITY_EXTRA='--run_dim 64 --albedo_bias 0 --gsrgb_loss' bash experiments/ref_gs_limitation_analysis/run_small_sanity.sh",
            "full_run": f"python train-NeRF.py -s '{root}/{nerf}' --eval --run_dim 64 --albedo_bias 0 --gsrgb_loss --model_path output/ref_gs_limitation/e5_nerf_materials",
            "expected": "If reflection components add time/memory without NVS gains on non-reflective scenes, scope should be stated as reflective/material scenes.",
        },
    ]


def write_outputs(matrix, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "experiment_matrix.json"
    csv_path = out_dir / "experiment_matrix.csv"
    md_path = out_dir / "experiment_matrix.md"
    json_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix[0].keys()))
        writer.writeheader()
        writer.writerows(matrix)
    lines = [
        "| ID | Limitation | Dataset/Scene | Compared Settings | Metrics | Commands | Expected Evidence |",
        "| -- | ---------- | ------------- | ----------------- | ------- | -------- | ----------------- |",
    ]
    for row in matrix:
        cmd = f"dry-run: `{row['dry_run']}`<br>small: `{row['small_sanity']}`<br>full: `{row['full_run']}`"
        lines.append(
            f"| {row['id']} | {row['limitation']} | `{row['dataset_scene']}` | {row['settings']} | {row['metrics']} | {cmd} | {row['expected']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, csv_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="experiments/ref_gs_limitation_analysis/dataset_inventory.json")
    parser.add_argument("--out-dir", default="experiments/ref_gs_limitation_analysis")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    inv = load_inventory(Path(args.inventory))
    matrix = build_matrix(inv)
    paths = write_outputs(matrix, Path(args.out_dir))
    if args.dry_run:
        for row in matrix:
            print(f"[{row['id']}] {row['limitation']}")
            print(f"  scene: {row['dataset_scene']}")
            print(f"  dry-run: {row['dry_run']}")
            print(f"  small: {row['small_sanity']}")
            print(f"  full: {row['full_run']}")
    print("Wrote " + ", ".join(str(p) for p in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
