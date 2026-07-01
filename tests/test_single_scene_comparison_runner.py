from pathlib import Path
import subprocess
import tempfile
import unittest


class SingleSceneComparisonRunnerTest(unittest.TestCase):
    def test_dry_run_writes_three_variant_commands_and_summary_command(self):
        script = Path("scripts/srd_gs/run_single_scene_comparison.sh")
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
                    "17",
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

            variants = ["refgs_baseline", "full_srd_gs", "full_srd_gs_branch_raster"]
            train_commands = {}
            for variant in variants:
                variant_dir = output_root / "results" / "ball" / variant
                train_commands[variant] = (variant_dir / "train_command.txt").read_text(encoding="utf-8")
                self.assertTrue((variant_dir / "eval_gt_mesh_command.txt").exists(), variant)

            summary_command = (output_root / "tables" / "collect_metric_summary_command.txt").read_text(
                encoding="utf-8"
            )

        self.assertIn("DRY_RUN=1", result.stdout)
        self.assertIn("--iterations 17", train_commands["refgs_baseline"])
        self.assertIn("--eval", train_commands["refgs_baseline"])
        self.assertNotIn("--enable_srd_gs", train_commands["refgs_baseline"])
        self.assertIn("--enable_srd_gs", train_commands["full_srd_gs"])
        self.assertIn("--srd_rasterize_branch_maps", train_commands["full_srd_gs_branch_raster"])
        self.assertIn("collect_results.py", summary_command)
        self.assertIn("ball_metric_summary.csv", summary_command)


if __name__ == "__main__":
    unittest.main()
