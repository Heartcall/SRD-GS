from pathlib import Path
import subprocess
import tempfile
import unittest


class BranchRasterSmokeRunnerTest(unittest.TestCase):
    def test_dry_run_writes_eval_true_gt_mesh_metric_chain_commands(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        self.assertTrue(script.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            result = subprocess.run(
                [
                    "bash",
                    str(script),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "7",
                    "--max_mesh_views",
                    "3",
                    "--depth_trunc",
                    "9.5",
                    "--max_texture_views",
                    "2",
                    "--max_eval_views",
                    "2",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            mesh_command = (variant_dir / "mesh_command.txt").read_text(encoding="utf-8")
            texture_command = (variant_dir / "texture_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")
            eval_command = (variant_dir / "eval_gt_mesh_command.txt").read_text(encoding="utf-8")

        self.assertIn("DRY_RUN=1", result.stdout)
        self.assertIn("LD_LIBRARY_PATH", script.read_text(encoding="utf-8"))
        self.assertIn("train.py", train_command)
        self.assertIn("--eval", train_command)
        self.assertIn("--enable_srd_gs", train_command)
        self.assertIn("--srd_rasterize_branch_maps", train_command)
        self.assertIn("--srd_use_branch_gate", train_command)
        self.assertIn("--iterations 7", train_command)
        self.assertIn("extract_surface_mesh.py", mesh_command)
        self.assertIn("--mesh_mode surface", mesh_command)
        self.assertIn("--max_views 3", mesh_command)
        self.assertIn("--depth_trunc 9.5", mesh_command)
        self.assertIn("export_pbr_textures.py", texture_command)
        self.assertIn("--max_views 2", texture_command)
        self.assertIn("render_eval_pairs.py", render_command)
        self.assertIn("--split test", render_command)
        self.assertIn("--max_views 2", render_command)
        self.assertIn("--auto_reflective_mask", render_command)
        self.assertIn("--srd_rasterize_branch_maps", render_command)
        self.assertIn("eval_reflective_assets.py", eval_command)
        self.assertIn("--eval_pairs_dir", eval_command)
        self.assertIn("--source_path /tmp/srd_scene", eval_command)
        self.assertIn("--pred_geometry", eval_command)
        self.assertIn("--geometry_sample_count 1000", eval_command)

    def test_gate_ramp_config_writes_schedule_flags(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        config = Path("configs/srd_gs/full_srd_gs_branch_raster_gate_ramp.yaml")
        self.assertTrue(config.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            subprocess.run(
                [
                    "bash",
                    str(script),
                    "--config",
                    str(config),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "40",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster_gate_ramp"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")

        self.assertIn("--srd_branch_gate_start_iter 10", train_command)
        self.assertIn("--srd_branch_gate_ramp_iters 20", train_command)
        self.assertIn("--srd_branch_gate_start_iter 10", render_command)
        self.assertIn("--srd_branch_gate_ramp_iters 20", render_command)

    def test_render_gate_delay_config_writes_independent_render_gate_flags(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        config = Path("configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay.yaml")
        self.assertTrue(config.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            subprocess.run(
                [
                    "bash",
                    str(script),
                    "--config",
                    str(config),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "30",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster_render_gate_delay"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")

        self.assertIn("--srd_render_gate_start_iter 60", train_command)
        self.assertIn("--srd_render_gate_ramp_iters 0", train_command)
        self.assertIn("--srd_render_gate_start_iter 60", render_command)
        self.assertIn("--srd_render_gate_ramp_iters 0", render_command)

    def test_stagebc_render_gate_delay_config_writes_stage_and_gate_flags(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        config = Path("configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_stagebc.yaml")
        self.assertTrue(config.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            subprocess.run(
                [
                    "bash",
                    str(script),
                    "--config",
                    str(config),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "300",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster_render_gate_delay_stagebc"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")

        self.assertIn("--srd_reflection_warmup 100", train_command)
        self.assertIn("--srd_render_gate_start_iter 200", train_command)
        self.assertIn("--srd_render_gate_ramp_iters 100", train_command)
        self.assertIn("--srd_reflection_warmup 100", render_command)
        self.assertIn("--srd_render_gate_start_iter 200", render_command)
        self.assertIn("--srd_render_gate_ramp_iters 100", render_command)

    def test_i300_control_config_uses_same_gate_without_accelerated_stagebc(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        config = Path("configs/srd_gs/full_srd_gs_branch_raster_render_gate_delay_i300_control.yaml")
        self.assertTrue(config.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            subprocess.run(
                [
                    "bash",
                    str(script),
                    "--config",
                    str(config),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "300",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster_render_gate_delay_i300_control"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")

        self.assertNotIn("--srd_reflection_warmup 100", train_command)
        self.assertNotIn("--srd_stage 2", train_command)
        self.assertNotIn("--srd_stage 3", train_command)
        self.assertIn("--srd_render_gate_start_iter 200", train_command)
        self.assertIn("--srd_render_gate_ramp_iters 100", train_command)
        self.assertNotIn("--srd_reflection_warmup 100", render_command)
        self.assertIn("--srd_render_gate_start_iter 200", render_command)
        self.assertIn("--srd_render_gate_ramp_iters 100", render_command)

    def test_i300_neutral_render_gate_config_keeps_render_gate_off_past_checkpoint(self):
        script = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        config = Path("configs/srd_gs/full_srd_gs_branch_raster_render_gate_neutral_i300.yaml")
        self.assertTrue(config.exists())

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir)
            subprocess.run(
                [
                    "bash",
                    str(script),
                    "--config",
                    str(config),
                    "--scene_path",
                    "/tmp/srd_scene",
                    "--output_root",
                    str(output_root),
                    "--scene_name",
                    "ball",
                    "--iterations",
                    "300",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            variant_dir = output_root / "results" / "ball" / "full_srd_gs_branch_raster_render_gate_neutral_i300"
            train_command = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
            render_command = (variant_dir / "render_eval_pairs_command.txt").read_text(encoding="utf-8")

        self.assertIn("--srd_branch_gate_start_iter 10", train_command)
        self.assertIn("--srd_branch_gate_ramp_iters 20", train_command)
        self.assertIn("--srd_render_gate_start_iter 100000", train_command)
        self.assertIn("--srd_render_gate_ramp_iters 0", train_command)
        self.assertNotIn("--srd_reflection_warmup 100", train_command)
        self.assertIn("--srd_render_gate_start_iter 100000", render_command)
        self.assertIn("--srd_render_gate_ramp_iters 0", render_command)


if __name__ == "__main__":
    unittest.main()
