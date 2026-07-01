import json
import os
from argparse import ArgumentParser

import numpy as np
import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import get_srd_branch_map_policy, render
from scene import GaussianModel, Scene
from utils.metric_utils import estimate_reflective_mask, save_reflective_mask
from utils.render_utils import save_img_f32, save_img_u8


RENDER_EVAL_FIELDS = (
    "pred_rgb",
    "gt_rgb",
    "diffuse_rgb",
    "specular_rgb",
    "surface_depth",
    "surface_normal",
    "roughness_map",
    "branch_gate_map",
)


def build_empty_manifest(model_path, source_path, split, iteration, enable_srd_gs, branch_map_policy):
    return {
        "schema_version": 1,
        "model_path": model_path,
        "source_path": source_path,
        "split": split,
        "iteration": iteration,
        "enable_srd_gs": bool(enable_srd_gs),
        "branch_map_policy": branch_map_policy,
        "fields": {
            field: {
                "directory": field,
                "available": False,
                "not_available_reason": "not_rendered_yet",
            }
            for field in RENDER_EVAL_FIELDS
        },
        "reflective_mask": {
            "path": "reflective_mask.png",
            "source": None,
            "available": False,
            "not_available_reason": "not_rendered_yet",
        },
        "frames": [],
    }


def _ensure_dirs(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for field in RENDER_EVAL_FIELDS:
        os.makedirs(os.path.join(output_dir, field), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "reflective_mask"), exist_ok=True)


def _tensor_to_hwc(tensor, normal=False):
    if tensor is None:
        return None
    if hasattr(tensor, "detach"):
        tensor = tensor.detach().cpu().float().numpy()
    array = np.asarray(tensor, dtype=np.float32)
    if array.ndim == 3 and array.shape[0] in (1, 3, 4):
        array = np.transpose(array, (1, 2, 0))
    if array.ndim == 3 and array.shape[-1] == 4:
        array = array[..., :3]
    if normal:
        array = (array + 1.0) * 0.5
    return np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0)


def _save_frame(output_dir, field, index, array, float32=False):
    if array is None:
        return None
    ext = "tiff" if float32 else "png"
    path = os.path.join(output_dir, field, "{:05d}.{}".format(index, ext))
    if float32:
        save_img_f32(array, path)
    else:
        save_img_u8(array, path)
    return os.path.relpath(path, output_dir)


def _mark_available(manifest, field):
    manifest["fields"][field]["available"] = True
    manifest["fields"][field]["not_available_reason"] = None


def _mark_unavailable(manifest, field, reason):
    if not manifest["fields"][field]["available"]:
        manifest["fields"][field]["not_available_reason"] = reason


def _render_field_arrays(render_pkg, view):
    arrays = {
        "pred_rgb": _tensor_to_hwc(render_pkg.get("pbr_rgb")),
        "gt_rgb": _tensor_to_hwc(view.original_image[:3]),
        "diffuse_rgb": _tensor_to_hwc(render_pkg.get("diffuse_rgb")),
        "specular_rgb": _tensor_to_hwc(render_pkg.get("specular_rgb")),
        "surface_depth": _tensor_to_hwc(render_pkg.get("surface_depth", render_pkg.get("surf_depth"))),
        "surface_normal": _tensor_to_hwc(render_pkg.get("surface_normal", render_pkg.get("surf_normal")), normal=True),
        "roughness_map": _tensor_to_hwc(render_pkg.get("roughness_map")),
        "branch_gate_map": _tensor_to_hwc(render_pkg.get("branch_gate_map")),
    }
    return arrays


