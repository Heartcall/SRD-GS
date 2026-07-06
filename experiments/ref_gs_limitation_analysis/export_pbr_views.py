#!/usr/bin/env python3
"""Export Ref-GS PBR/render/component buffers from a checkpoint.

The exporter is intentionally conservative: missing renderer keys are recorded
in the manifest instead of being fabricated.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DESIRED_KEYS = [
    "gt",
    "pbr_rgb",
    "render",
    "diffuse",
    "specular",
    "spec",
    "albedo",
    "roughness",
    "normal",
    "depth",
    "alpha",
    "ref_w",
    "out_w",
    "features",
]

RGB_LIKE_KEYS = {"gt", "pbr_rgb", "render", "diffuse", "specular", "spec", "albedo"}
VIS_KEYS = {"normal", "depth", "alpha", "roughness", "ref_w", "out_w"}
ALIASES = {
    "normal": ["rend_normal"],
    "depth": ["surf_depth"],
    "alpha": ["rend_alpha"],
    "specular": ["spec"],
}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def default_model_args(args):
    return SimpleNamespace(
        sh_degree=args.sh_degree,
        source_path=os.path.abspath(args.source_path),
        model_path=args.model_path,
        images=args.images,
        resolution=args.resolution,
        white_background=args.white_background,
        data_device="cuda",
        eval=True,
        run_dim=args.run_dim,
        albedo_bias=args.albedo_bias,
        gsrgb_loss=args.gsrgb_loss,
        rand_init=args.rand_init,
        init_until_iter=args.init_until_iter,
        env_scope_center=args.env_scope_center,
        env_scope_radius=args.env_scope_radius,
        alpha_weight=0.0,
        depth_tv_weight=0.0,
        density_weight=0.0,
        tv_weight=0.0,
        xyz_axis=args.xyz_axis,
    )


def default_opt_args():
    return SimpleNamespace(
        percent_dense=0.01,
        position_lr_init=0.00016,
        position_lr_final=0.0000016,
        position_lr_delay_mult=0.01,
        position_lr_max_steps=30000,
        feature_lr=0.002,
        opacity_lr=0.05,
        scaling_lr=0.005,
        rotation_lr=0.001,
        albedo_lr=0.001,
        mask_lr=0.002,
        roughness_lr=0.002,
        encoding_lr=0.002,
        mlp_lr=0.0005,
        lambda_dssim=0.2,
        lambda_dist=0.0,
        lambda_normal=0.05,
        opacity_cull=0.05,
        densification_interval=100,
        opacity_reset_interval=3000,
        densify_from_iter=500,
        densify_until_iter=15000,
        densify_grad_threshold=0.0002,
    )


def default_pipe_args(args):
    return SimpleNamespace(
        convert_SHs_python=False,
        compute_cov3D_python=False,
        depth_ratio=args.depth_ratio,
        debug=False,
    )


def tensor_to_chw(tensor):
    if tensor is None:
        return None
    tensor = tensor.detach().float().cpu()
    if tensor.ndim == 2:
        tensor = tensor.unsqueeze(0)
    if tensor.ndim == 3 and tensor.shape[0] not in (1, 3, 4):
        tensor = tensor.permute(2, 0, 1)
    return tensor


def tensor_stats(tensor):
    import torch

    cpu = tensor_to_chw(tensor)
    if cpu is None:
        return {}
    finite = cpu[torch.isfinite(cpu)]
    return {
        "shape": list(cpu.shape),
        "dtype": str(cpu.dtype),
        "min": float(finite.min()) if finite.numel() else "NA",
        "max": float(finite.max()) if finite.numel() else "NA",
    }


def tensor_to_image(tensor, kind):
    import torch

    image = tensor_to_chw(tensor)
    if image is None:
        return None
    if kind == "normal":
        image = (image[:3] + 1.0) * 0.5
    elif kind == "depth":
        valid = image[torch.isfinite(image)]
        if valid.numel() and float(valid.max()) > float(valid.min()):
            image = (image - valid.min()) / (valid.max() - valid.min())
        else:
            image = image * 0
    elif image.shape[0] == 1:
        image = image.repeat(3, 1, 1)
    elif image.shape[0] > 3:
        image = image[:3]
    image = torch.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0)
    return image.clamp(0.0, 1.0)


def save_tensor_png(path, tensor, kind="rgb"):
    import torchvision

    image = tensor_to_image(tensor, kind)
    if image is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    torchvision.utils.save_image(image, str(path))
    return True


def save_tensor_npz(path, key, tensor):
    import numpy as np

    arr = tensor_to_chw(tensor)
    if arr is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(path), **{key: arr.numpy()})
    return True


def load_scene_and_model(args, manifest):
    import torch
    from scene import Scene, GaussianModel

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available; Ref-GS model construction uses .cuda().")

    model_args = default_model_args(args)
    os.makedirs(model_args.model_path, exist_ok=True)

    load_iteration = args.iteration
    if load_iteration is None and not args.checkpoint:
        pc_root = Path(args.model_path) / "point_cloud"
        if pc_root.exists():
            candidates = []
            for child in pc_root.glob("iteration_*"):
                try:
                    candidates.append(int(child.name.replace("iteration_", "")))
                except ValueError:
                    pass
            if candidates:
                load_iteration = max(candidates)
    gaussians = GaussianModel(model_args.sh_degree, model_args)
    scene = Scene(model_args, gaussians, load_iteration=load_iteration, shuffle=False, resolution_scales=[1.0])

    if args.checkpoint:
        checkpoint = Path(args.checkpoint)
        if not checkpoint.exists():
            raise FileNotFoundError(f"checkpoint not found: {checkpoint}")
        opt_args = default_opt_args()
        gaussians.training_setup(opt_args)
        model_params, iteration = torch.load(str(checkpoint))
        gaussians.restore(model_params, opt_args)
        manifest["checkpoint_iteration"] = int(iteration)
    elif load_iteration is None:
        raise FileNotFoundError("No checkpoint or point_cloud/iteration_* found. Provide --checkpoint or --iteration.")
    else:
        manifest["checkpoint_iteration"] = int(load_iteration)
    return scene, gaussians, default_pipe_args(args)


def resolve_render_func(args):
    if args.render_func != "auto":
        return args.render_func
    name = Path(args.source_path).as_posix().lower()
    if "shiny blender real" in name:
        return "real"
    if "nerf synthetic" in name:
        return "nerf"
    return "ref"


def choose_renderer(args, gaussians, pipe, camera):
    import torch
    from gaussian_renderer import render, render_nerf, render_real

    bg = torch.tensor([1, 1, 1] if args.white_background else [0, 0, 0], dtype=torch.float32, device="cuda")
    render_func = resolve_render_func(args)
    common = {"iteration": args.render_iteration, "return_components": args.return_components}
    if render_func == "nerf":
        return render_nerf(camera, gaussians, pipe, bg, **common)
    if render_func == "real":
        center = torch.tensor([float(v) for v in args.env_scope_center], dtype=torch.float32, device="cuda")
        xyz = [int(float(v)) for v in args.xyz_axis]
        return render_real(
            camera,
            gaussians,
            pipe,
            bg,
            ITER=args.init_until_iter,
            ENV_CENTER=center,
            ENV_RADIUS=args.env_scope_radius,
            XYZ=xyz,
            **common,
        )
    return render(camera, gaussians, pipe, bg, **common)


def get_buffer(render_pkg, key):
    if key in render_pkg:
        return render_pkg.get(key), None
    for alias in ALIASES.get(key, []):
        if alias in render_pkg:
            return render_pkg.get(alias), alias
    return None, None


def save_buffer(view_dir, key, tensor, args):
    entry = {"exported": False, "missing": False}
    if tensor is None:
        entry.update({"missing": True, "reason": "not returned by renderer"})
        return entry, None
    entry.update(tensor_stats(tensor))
    paths = {}
    kind = "normal" if key == "normal" else "depth" if key == "depth" else "rgb"
    if args.save_png and (key in RGB_LIKE_KEYS or key in VIS_KEYS):
        png_path = view_dir / f"{key}.png"
        if save_tensor_png(png_path, tensor, kind):
            paths["png"] = str(png_path)
    if args.save_npz or key not in RGB_LIKE_KEYS | VIS_KEYS:
        npz_path = view_dir / f"{key}.npz"
        if save_tensor_npz(npz_path, key, tensor):
            paths["npz"] = str(npz_path)
    if paths:
        entry["exported"] = True
        entry["paths"] = paths
        entry["path"] = paths.get("png") or paths.get("npz")
    else:
        entry.update({"missing": True, "reason": "no supported save format selected"})
    return entry, entry.get("path")


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_path", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--iteration", type=int, default=None)
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--max_views", type=int, default=3)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--return_components", action="store_true")
    parser.add_argument("--render_func", choices=["ref", "real", "nerf", "auto"], default="ref")
    parser.add_argument("--save_npz", action="store_true")
    parser.add_argument("--save_png", action="store_true", default=True)
    parser.add_argument("--render_iteration", type=int, default=1)
    parser.add_argument("--images", default="images")
    parser.add_argument("--resolution", "-r", type=int, default=-1)
    parser.add_argument("--white_background", action="store_true")
    parser.add_argument("--sh_degree", type=int, default=3)
    parser.add_argument("--run_dim", type=int, default=256)
    parser.add_argument("--albedo_bias", type=float, default=0.0)
    parser.add_argument("--gsrgb_loss", action="store_true")
    parser.add_argument("--rand_init", action="store_true")
    parser.add_argument("--depth_ratio", type=float, default=0.0)
    parser.add_argument("--init_until_iter", type=int, default=0)
    parser.add_argument("--env_scope_center", nargs=3, type=float, default=[0.0, 0.0, 0.0])
    parser.add_argument("--env_scope_radius", type=float, default=0.0)
    parser.add_argument("--xyz_axis", nargs=3, type=float, default=[0.0, 1.0, 2.0])
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    manifest = {
        "source_path": args.source_path,
        "model_path": args.model_path,
        "checkpoint": args.checkpoint,
        "split": args.split,
        "max_views": args.max_views,
        "render_func": args.render_func,
        "resolved_render_func": resolve_render_func(args),
        "return_components": bool(args.return_components),
        "save_png": bool(args.save_png),
        "save_npz": bool(args.save_npz),
        "views": [],
        "exported_keys": [],
        "missing_keys": [],
        "errors": [],
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        checks = {
            "source_exists": Path(args.source_path).exists(),
            "model_path_exists": Path(args.model_path).exists(),
            "checkpoint_exists": Path(args.checkpoint).exists() if args.checkpoint else None,
        }
        manifest["checks"] = checks
        manifest["missing_keys"] = DESIRED_KEYS
        write_json(out_dir / "manifest.json", manifest)
        print(json.dumps(checks, indent=2, sort_keys=True))
        print(f"Wrote {out_dir / 'manifest.json'}")
        return 0

    try:
        import torch

        scene, gaussians, pipe = load_scene_and_model(args, manifest)
        cameras = scene.getTestCameras() if args.split == "test" else scene.getTrainCameras()
        cameras = cameras[: max(0, args.max_views)]
        exported_keys = set()
        missing_keys = set()
        with torch.no_grad():
            for index, camera in enumerate(cameras):
                view_name = f"{index:05d}_{camera.image_name}"
                view_dir = out_dir / "views" / view_name
                view = {
                    "index": index,
                    "image_name": camera.image_name,
                    "files": {},
                    "buffers": {},
                    "missing": [],
                    "errors": [],
                }
                try:
                    render_pkg = choose_renderer(args, gaussians, pipe, camera)
                    tensors = {"gt": camera.original_image[:3]}
                    for key in DESIRED_KEYS:
                        if key == "gt":
                            tensor, alias = tensors[key], None
                        else:
                            tensor, alias = get_buffer(render_pkg, key)
                        entry, path = save_buffer(view_dir, key, tensor, args)
                        if alias:
                            entry["alias"] = alias
                        view["buffers"][key] = entry
                        if path:
                            view["files"][key] = path
                            exported_keys.add(key)
                        else:
                            view["missing"].append(key)
                            missing_keys.add(key)
                    manifest["views"].append(view)
                except Exception as exc:
                    view["errors"].append(str(exc))
                    manifest["views"].append(view)
                    manifest["errors"].append(f"{view_name}: {exc}")
        manifest["num_views"] = len(cameras)
        manifest["exported_keys"] = sorted(exported_keys)
        manifest["missing_keys"] = sorted(missing_keys)
        write_json(out_dir / "manifest.json", manifest)
        print(f"Wrote {out_dir / 'manifest.json'}")
        return 1 if manifest["errors"] else 0
    except Exception as exc:
        manifest["errors"].append(str(exc))
        manifest["missing_keys"] = DESIRED_KEYS
        write_json(out_dir / "manifest.json", manifest)
        print(f"export failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
