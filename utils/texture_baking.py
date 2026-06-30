import json
import os

import imageio.v2 as imageio
import torch
import torch.nn.functional as F


def _to_chw_float(tensor, name):
    if tensor is None:
        raise KeyError("missing required baking buffer: {}".format(name))
    if not torch.is_tensor(tensor):
        tensor = torch.as_tensor(tensor)
    tensor = tensor.detach().float().cpu()
    if tensor.dim() == 2:
        tensor = tensor.unsqueeze(0)
    if tensor.dim() == 3 and tensor.shape[-1] in (1, 3) and tensor.shape[0] not in (1, 3):
        tensor = tensor.permute(2, 0, 1)
    if tensor.dim() != 3:
        raise ValueError("{} must be CHW, HWC, or HW tensor".format(name))
    return tensor


def _optional_chw(render_pkg, key, like, fill):
    value = render_pkg.get(key)
    if value is None:
        return torch.full_like(like, fill)
    return _to_chw_float(value, key)


def _save_u8(tensor, path):
    tensor = _to_chw_float(tensor, os.path.basename(path))
    array = tensor
    if array.shape[0] == 1:
        array = array[0]
    else:
        array = array.permute(1, 2, 0)
    array = torch.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0).clamp(0.0, 1.0)
    image = (array.numpy() * 255.0 + 0.5).astype("uint8")
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    imageio.imwrite(path, image)


def compute_baking_weights(
    alpha,
    normal,
    viewdir=None,
    specular_rgb=None,
    branch_gate_map=None,
    visibility_confidence=None,
    reprojection_confidence=None,
    eps=1e-6,
):
    """
    Compute per-pixel image-space baking weights.

    The weight combines visibility confidence, alpha confidence, view-angle
    confidence, specular residual downweight, branch-gate downweight, and
    optional reprojection confidence. This is a minimal image-space proxy;
    vertex/UV correspondence still needs runtime validation on real assets.
    """
    alpha = _to_chw_float(alpha, "alpha").clamp(0.0, 1.0)
    normal = F.normalize(_to_chw_float(normal, "normal"), dim=0, eps=eps)

    if viewdir is None:
        viewdir = torch.zeros_like(normal)
        viewdir[2:3] = 1.0
    viewdir = F.normalize(_to_chw_float(viewdir, "viewdir"), dim=0, eps=eps)
    view_weight = (normal * viewdir).sum(dim=0, keepdim=True).abs().clamp(0.0, 1.0)

    if specular_rgb is None:
        specular_energy = torch.zeros_like(alpha)
    else:
        specular_rgb = _to_chw_float(specular_rgb, "specular_rgb").clamp(0.0, 1.0)
        specular_energy = specular_rgb.max(dim=0, keepdim=True).values
    specular_downweight = (1.0 - specular_energy).clamp(0.0, 1.0)

    if branch_gate_map is None:
        branch_downweight = torch.ones_like(alpha)
    else:
        branch_gate_map = _to_chw_float(branch_gate_map, "branch_gate_map").clamp(0.0, 1.0)
        branch_downweight = (1.0 - branch_gate_map).clamp(0.0, 1.0)

    if visibility_confidence is None:
        visibility_confidence = torch.ones_like(alpha)
    else:
        visibility_confidence = _to_chw_float(visibility_confidence, "visibility_confidence").clamp(0.0, 1.0)

    if reprojection_confidence is None:
        reprojection_confidence = torch.ones_like(alpha)
    else:
        reprojection_confidence = _to_chw_float(reprojection_confidence, "reprojection_confidence").clamp(0.0, 1.0)

    weight = (
        alpha
        * visibility_confidence
        * view_weight
        * specular_downweight
        * branch_downweight
        * reprojection_confidence
    )
    return weight.clamp_min(0.0)


def _select_albedo(render_pkg, mode):
    if mode == "direct_rgb":
        if "pbr_rgb" in render_pkg:
            return _to_chw_float(render_pkg["pbr_rgb"], "pbr_rgb")
        return _to_chw_float(render_pkg.get("render"), "render")
    if "surface_rgb" in render_pkg:
        return _to_chw_float(render_pkg["surface_rgb"], "surface_rgb")
    if "diffuse_rgb" in render_pkg:
        return _to_chw_float(render_pkg["diffuse_rgb"], "diffuse_rgb")
    raise KeyError("specular_free baking requires surface_rgb or diffuse_rgb; final pbr_rgb is not allowed")


