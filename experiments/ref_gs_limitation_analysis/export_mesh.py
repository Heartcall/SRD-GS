#!/usr/bin/env python3
"""Export a predicted mesh from a Ref-GS checkpoint via GaussianExtractor."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from export_pbr_views import default_pipe_args, load_scene_and_model, resolve_render_func


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_path", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--iteration", type=int, default=None)
    parser.add_argument("--split", choices=["train", "test", "all"], default="test")
    parser.add_argument("--depth_ratio", type=float, default=1.0)
    parser.add_argument("--voxel_size", type=float, default=0.004)
    parser.add_argument("--sdf_trunc", type=float, default=0.02)
    parser.add_argument("--depth_trunc", type=float, default=None)
    parser.add_argument("--max_views", type=int, default=3)
    parser.add_argument("--out_mesh", required=True)
    parser.add_argument("--out_points", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--render_func", choices=["ref", "real", "nerf", "auto"], default="auto")
    parser.add_argument("--images", default="images")
    parser.add_argument("--resolution", "-r", type=int, default=-1)
    parser.add_argument("--white_background", action="store_true")
    parser.add_argument("--sh_degree", type=int, default=3)
    parser.add_argument("--run_dim", type=int, default=256)
    parser.add_argument("--albedo_bias", type=float, default=0.0)
    parser.add_argument("--gsrgb_loss", action="store_true")
    parser.add_argument("--rand_init", action="store_true")
    parser.add_argument("--init_until_iter", type=int, default=0)
    parser.add_argument("--env_scope_center", nargs=3, type=float, default=[0.0, 0.0, 0.0])
    parser.add_argument("--env_scope_radius", type=float, default=0.0)
    parser.add_argument("--xyz_axis", nargs=3, type=float, default=[0.0, 1.0, 2.0])
    return parser


def get_cameras(scene, split, max_views):
    if split == "train":
        cameras = scene.getTrainCameras()
    elif split == "test":
        cameras = scene.getTestCameras()
    else:
        cameras = scene.getTrainCameras() + scene.getTestCameras()
    return cameras[: max(0, max_views)]


def make_render_wrapper(args):
    import torch
    from gaussian_renderer import render, render_nerf, render_real

    resolved = resolve_render_func(args)
    center = torch.tensor([float(v) for v in args.env_scope_center], dtype=torch.float32, device="cuda")
    xyz = [int(float(v)) for v in args.xyz_axis]

    def render_wrapper(viewpoint_camera, pc, pipe, bg_color):
        if resolved == "nerf":
            return render_nerf(viewpoint_camera, pc, pipe, bg_color, return_components=True)
        if resolved == "real":
            return render_real(
                viewpoint_camera,
                pc,
                pipe,
                bg_color,
                ITER=args.init_until_iter,
                ENV_CENTER=center,
                ENV_RADIUS=args.env_scope_radius,
                XYZ=xyz,
                return_components=True,
            )
        return render(viewpoint_camera, pc, pipe, bg_color, return_components=True)

    return render_wrapper, resolved


def write_points(path, gaussians):
    import numpy as np
    import open3d as o3d

    points = gaussians.get_xyz.detach().cpu().numpy()
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(points))
    path.parent.mkdir(parents=True, exist_ok=True)
    return bool(o3d.io.write_point_cloud(str(path), pcd))


def main():
    args = build_parser().parse_args()
    out_mesh = Path(args.out_mesh)
    manifest_path = out_mesh.parent / "mesh_manifest.json"
    manifest = {
        "source_path": args.source_path,
        "model_path": args.model_path,
        "checkpoint": args.checkpoint,
        "iteration": args.iteration,
        "split": args.split,
        "max_views": args.max_views,
        "depth_ratio": args.depth_ratio,
        "voxel_size": args.voxel_size,
        "sdf_trunc": args.sdf_trunc,
        "depth_trunc": args.depth_trunc,
        "out_mesh": str(out_mesh),
        "out_points": args.out_points,
        "render_func": args.render_func,
        "status": "NA",
        "reason": "",
        "dry_run": bool(args.dry_run),
        "checks": {
            "source_exists": Path(args.source_path).exists(),
            "model_path_exists": Path(args.model_path).exists(),
            "checkpoint_exists": Path(args.checkpoint).exists() if args.checkpoint else None,
        },
    }

    if args.dry_run:
        manifest["status"] = "dry_run"
        manifest["reason"] = "paths and parameters checked only"
        write_json(manifest_path, manifest)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    try:
        import open3d as o3d
        from utils.mesh_utils import GaussianExtractor, post_process_mesh

        args.return_components = True
        args.render_iteration = 1
        scene, gaussians, pipe = load_scene_and_model(args, manifest)
        pipe.depth_ratio = args.depth_ratio if pipe is not None else default_pipe_args(args).depth_ratio
        cameras = get_cameras(scene, args.split, args.max_views)
        if not cameras:
            raise RuntimeError(f"no cameras available for split={args.split}")
        render_wrapper, resolved = make_render_wrapper(args)
        manifest["resolved_render_func"] = resolved
        extractor = GaussianExtractor(
            gaussians,
            render_wrapper,
            pipe,
            bg_color=[1, 1, 1] if args.white_background else [0, 0, 0],
        )
        extractor.reconstruction(cameras)
        depth_trunc = args.depth_trunc if args.depth_trunc is not None else max(float(extractor.radius) * 2.0, 1e-6)
        mesh = extractor.extract_mesh_bounded(
            voxel_size=args.voxel_size,
            sdf_trunc=args.sdf_trunc,
            depth_trunc=depth_trunc,
            mask_backgrond=True,
        )
        mesh = post_process_mesh(mesh)
        out_mesh.parent.mkdir(parents=True, exist_ok=True)
        ok = bool(o3d.io.write_triangle_mesh(str(out_mesh), mesh))
        manifest["mesh_exists"] = out_mesh.exists()
        manifest["mesh_write_ok"] = ok
        manifest["num_vertices"] = int(len(mesh.vertices))
        manifest["num_triangles"] = int(len(mesh.triangles))
        manifest["depth_trunc_resolved"] = depth_trunc
        if args.out_points:
            points_path = Path(args.out_points)
            manifest["points_write_ok"] = write_points(points_path, gaussians)
            manifest["points_exists"] = points_path.exists()
        manifest["status"] = "ok" if ok else "NA"
        manifest["reason"] = "" if ok else "Open3D write_triangle_mesh returned false"
    except Exception as exc:
        manifest["status"] = "NA"
        manifest["reason"] = str(exc)
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if args.strict and manifest["status"] != "ok":
        return 1
    return 0 if manifest["status"] in {"ok", "NA"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
