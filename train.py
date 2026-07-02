import csv
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "2"
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

import sys
import uuid
import torch
import numpy as np
from tqdm import tqdm

from random import randint
from scene import Scene, GaussianModel
from utils.loss_utils import (
    branch_separation_loss,
    highlight_leakage_loss,
    l1_loss,
    material_consistency_loss,
    specular_sparsity_loss,
    ssim,
    transport_consistency_loss,
    binary_cross_entropy,
)
from utils.general_utils import safe_state
from gaussian_renderer import *

from utils.image_utils import psnr
from argparse import ArgumentParser, Namespace
from arguments import ModelParams, PipelineParams, OptimizationParams

try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_FOUND = True
except ImportError:
    TENSORBOARD_FOUND = False


def get_srd_training_stage(dataset, iteration):
    if not getattr(dataset, "enable_srd_gs", False):
        return "baseline"

    manual_stage = int(getattr(dataset, "srd_stage", 0))
    if manual_stage == 1:
        return "stage_a"
    if manual_stage == 2:
        return "stage_b"
    if manual_stage == 3:
        return "stage_c"

    warmup = max(1, int(getattr(dataset, "srd_reflection_warmup", 3000)))
    if iteration <= warmup:
        return "stage_a"
    if iteration <= 2 * warmup:
        return "stage_b"
    return "stage_c"


def should_apply_srd_losses(dataset, iteration):
    return get_srd_training_stage(dataset, iteration) in ("stage_b", "stage_c")


def _zero_like_loss(reference):
    return reference.sum() * 0.0


SRD_LOSS_LOG_FIELDS = [
    "iteration",
    "stage",
    "total_loss",
    "loss_photo",
    "loss_geo",
    "loss_sep",
    "loss_ref",
    "loss_mat",
    "loss_tex",
    "loss_sparsity",
    "specular_energy",
    "branch_gate_mean",
    "surface_alpha_mean",
    "gaussian_count",
]


def _scalar_value(value):
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "item"):
        value = value.item()
    return float(value)


def build_srd_loss_log_row(
    iteration,
    stage,
    total_loss,
    loss_photo,
    loss_geo,
    loss_sep,
    loss_ref,
    loss_mat,
    loss_tex,
    loss_sparsity,
    specular_energy,
    branch_gate_mean,
    surface_alpha_mean,
    gaussian_count,
):
    return {
        "iteration": int(iteration),
        "stage": stage,
        "total_loss": _scalar_value(total_loss),
        "loss_photo": _scalar_value(loss_photo),
        "loss_geo": _scalar_value(loss_geo),
        "loss_sep": _scalar_value(loss_sep),
        "loss_ref": _scalar_value(loss_ref),
        "loss_mat": _scalar_value(loss_mat),
        "loss_tex": _scalar_value(loss_tex),
        "loss_sparsity": _scalar_value(loss_sparsity),
        "specular_energy": _scalar_value(specular_energy),
        "branch_gate_mean": _scalar_value(branch_gate_mean),
        "surface_alpha_mean": _scalar_value(surface_alpha_mean),
        "gaussian_count": int(gaussian_count),
    }


def append_srd_loss_log_row(path, row):
    if not path:
        return
    path = os.fspath(path)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    needs_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SRD_LOSS_LOG_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in SRD_LOSS_LOG_FIELDS})


