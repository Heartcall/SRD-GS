import os
from argparse import ArgumentParser

import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import render
from scene import GaussianModel, Scene
from utils.texture_baking import bake_image_space_materials, create_baking_report, save_baking_outputs


@torch.no_grad()
def collect_render_packages(views, gaussians, pipe, bg_color, render_iteration=0):
    render_packages = []
    for view in views:
        render_pkg = render(view, gaussians, pipe, bg_color, iteration=render_iteration)
        render_packages.append(render_pkg)
    return render_packages


def main():
    parser = ArgumentParser(description="Export SRD-GS specular-free image-space PBR material maps")
    model_params = ModelParams(parser, sentinel=True)
    pipeline_params = PipelineParams(parser)
    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--split", choices=["train", "test"], default="train")
    parser.add_argument("--mode", choices=["specular_free", "direct_rgb"], default="specular_free")
    parser.add_argument("--output_dir", type=str, default="")
    parser.add_argument("--max_views", type=int, default=0)
    args = get_combined_args(parser)

    dataset = model_params.extract(args)
    pipe = pipeline_params.extract(args)
    dataset.enable_srd_gs = True

    gaussians = GaussianModel(dataset.sh_degree, dataset)
    scene = Scene(dataset, gaussians, load_iteration=args.iteration, shuffle=False)
    views = scene.getTrainCameras(scale=1.0) if args.split == "train" else scene.getTestCameras(scale=1.0)
    if args.max_views > 0:
        views = views[:args.max_views]
    if not views:
        raise RuntimeError("no cameras available for {} split".format(args.split))

    background = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    render_packages = collect_render_packages(views, gaussians, pipe, background, render_iteration=scene.loaded_iter)
    outputs = bake_image_space_materials(render_packages, mode=args.mode)

    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join(scene.model_path, "pbr_textures_{}_iter{}".format(args.mode, scene.loaded_iter))
    paths = save_baking_outputs(outputs, output_dir)
    report = create_baking_report(outputs, paths, mode=args.mode)
    print("Wrote SRD-GS material maps:", output_dir)
    print("Highlight leakage score:", report["highlight_leakage_score"])


if __name__ == "__main__":
    torch.set_grad_enabled(False)
    main()
