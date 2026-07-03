import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class HighlightLeakageDiagnosticBridgeTest(unittest.TestCase):
    def test_bridge_surfaces_export_diagnostic_without_solving_gt_material_metric(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result_root"
            eval_dir = result_root / "eval_with_gt_mesh"
            texture_dir = result_root / "pbr_textures_specular_free"
            output_dir = tmp / "m36"
            eval_dir.mkdir(parents=True)
            texture_dir.mkdir(parents=True)

            (texture_dir / "baking_report.json").write_text(
                json.dumps(
                    {
                        "mode": "specular_free",
                        "output_type": "image_space_material_maps",
                        "observation_count": 2,
                        "highlight_leakage_score": 0.125,
                    }
                ),
                encoding="utf-8",
            )
            (texture_dir / "highlight_leakage_mask.png").write_bytes(b"mask")

            metric_rows = [
                {
                    "category": "texture_material",
                    "name": "highlight_leakage_score",
                    "value": "",
                    "supports_hypothesis": "specular_free_texture",
                    "higher_is_better": "False",
                    "not_available_reason": "highlight_leakage_mask_not_available",
                },
                {
                    "category": "texture_material",
                    "name": "albedo_error",
                    "value": "",
                    "supports_hypothesis": "specular_free_texture",
                    "higher_is_better": "False",
                    "not_available_reason": "gt_albedo_not_available",
                },
            ]
            metrics_csv = eval_dir / "metrics.csv"
            with metrics_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "category",
                        "name",
                        "value",
                        "supports_hypothesis",
                        "higher_is_better",
                        "not_available_reason",
                    ],
                )
                writer.writeheader()
                writer.writerows(metric_rows)

            metrics_json = eval_dir / "metrics.json"
            metrics_json.write_text(
                json.dumps({"metrics": [{**row, "value": None} for row in metric_rows]}),
                encoding="utf-8",
            )
            failure_summary = eval_dir / "failure_case_panels" / "failure_summary.md"
            failure_summary.parent.mkdir()
            failure_summary.write_text(
                "- texture_material/highlight_leakage_score: highlight_leakage_mask_not_available\n"
                "- texture_material/albedo_error: gt_albedo_not_available\n",
                encoding="utf-8",
            )

            m35_plan = tmp / "eval_material_artifact_plan.json"
            m35_plan.write_text(
                json.dumps(
                    {
                        "paper_scale_gate": "NO-GO",
                        "supports_paper_claim": False,
                        "plumbing_candidates": ["texture_material/highlight_leakage_score"],
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/bridge_highlight_leakage_diagnostic_m36.py",
                    "--metrics_csv",
                    str(metrics_csv),
                    "--metrics_json",
                    str(metrics_json),
                    "--failure_summary",
                    str(failure_summary),
                    "--m35_plan",
                    str(m35_plan),
                    "--texture_dir",
                    str(texture_dir),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            for path in [
                output_dir / "highlight_leakage_diagnostic_summary.csv",
                output_dir / "highlight_leakage_diagnostic_summary.json",
                output_dir / "highlight_leakage_diagnostic_summary.md",
                output_dir / "eval_material_augmented_metrics.csv",
                output_dir / "eval_material_augmented_metrics.json",
            ]:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads(
                (output_dir / "highlight_leakage_diagnostic_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["supports_pbr_material_accuracy"])
            self.assertEqual(summary["bridged_diagnostic_count"], 1)
            self.assertEqual(summary["diagnostic_scope"], "export_diagnostic")

            with (output_dir / "eval_material_augmented_metrics.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            source_row = [
                row for row in rows
                if row["category"] == "texture_material" and row["name"] == "highlight_leakage_score"
            ][0]
            diagnostic_row = [
                row for row in rows
                if row["category"] == "texture_material_export_diagnostic"
                and row["name"] == "highlight_leakage_score"
            ][0]
            self.assertEqual(source_row["not_available_reason"], "highlight_leakage_mask_not_available")
            self.assertEqual(diagnostic_row["value"], "0.125")
            self.assertEqual(diagnostic_row["diagnostic_scope"], "export_diagnostic")
            self.assertEqual(diagnostic_row["supports_hypothesis"], "export_artifact_plumbing")

            report = (output_dir / "highlight_leakage_diagnostic_summary.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("GT PBR material accuracy: unsupported", report)
            self.assertIn("No train/render/mesh/texture/eval runtime launched", report)


if __name__ == "__main__":
    unittest.main()