def training(dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint):
    first_iter = 0
    tb_writer = prepare_output_and_logger(dataset)
    srd_loss_log_path = getattr(dataset, "srd_loss_log_path", "")
    gaussians = GaussianModel(dataset.sh_degree, dataset)
    
    scene = Scene(dataset, gaussians, resolution_scales=[1.0])
    
    gaussians.training_setup(opt)
    
    if checkpoint:
        (model_params, first_iter) = torch.load(checkpoint)
        gaussians.restore(model_params, opt)

    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    iter_start = torch.cuda.Event(enable_timing = True)
    iter_end = torch.cuda.Event(enable_timing = True)
    
    ###########################################################################
    viewpoint_stack = scene.getTrainCameras(scale=1.0).copy()
    print('Training set length', len(viewpoint_stack))
        
    ema_loss_for_log = 0.0
    ema_dist_for_log = 0.0
    ema_normal_for_log = 0.0
    ema_srd_for_log = {
        "loss_sep": 0.0,
        "loss_ref": 0.0,
        "loss_mat": 0.0,
        "loss_tex": 0.0,
    }

    progress_bar = tqdm(range(first_iter, opt.iterations), desc="Training progress")
    first_iter += 1
    for iteration in range(first_iter, opt.iterations + 1):        

        iter_start.record()

        gaussians.update_learning_rate(iteration)

        if iteration % 1000 == 0:
            gaussians.oneupSHdegree()

        data_idx = np.random.randint(len(viewpoint_stack))
        
        viewpoint_cam = viewpoint_stack[data_idx]
        
        bg = torch.rand((3), device="cuda")
        
        render_pkg = render(viewpoint_cam, gaussians, pipe, bg, iteration=iteration)
        
        viewspace_point_tensor = render_pkg["viewspace_points"]
        visibility_filter = render_pkg["visibility_filter"]
        radii = render_pkg["radii"]
        
        gt_image = viewpoint_cam.original_image.cuda()
        gt_image = gt_image[:3,...] * gt_image[3:,...] + (1-gt_image[3:,...]) * bg[:, None, None]
            
        loss = 0.0
        
        pbr_rgb = render_pkg["pbr_rgb"] * render_pkg["rend_alpha"] + (1-render_pkg["rend_alpha"]) * bg[:, None, None]
        Ll1 = l1_loss(pbr_rgb, gt_image)
        loss_pbr = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim(pbr_rgb, gt_image))
        loss += loss_pbr

        if iteration < 3000:
            gt_mask = viewpoint_cam.original_image.cuda()[3:,...]
            alpha_loss = binary_cross_entropy(render_pkg["rend_alpha"], gt_mask)
            loss += alpha_loss

        # regularization
        lambda_normal = 0.05 if iteration > 0 else 0.0
        lambda_dist = 0.0 if iteration > 0 else 0.0
        
        rend_dist = render_pkg["rend_dist"]
        rend_normal  = render_pkg['rend_normal']
        surf_normal = render_pkg['surf_normal']
        normal_error = (1 - (rend_normal * surf_normal).sum(dim=0))[None]
        normal_loss = lambda_normal * (normal_error).mean()
        dist_loss = lambda_dist * (rend_dist).mean()
        loss = loss + dist_loss + normal_loss

        srd_stage = get_srd_training_stage(dataset, iteration)
        loss_photo = loss_pbr
        loss_geo = normal_loss + dist_loss
        loss_sep = _zero_like_loss(loss_pbr)
        loss_ref = _zero_like_loss(loss_pbr)
        loss_mat = _zero_like_loss(loss_pbr)
        loss_tex = _zero_like_loss(loss_pbr)
        loss_sparsity = _zero_like_loss(loss_pbr)
        specular_energy = _zero_like_loss(loss_pbr)
        branch_gate_mean = _zero_like_loss(loss_pbr)
        surface_alpha_mean = render_pkg["rend_alpha"].mean()

        if should_apply_srd_losses(dataset, iteration):
            alpha_conf = render_pkg["rend_alpha"].detach()
            loss_sep = branch_separation_loss(
                render_pkg["branch_gate_map"],
                render_pkg["specular_weight_map"],
                alpha_conf,
            ) * getattr(opt, "lambda_srd_sep", 0.02)
            loss_ref = transport_consistency_loss(
                render_pkg["transport_feature_map"],
                confidence=alpha_conf,
            ) * getattr(opt, "lambda_srd_ref", 0.01)
            loss_mat = material_consistency_loss(
                render_pkg["surface_rgb"],
                render_pkg["diffuse_rgb"].detach(),
                alpha_conf,
            ) * getattr(opt, "lambda_srd_mat", 0.01)
            loss_sparsity = specular_sparsity_loss(
                render_pkg["specular_rgb"],
                alpha_conf,
            ) * getattr(opt, "lambda_srd_sparsity", 0.005)
            if srd_stage == "stage_c":
                loss_tex = highlight_leakage_loss(
                    render_pkg["diffuse_rgb"],
                    render_pkg["specular_rgb"].detach(),
                    render_pkg["branch_gate_map"].detach(),
                    alpha_conf,
                ) * getattr(opt, "lambda_srd_tex", 0.01)

            loss = loss + loss_sep + loss_ref + loss_mat + loss_tex + loss_sparsity
            specular_energy = render_pkg["specular_rgb"].abs().mean()
            branch_gate_mean = render_pkg["branch_gate_map"].mean()
        
        # loss
        total_loss = loss
        total_loss.backward()
        iter_end.record()
        
        with torch.no_grad():
            # Progress bar
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            ema_dist_for_log = 0.4 * dist_loss.item() + 0.6 * ema_dist_for_log
            ema_normal_for_log = 0.4 * normal_loss.item() + 0.6 * ema_normal_for_log
            ema_srd_for_log["loss_sep"] = 0.4 * loss_sep.item() + 0.6 * ema_srd_for_log["loss_sep"]
            ema_srd_for_log["loss_ref"] = 0.4 * loss_ref.item() + 0.6 * ema_srd_for_log["loss_ref"]
            ema_srd_for_log["loss_mat"] = 0.4 * loss_mat.item() + 0.6 * ema_srd_for_log["loss_mat"]
            ema_srd_for_log["loss_tex"] = 0.4 * loss_tex.item() + 0.6 * ema_srd_for_log["loss_tex"]

            if tb_writer:
                tb_writer.add_scalar("train/loss_photo", loss_photo.item(), iteration)
                tb_writer.add_scalar("train/loss_geo", loss_geo.item(), iteration)
                tb_writer.add_scalar("train/loss_sep", loss_sep.item(), iteration)
                tb_writer.add_scalar("train/loss_ref", loss_ref.item(), iteration)
                tb_writer.add_scalar("train/loss_mat", loss_mat.item(), iteration)
                tb_writer.add_scalar("train/loss_tex", loss_tex.item(), iteration)
                tb_writer.add_scalar("train/specular_energy", specular_energy.item(), iteration)
                tb_writer.add_scalar("train/branch_gate_mean", branch_gate_mean.item(), iteration)
                tb_writer.add_scalar("train/surface_alpha_mean", surface_alpha_mean.item(), iteration)

            if srd_loss_log_path and (iteration % 10 == 0 or iteration == opt.iterations):
                append_srd_loss_log_row(
                    srd_loss_log_path,
                    build_srd_loss_log_row(
                        iteration=iteration,
                        stage=srd_stage,
                        total_loss=total_loss,
                        loss_photo=loss_photo,
                        loss_geo=loss_geo,
                        loss_sep=loss_sep,
                        loss_ref=loss_ref,
                        loss_mat=loss_mat,
                        loss_tex=loss_tex,
                        loss_sparsity=loss_sparsity,
                        specular_energy=specular_energy,
                        branch_gate_mean=branch_gate_mean,
                        surface_alpha_mean=surface_alpha_mean,
                        gaussian_count=len(gaussians.get_xyz),
                    ),
                )

            if iteration % 10 == 0:
                loss_dict = {
                    "Loss": f"{ema_loss_for_log:.{5}f}",
                    "distort": f"{ema_dist_for_log:.{5}f}",
                    "normal": f"{ema_normal_for_log:.{5}f}",
                    "srd": srd_stage,
                    "sep": f"{ema_srd_for_log['loss_sep']:.{5}f}",
                    "ref": f"{ema_srd_for_log['loss_ref']:.{5}f}",
                    "mat": f"{ema_srd_for_log['loss_mat']:.{5}f}",
                    "tex": f"{ema_srd_for_log['loss_tex']:.{5}f}",
                    "Points": f"{len(gaussians.get_xyz)}"
                }
                progress_bar.set_postfix(loss_dict)

                progress_bar.update(10)
            if iteration == opt.iterations:
                progress_bar.close()

            if (iteration in saving_iterations):
                print("\n[ITER {}] Saving Gaussians".format(iteration))
                scene.save(iteration)

            # Densification
            if iteration < opt.densify_until_iter:
                gaussians.max_radii2D[visibility_filter] = torch.max(gaussians.max_radii2D[visibility_filter], radii[visibility_filter])
                gaussians.add_densification_stats(viewspace_point_tensor, visibility_filter)

                if iteration > opt.densify_from_iter and iteration % opt.densification_interval == 0:
                    size_threshold = 20 if iteration > opt.opacity_reset_interval else None
                    gaussians.densify_and_prune(opt.densify_grad_threshold, opt.opacity_cull, scene.cameras_extent, size_threshold)
                
                if iteration % opt.opacity_reset_interval == 0 or (dataset.white_background and iteration == opt.densify_from_iter):
                    gaussians.reset_opacity()
                    
            # Optimizer step
            if iteration < opt.iterations:
                gaussians.optimizer.step()
                gaussians.optimizer.zero_grad(set_to_none = True)

            if (iteration in checkpoint_iterations):
                print("\n[ITER {}] Saving Checkpoint".format(iteration))
                torch.save((gaussians.capture(), iteration), scene.model_path + "/chkpnt" + str(iteration) + ".pth")

                
