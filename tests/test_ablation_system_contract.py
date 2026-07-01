from pathlib import Path
import csv
import json
import subprocess
import tempfile
import unittest


class AblationSystemContractTest(unittest.TestCase):
    expected_configs = [
        "refgs_baseline.yaml",
        "full_srd_gs.yaml",
        "full_srd_gs_branch_raster.yaml",
        "full_srd_gs_branch_raster_gate_ramp.yaml",
        "full_srd_gs_branch_raster_render_gate_delay.yaml",
        "no_reflection_branch.yaml",
        "no_branch_separation.yaml",
        "no_geo_loss.yaml",
        "no_transport_consistency.yaml",
        "naive_specular_rgb_consistency.yaml",
        "no_texture_despecularization.yaml",
        "no_staged_training.yaml",
        "all_branch_mesh.yaml",
    ]

    required_fields = [
        "name:",
        "hypothesis:",
        "what_it_removes:",
        "expected_supporting_result:",
        "refuting_result:",
        "metrics_to_inspect_first:",
    ]

    def test_all_required_ablation_configs_exist_and_record_claim_contract(self):
        config_dir = Path("configs/srd_gs")
        for filename in self.expected_configs:
            with self.subTest(filename=filename):
                path = config_dir / filename
                self.assertTrue(path.exists(), filename)
                text = path.read_text(encoding="utf-8")
                for field in self.required_fields:
                    self.assertIn(field, text)

    def test_runners_default_to_dry_run_and_reference_train_export_eval_steps(self):
        run_one = Path("scripts/srd_gs/run_one_scene.sh")
        run_ablation = Path("scripts/srd_gs/run_ablation_one_scene.sh")
        run_branch_raster_smoke = Path("scripts/srd_gs/run_branch_raster_smoke_one_scene.sh")
        self.assertTrue(run_one.exists())
        self.assertTrue(run_ablation.exists())
        self.assertTrue(run_branch_raster_smoke.exists())
        one_text = run_one.read_text(encoding="utf-8")
        ablation_text = run_ablation.read_text(encoding="utf-8")
        branch_raster_text = run_branch_raster_smoke.read_text(encoding="utf-8")

        self.assertIn("DRY_RUN=1", one_text)
        self.assertIn("--execute", one_text)
        self.assertIn("train.py", one_text)
        self.assertIn("extract_surface_mesh.py", one_text)
        self.assertIn("export_pbr_textures.py", one_text)
        self.assertIn("eval_reflective_assets.py", one_text)
        self.assertIn("configs/srd_gs/*.yaml", ablation_text)
        self.assertIn("run_one_scene.sh", ablation_text)
        self.assertIn("DRY_RUN=1", branch_raster_text)
        self.assertIn("render_eval_pairs.py", branch_raster_text)
        self.assertIn("eval_reflective_assets.py", branch_raster_text)
        self.assertIn("--source_path", branch_raster_text)

    def test_collect_results_summarizes_metrics_json_to_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            metrics_path = root / "scene_a" / "variant_a" / "eval" / "metrics.json"
            metrics_path.parent.mkdir(parents=True)
            gt_metrics_path = root / "scene_b" / "variant_b" / "eval_with_gt_mesh" / "metrics.json"
            gt_metrics_path.parent.mkdir(parents=True)
            metrics_path.write_text(
                json.dumps(
                    {
                        "metrics": [
                            {
                                "category": "rendering",
                                "name": "psnr",
                                "value": 31.5,
                                "supports_hypothesis": "rendering_fidelity",
                                "higher_is_better": True,
                                "not_available_reason": None,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            gt_metrics_path.write_text(
                json.dumps(
                    {
                        "metrics": [
                            {
                                "category": "geometry",
                                "name": "chamfer_distance",
                                "value": 0.25,
                                "supports_hypothesis": "surface_geometry_quality",
                                "higher_is_better": False,
                                "not_available_reason": None,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output_csv = root / "summary.csv"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/collect_results.py",
                    "--results_root",
                    str(root),
                    "--output_csv",
                    str(output_csv),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            with output_csv.open("r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["scene"], "scene_a")
        self.assertEqual(rows[0]["variant"], "variant_a")
        self.assertEqual(rows[0]["name"], "psnr")
        self.assertEqual(rows[0]["value"], "31.5")
        self.assertEqual(rows[1]["scene"], "scene_b")
        self.assertEqual(rows[1]["variant"], "variant_b")
        self.assertEqual(rows[1]["name"], "chamfer_distance")


if __name__ == "__main__":
    unittest.main()
