import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class EvalMaterialArtifactPlumbingTest(unittest.TestCase):
    def test_audit_classifies_missing_metrics_without_runtime_or_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result_root"
            eval_dir = result_root / "eval_with_gt_mesh"
            render_dir = result_root / "render_eval_pairs"
            texture_dir = result_root / "pbr_textures_specular_free"
            output_dir = tmp / "m35"

            eval_dir.mkdir(parents=True)
            render_dir.mkdir(parents=True)
            texture_dir.mkdir(parents=True)
            (texture_dir / "baking_report.json").write_text(
                json.dumps({"highlight_leakage_score": 0.001}),
                encoding="utf-8",
            )
            (texture_dir / "highlight_leakage_mask.png").write_bytes(b"mask")
            (result_root / "loss_log.csv").write_text("iteration,total_loss\n10,1.0\n", encoding="utf-8")
            (eval_dir / "failure_case_panels").mkdir()
            (eval_dir / "failure_case_panels" / "failure_summary.md").write_text(
                "highlight_leakage_mask_not_available\nlpips_not_available\n",
                encoding="utf-8",
            )
            metrics_rows = [
                {
                    "category": "rendering",
                    "name": "lpips",
                    "value": "",
                    "not_available_reason": "lpips_not_available",
                },
                {
                    "category": "reflective_region",
                    "name": "refl_lpips",
                    "value": "",
                    "not_available_reason": "lpips_not_available",
                },
                {
                    "category": "geometry",
                    "name": "depth_error",
                    "value": "",
                    "not_available_reason": "gt_depth_not_available",
                },
                {
                    "category": "texture_material",
                    "name": "highlight_leakage_score",
                    "value": "",
                    "not_available_reason": "highlight_leakage_mask_not_available",
                },
                {
                    "category": "texture_material",
                    "name": "albedo_error",
                    "value": "",
                    "not_available_reason": "gt_albedo_not_available",
                },
                {
                    "category": "runtime",
                    "name": "training_time",
                    "value": "",
                    "not_available_reason": "training_time_not_available",
                },
            ]
            metrics_path = eval_dir / "metrics.csv"
            with metrics_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["category", "name", "value", "not_available_reason"])
                writer.writeheader()
                writer.writerows(metrics_rows)

            for field in ["pred_rgb", "gt_rgb", "surface_depth", "roughness_map"]:
                field_dir = render_dir / field
                field_dir.mkdir()
                (field_dir / "00000.png").write_bytes(b"png")
                (field_dir / "00001.png").write_bytes(b"png")
            manifest_path = render_dir / "render_eval_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_path": str(tmp / "source"),
                        "split": "test",
                        "frames": [{"index": 0}, {"index": 1}],
                        "fields": {
                            "pred_rgb": {"available": True, "directory": "pred_rgb"},
                            "gt_rgb": {"available": True, "directory": "gt_rgb"},
                            "surface_depth": {"available": True, "directory": "surface_depth"},
                            "roughness_map": {"available": True, "directory": "roughness_map"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/audit_eval_material_artifacts_m35.py",
                    "--metrics_csv",
                    str(metrics_path),
                    "--failure_summary",
                    str(eval_dir / "failure_case_panels" / "failure_summary.md"),
                    "--manifest",
                    str(manifest_path),
                    "--result_root",
                    str(result_root),
                    "--source_path",
                    str(tmp / "source"),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "eval_material_artifact_requirements.csv",
                output_dir / "eval_material_artifact_plan.json",
                output_dir / "eval_material_artifact_plan.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            payload = json.loads((output_dir / "eval_material_artifact_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["paper_scale_gate"], "NO-GO")
            self.assertFalse(payload["supports_paper_claim"])
            self.assertEqual(payload["unavailable_metric_count"], 6)
            self.assertEqual(payload["plumbing_candidate_count"], 1)
            self.assertIn("highlight-leakage export diagnostic bridge", payload["recommended_next_milestone"])

            with (output_dir / "eval_material_artifact_requirements.csv").open(newline="", encoding="utf-8") as handle:
                rows = {
                    f"{row['category']}/{row['name']}": row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(rows["texture_material/highlight_leakage_score"]["status"], "plumbing_candidate")
            self.assertEqual(rows["texture_material/highlight_leakage_score"]["result_artifact_available"], "true")
            self.assertEqual(rows["texture_material/albedo_error"]["status"], "blocked_missing_gt")
            self.assertEqual(rows["runtime/training_time"]["status"], "blocked_missing_runtime_log")
            self.assertEqual(rows["rendering/lpips"]["render_pair_available"], "true")
            self.assertIn(
                rows["rendering/lpips"]["status"],
                {"blocked_missing_dependency", "dependency_available"},
            )

            report = (output_dir / "eval_material_artifact_plan.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)
            self.assertIn("No train/render/eval runtime launched", report)


if __name__ == "__main__":
    unittest.main()