@torch.no_grad()
def render_eval_pairs(model_params, pipe, split, iteration, output_dir, max_views=0, auto_reflective_mask=True, mask_threshold=0.2):
    _ensure_dirs(output_dir)
    branch_policy = (
        get_srd_branch_map_policy(getattr(model_params, "srd_use_branch_gate", False))
        if getattr(model_params, "enable_srd_gs", False)
        else {"policy": "baseline_no_srd", "warning": None}
    )
    manifest = build_empty_manifest(
        model_path=model_params.model_path,
        source_path=model_params.source_path,
        split=split,
        iteration=iteration,
        enable_srd_gs=getattr(model_params, "enable_srd_gs", False),
        branch_map_policy=branch_policy,
    )

    gaussians = GaussianModel(model_params.sh_degree, model_params)
    scene = Scene(model_params, gaussians, load_iteration=iteration, shuffle=False)
    views = scene.getTrainCameras(scale=1.0) if split == "train" else scene.getTestCameras(scale=1.0)
    if max_views > 0:
        views = views[:max_views]
    if not views:
        raise RuntimeError("no cameras available for {} split".format(split))

    background = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    first_mask = None
    first_mask_path = None
    for index, view in enumerate(views):
        render_pkg = render(view, gaussians, pipe, background, iteration=iteration)
        rendered_branch_policy = render_pkg.get("srd_branch_map_policy")
        if rendered_branch_policy is not None:
            manifest["branch_map_policy"] = rendered_branch_policy
        arrays = _render_field_arrays(render_pkg, view)
        frame = {
            "index": index,
            "image_name": getattr(view, "image_name", "{:05d}".format(index)),
        }
        for field, array in arrays.items():
            if array is None:
                frame[field] = None
                _mark_unavailable(manifest, field, "field_not_returned_by_renderer")
                continue
            rel_path = _save_frame(output_dir, field, index, array, float32=field == "surface_depth")
            frame[field] = rel_path
            _mark_available(manifest, field)

        if auto_reflective_mask and arrays["pred_rgb"] is not None and arrays["gt_rgb"] is not None:
            mask = estimate_reflective_mask(arrays["pred_rgb"], arrays["gt_rgb"], threshold=mask_threshold)
            mask_path = os.path.join(output_dir, "reflective_mask", "{:05d}.png".format(index))
            save_reflective_mask(mask, mask_path)
            frame["reflective_mask"] = os.path.relpath(mask_path, output_dir)
            manifest["reflective_mask"]["available"] = True
            manifest["reflective_mask"]["source"] = "auto_residual_threshold"
            manifest["reflective_mask"]["not_available_reason"] = None
            if first_mask is None:
                first_mask = mask
                first_mask_path = os.path.join(output_dir, "reflective_mask.png")
                save_reflective_mask(first_mask, first_mask_path)
        else:
            frame["reflective_mask"] = None

        manifest["frames"].append(frame)

    if first_mask_path is not None:
        manifest["reflective_mask"]["path"] = os.path.relpath(first_mask_path, output_dir)
    elif not manifest["reflective_mask"]["available"]:
        manifest["reflective_mask"]["not_available_reason"] = "auto_mask_disabled_or_missing_pred_gt"

    manifest_path = os.path.join(output_dir, "render_eval_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return manifest


def main():
    parser = ArgumentParser(description="Render Ref-GS/SRD-GS eval RGB pairs and diagnostic buffers")
    model_params = ModelParams(parser, sentinel=True)
    pipeline_params = PipelineParams(parser)
    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--max_views", type=int, default=0)
    parser.add_argument("--auto_reflective_mask", action="store_true", default=False)
    parser.add_argument("--mask_threshold", type=float, default=0.2)
    args = get_combined_args(parser)

    dataset = model_params.extract(args)
    pipe = pipeline_params.extract(args)
    manifest = render_eval_pairs(
        dataset,
        pipe,
        split=args.split,
        iteration=args.iteration,
        output_dir=args.output_dir,
        max_views=args.max_views,
        auto_reflective_mask=args.auto_reflective_mask,
        mask_threshold=args.mask_threshold,
    )
    print("Wrote render eval manifest:", os.path.join(args.output_dir, "render_eval_manifest.json"))
    print("Rendered frames:", len(manifest["frames"]))


if __name__ == "__main__":
    torch.set_grad_enabled(False)
    main()
