import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_rgb(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.full((2, 2, 3), value, dtype=np.uint8)
    Image.fromarray(data, mode="RGB").save(path)


class MaterialConsistencyDiagnosticTest(unittest.TestCase):
    def test_computes_diagnostic_from_manifest_without_overwriting_source_metric(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            output_dir = tmp / "m41"
            view0_diffuse = tmp / "diffuse_rgb" / "00000.png"
            view1_diffuse = tmp / "diffuse_rgb" / "00001.png"
            view0_roughness = tmp / "roughness_map" / "00000.png"
            view1_roughness = tmp / "roughness_map" / "00001.png"
            _write_rgb(view0_diffuse, 10)
            _write_rgb(view1_diffuse, 20)
            _write_rgb(view0_roughness, 30)
            _write_rgb(view1_roughness, 50)

            manifest = tmp / "material_view_manifest.json"
            _write_json(
                manifest,
                {
                    "schema_version": 1,
                    "metric_scope": "material_view_manifest_only",
                    "paper_scale_gate": "NO-GO",
                    "contract_status": "ready_for_future_material_consistency_compute",
                    "required_fields": ["diffuse_rgb", "roughness_map"],
                    "material_consistency_computed": False,
                    "source_metrics_overwritten": False,
                    "material_views": [
                        {
                            "view_index": "0",
                            "image_name": "r_0",
                            "complete_required_material_fields": "true",
                            "diffuse_rgb_path": str(view0_diffuse),
                            "roughness_map_path": str(view0_roughness),
                        },
                        {
                            "view_index": "1",
                            "image_name": "r_1",
                            "complete_required_material_fields": "true",
                            "diffuse_rgb_path": str(view1_diffuse),
                            "roughness_map_path": str(view1_roughness),
                        },
                    ],
                },
            )
            metrics_csv = tmp / "metrics.csv"
            _write_csv(
                metrics_csv,
                ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason"],
                [
                    {
                        "category": "texture_material",
                        "name": "material_consistency",
                        "value": "",
                        "supports_hypothesis": "material_view_consistency",
                        "higher_is_better": "False",
                        "not_available_reason": "need_at_least_two_material_views",
                    }
                ],
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/compute_material_consistency_m41.py",
                    "--material_view_manifest",
                    str(manifest),
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
                output_dir / "material_consistency_pairwise.csv",
                output_dir / "material_consistency_diagnostic.csv",
                output_dir / "material_consistency_summary.json",
                output_dir / "material_consistency_report.md",
                output_dir / "eval_material_augmented_metrics.csv",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "material_consistency_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertFalse(summary["supports_pbr_material_accuracy"])
            self.assertFalse(summary["source_metrics_overwritten"])
            self.assertTrue(summary["material_consistency_diagnostic_computed"])
            self.assertEqual(summary["pair_count"], 1)
            expected_mae = ((10.0 / 255.0) + (20.0 / 255.0)) / 2.0
            self.assertAlmostEqual(summary["material_consistency_mae"], expected_mae)

            with (output_dir / "eval_material_augmented_metrics.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            source_row = [row for row in rows if row["category"] == "texture_material"][0]
            diagnostic_row = [row for row in rows if row["category"] == "texture_material_diagnostic"][0]
            self.assertEqual(source_row["name"], "material_consistency")
            self.assertEqual(source_row["not_available_reason"], "need_at_least_two_material_views")
            self.assertEqual(diagnostic_row["name"], "material_consistency_mae")
            self.assertEqual(diagnostic_row["metric_scope"], "bounded_material_view_diagnostic")

            report = (output_dir / "material_consistency_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("GT PBR material accuracy: unsupported", report)
            self.assertIn("Source metrics overwritten: false", report)


if __name__ == "__main__":
    unittest.main()
