import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"artifact")


class GtDepthMaterialProtocolTest(unittest.TestCase):
    def test_audits_gt_candidates_without_computing_metrics_or_overclaiming(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            source_path = tmp / "source" / "ball"
            result_root = tmp / "result"
            output_dir = tmp / "m42"

            _touch(source_path / "test" / "r_0_depth.png")
            _touch(source_path / "test" / "r_1_depth.png")
            _touch(source_path / "test" / "r_0_albedo.png")
            _touch(source_path / "test" / "r_1_albedo.png")
            _touch(source_path / "test" / "r_0_normal.png")
            _touch(source_path / "test" / "r_1_normal.png")
            _touch(result_root / "render_eval_pairs" / "surface_depth" / "00000.tiff")
            _touch(result_root / "render_eval_pairs" / "surface_depth" / "00001.tiff")
            _touch(result_root / "pbr_textures_specular_free" / "albedo.png")
            _touch(result_root / "pbr_textures_specular_free" / "roughness.png")

            metrics_csv = tmp / "metrics.csv"
            _write_csv(
                metrics_csv,
                ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason"],
                [
                    {
                        "category": "geometry",
                        "name": "depth_error",
                        "value": "",
                        "supports_hypothesis": "depth_stability",
                        "higher_is_better": "False",
                        "not_available_reason": "gt_depth_not_available",
                    },
                    {
                        "category": "texture_material",
                        "name": "albedo_error",
                        "value": "",
                        "supports_hypothesis": "specular_free_texture",
                        "higher_is_better": "False",
                        "not_available_reason": "gt_albedo_not_available",
                    },
                    {
                        "category": "texture_material",
                        "name": "roughness_error",
                        "value": "",
                        "supports_hypothesis": "pbr_material_quality",
                        "higher_is_better": "False",
                        "not_available_reason": "gt_roughness_not_available",
                    },
                ],
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/audit_gt_depth_material_protocol_m42.py",
                    "--source_path",
                    str(source_path),
                    "--result_root",
                    str(result_root),
                    "--metrics_csv",
                    str(metrics_csv),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "gt_depth_material_protocol.csv",
                output_dir / "gt_depth_material_candidates.csv",
                output_dir / "gt_depth_material_protocol.json",
                output_dir / "gt_depth_material_protocol.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "gt_depth_material_protocol.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertFalse(summary["metrics_computed"])
            self.assertEqual(summary["ready_contract_count"], 2)
            self.assertEqual(summary["blocked_contract_count"], 1)

            with (output_dir / "gt_depth_material_protocol.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["geometry/depth_error"]["status"], "ready_for_future_metric_compute")
            self.assertEqual(rows["texture_material/albedo_error"]["status"], "ready_for_future_metric_compute")
            self.assertEqual(rows["texture_material/roughness_error"]["status"], "blocked_missing_accepted_gt")
            self.assertEqual(rows["texture_material/roughness_error"]["prediction_artifact_available"], "true")

            report = (output_dir / "gt_depth_material_protocol.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Metrics computed: false", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
