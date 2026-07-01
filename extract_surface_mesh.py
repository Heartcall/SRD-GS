import os
from argparse import ArgumentParser

import open3d as o3d
import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import render
from scene import GaussianModel, Scene
from utils.mesh_utils import GaussianExtractor, post_process_mesh


def main():
    parser = ArgumentParser(description="Extract SRD-GS surface-only or ablation meshes")
    model_params = ModelParams(parser, sentinel=True)
    pipeline_params = PipelineParams(parser)
    parser.add_argument("--iteration", type=int, default=-1)
    parser.add_argument("--mesh_mode", choices=['surface', 'unified', 'all_branch'], default="surface")
    parser.add_argument("--voxel_size", type=float, default=0.004)
    parser.add_argument("--sdf_trunc", type=float, default=0.02)
    parser.add_argument("--depth_trunc", type=float, default=3.0)
    parser.add_argument("--output_path", type=str, default="")
    parser.add_argument("--post_process", action="store_true", default=False)
    parser.add_argument("--cluster_to_keep", type=int, default=1000)
    parser.add_argument("--export_diagnostics", action="store_true", default=False)
    parser.add_argument("--max_views", type=int, default=0)
    args = get_combined_args(parser)

    dataset = model_params.extract(args)
    pipe = pipeline_params.extract(args)
    if args.mesh_mode in ("surface", "all_branch"):
        dataset.enable_srd_gs = True

    gaussians = GaussianModel(dataset.sh_degree, dataset)
    scene = Scene(dataset, gaussians, load_iteration=args.iteration, shuffle=False)
    train_views = scene.getTrainCameras(scale=1.0)
    if args.max_views > 0:
        train_views = train_views[:args.max_views]
    if not train_views:
        raise RuntimeError("no training views available for mesh extraction")

    extractor = GaussianExtractor(
        gaussians,
        render,
        pipe,
        surface_only=args.mesh_mode == 'surface',
        mesh_mode=args.mesh_mode,
        render_iteration=scene.loaded_iter,
    )
    extractor.reconstruction(train_views)
    mesh = extractor.extract_mesh_bounded(
        voxel_size=args.voxel_size,
        sdf_trunc=args.sdf_trunc,
        depth_trunc=args.depth_trunc,
    )
    if args.post_process:
        mesh = post_process_mesh(mesh, cluster_to_keep=args.cluster_to_keep)

    output_path = args.output_path
    if not output_path:
        output_name = "mesh_{}_iter{}.ply".format(args.mesh_mode, scene.loaded_iter)
        output_path = os.path.join(scene.model_path, output_name)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    o3d.io.write_triangle_mesh(output_path, mesh)
    print("Wrote mesh:", output_path)

    if args.export_diagnostics:
        diag_dir = os.path.join(scene.model_path, "surface_mesh_diagnostics_{}".format(args.mesh_mode))
        extractor.export_image(diag_dir)
        print("Wrote diagnostics:", diag_dir)

    if len(mesh.vertices) == 0:
        raise RuntimeError("mesh extraction produced an empty mesh")


if __name__ == "__main__":
    torch.set_grad_enabled(False)
    main()