def prepare_output_and_logger(args):
    dataset_name = args.source_path.split('/')[-1]
    if not args.model_path:
        if os.getenv('OAR_JOB_ID'):
            unique_str=os.getenv('OAR_JOB_ID')
        else:
            unique_str = str(uuid.uuid4())

        args.model_path = os.path.join("./output/refnerf/", dataset_name)
        
    # Set up output folder
    print("Output folder: {}".format(args.model_path))
    os.makedirs(args.model_path, exist_ok = True)
    with open(os.path.join(args.model_path, "cfg_args"), 'w') as cfg_log_f:
        cfg_log_f.write(str(Namespace(**vars(args))))

    # Create Tensorboard writer
    tb_writer = None
    if TENSORBOARD_FOUND:
        tb_writer = SummaryWriter(args.model_path)
    else:
        print("Tensorboard not available: not logging progress")
    return tb_writer


@torch.no_grad()
def training_report(tb_writer, iteration, Ll1, loss, l1_loss, elapsed, testing_iterations, scene : Scene, renderFunc, renderArgs):
    # Report test and samples of training set
    if iteration in testing_iterations:
        torch.cuda.empty_cache()
        validation_configs = ({'name': 'test', 'cameras' : scene.getTestCameras()}, 
                              {'name': 'train', 'cameras' : [scene.getTrainCameras()[idx % len(scene.getTrainCameras())] for idx in range(5, 30, 5)]})

        for config in validation_configs:
            if config['cameras'] and len(config['cameras']) > 0:
                l1_test = 0.0
                psnr_test = 0.0
                for idx, viewpoint in enumerate(config['cameras']):
                    render_pkg = renderFunc(viewpoint, scene.gaussians, *renderArgs)
                    image = torch.clamp(render_pkg["render"], 0.0, 1.0)
                    gt_image = torch.clamp(viewpoint.original_image.to("cuda"), 0.0, 1.0)

                    l1_test += l1_loss(image, gt_image).mean().double()
                    psnr_test += psnr(image, gt_image).mean().double()

                psnr_test /= len(config['cameras'])
                l1_test /= len(config['cameras'])
                print("\n[ITER {}] Evaluating {}: L1 {} PSNR {}".format(iteration, config['name'], l1_test, psnr_test))
                
        torch.cuda.empty_cache()