def bake_image_space_materials(render_packages, mode="specular_free"):
    """
    Bake minimal image-space material maps from SRD renderer outputs.

    `mode='specular_free'` uses surface/diffuse RGB for albedo. `mode='direct_rgb'`
    is the comparison baseline and uses final RGB. The function aggregates
    observations with physically motivated confidence weights, but does not
    construct a UV atlas.
    """
    if mode not in ("specular_free", "direct_rgb"):
        raise ValueError("mode must be specular_free or direct_rgb")
    if not render_packages:
        raise ValueError("render_packages must contain at least one render package")

    weighted = {}
    weight_sum = None
    leakage_accum = None

    for render_pkg in render_packages:
        albedo = _select_albedo(render_pkg, mode).clamp(0.0, 1.0)
        alpha = _to_chw_float(render_pkg.get("surface_alpha", render_pkg.get("rend_alpha")), "surface_alpha")
        normal = _to_chw_float(
            render_pkg.get("surface_normal", render_pkg.get("surf_normal", render_pkg.get("rend_normal"))),
            "surface_normal",
        )
        roughness = _to_chw_float(render_pkg.get("roughness_map"), "roughness_map").clamp(0.0, 1.0)
        specular = _optional_chw(render_pkg, "specular_rgb", albedo, 0.0).clamp(0.0, 1.0)
        branch_gate = _optional_chw(render_pkg, "branch_gate_map", alpha, 0.0).clamp(0.0, 1.0)
        specular_weight = _optional_chw(render_pkg, "specular_weight_map", alpha, 0.0).clamp(0.0, 1.0)
        viewdir = render_pkg.get("viewdir_map")

        weight = compute_baking_weights(
            alpha=alpha,
            normal=normal,
            viewdir=viewdir,
            specular_rgb=specular if mode == "specular_free" else None,
            branch_gate_map=branch_gate if mode == "specular_free" else None,
            visibility_confidence=render_pkg.get("visibility_confidence"),
            reprojection_confidence=render_pkg.get("reprojection_confidence"),
        )

        if weight_sum is None:
            weight_sum = torch.zeros_like(weight)
            weighted["albedo"] = torch.zeros_like(albedo)
            weighted["roughness"] = torch.zeros_like(roughness)
            weighted["normal"] = torch.zeros_like(normal)
            weighted["specular_weight"] = torch.zeros_like(specular_weight)
            leakage_accum = torch.zeros_like(weight)

        weighted["albedo"] += albedo * weight
        weighted["roughness"] += roughness * weight
        weighted["normal"] += normal * weight
        weighted["specular_weight"] += specular_weight * weight
        leakage_accum += specular.max(dim=0, keepdim=True).values * branch_gate * alpha
        weight_sum += weight

    denom = weight_sum.clamp_min(1e-6)
    albedo = weighted["albedo"] / denom
    roughness = weighted["roughness"] / denom
    normal = F.normalize(weighted["normal"] / denom, dim=0, eps=1e-6)
    specular_weight = weighted["specular_weight"] / denom
    highlight_leakage_mask = (leakage_accum / float(len(render_packages))).clamp(0.0, 1.0)

    return {
        "albedo": albedo.clamp(0.0, 1.0),
        "roughness": roughness.clamp(0.0, 1.0),
        "normal": (normal * 0.5 + 0.5).clamp(0.0, 1.0),
        "specular_weight": specular_weight.clamp(0.0, 1.0),
        "highlight_leakage_mask": highlight_leakage_mask,
        "weight_sum": weight_sum,
        "observation_count": len(render_packages),
        "mode": mode,
    }


def save_baking_outputs(outputs, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "albedo": os.path.join(output_dir, "albedo.png"),
        "roughness": os.path.join(output_dir, "roughness.png"),
        "normal": os.path.join(output_dir, "normal.png"),
        "specular_weight": os.path.join(output_dir, "specular_weight.png"),
        "highlight_leakage_mask": os.path.join(output_dir, "highlight_leakage_mask.png"),
        "report": os.path.join(output_dir, "baking_report.json"),
    }
    _save_u8(outputs["albedo"], paths["albedo"])
    _save_u8(outputs["roughness"], paths["roughness"])
    _save_u8(outputs["normal"], paths["normal"])
    _save_u8(outputs["specular_weight"], paths["specular_weight"])
    _save_u8(outputs["highlight_leakage_mask"], paths["highlight_leakage_mask"])
    return paths


def create_baking_report(outputs, paths, mode):
    leakage = outputs["highlight_leakage_mask"].detach().float()
    weight_sum = outputs["weight_sum"].detach().float()
    report = {
        "mode": mode,
        "output_type": "image_space_material_maps",
        "observation_count": int(outputs["observation_count"]),
        "highlight_leakage_score": float(leakage.mean().item()),
        "valid_weight_fraction": float((weight_sum > 1e-6).float().mean().item()),
        "outputs": {key: os.path.abspath(value) for key, value in paths.items() if key != "report"},
        "limitations": [
            "image-space baking only; UV atlas and mesh-vertex baking are not implemented in this milestone",
            "runtime quality needs verification on trained SRD-GS checkpoints",
        ],
    }
    report_path = paths["report"]
    directory = os.path.dirname(report_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report