if __name__ == "__main__":
    # Set up command line argument parser
    parser = ArgumentParser(description="Training script parameters")
    lp = ModelParams(parser)
    op = OptimizationParams(parser)
    pp = PipelineParams(parser)
    parser.add_argument('--ip', type=str, default="127.0.0.1")
    parser.add_argument('--port', type=int, default=6009)
    parser.add_argument('--detect_anomaly', action='store_true', default=False)
    parser.add_argument("--test_iterations", nargs="+", type=int, default=
                        [1_000, 5_000, 7_000, 10_000, 15_000, 20_000, 25_000, 30_000]
                       )
    parser.add_argument("--save_iterations", nargs="+", type=int, default=
                        [1_000, 5_000, 7_000, 10_000, 15_000, 20_000, 25_000, 30_000]
                       )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--checkpoint_iterations", nargs="+", type=int, default=[])
    parser.add_argument("--start_checkpoint", type=str, default = None)
    args = parser.parse_args(sys.argv[1:])
    args.save_iterations.append(args.iterations)
    
    print("Optimizing " + args.model_path)

    # Initialize system state (RNG)
    safe_state(args.quiet)

    torch.autograd.set_detect_anomaly(args.detect_anomaly)
    training(lp.extract(args), op.extract(args), pp.extract(args), args.test_iterations, args.save_iterations, args.checkpoint_iterations, args.start_checkpoint)

    # All done
    print("\nTraining complete.")
