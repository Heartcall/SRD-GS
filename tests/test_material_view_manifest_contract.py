import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class MaterialViewManifestContractTest(unittest.TestCase):
    def test_builds_manifest_from_render_eval_artifacts_without_computing_metric(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            eval_pairs_dir = tmp / "render_eval_pairs"
            output_dir = tmp / "m40"
            fields = ["diffuse_rgb", "roughness_map", "surface_normal", "pred_rgb", "gt_rgb"]
            for field in fields:
                (eval_pairs_dir / field).mkdir(parents=True, exist_ok=True)
                for index in range(2):
                    suffix = "tiff" if field == "surface_depth" else "png"
                    (eval_pairs_dir / field / f"{index:05d}.{suffix}").write_bytes(b"artifact")

            manifest = tmp / "render_eval_manifest.json"
            _write_json(
                manifest,
                {
                    "schema_version": 1,
                    "split": "test",
                    "source_path": "/example/ball",
                    "frames": [
                        {
                            "index": 0,
                            "image_name": "r_0",
                            "diffuse_rgb": "diffuse_rgb/00000.png",
                            "roughness_map": "roughness_map/00000.png",
                            "surface_normal": "surface_normal/00000.png",
                            "pred_rgb": "pred_rgb/00000.png",
                            "gt_rgb": "gt_rgb/00000.png",
                        },
                        {
                            "index": 1,
                            "image_name": "r_1",
                            "diffuse_rgb": "diffuse_rgb/00001.png",
                            "roughness_map": "roughness_map/00001.png",
                            "surface_normal": "surface_normal/00001.png",
                            "pred_rgb": "pred_rgb/00001.png",
                            "gt_rgb": "gt_rgb/00001.png",
                        },
                    ],
                    "fields": {
                        "diffuse_rgb": {"available": True, "directory": "diffuse_rgb"},
                        "roughness_map": {"available": True, "directory": "roughness_map"},
                        "surface_normal": {"available": True, "directory": "surface_normal"},
                        "pred_rgb": {"available": True, "directory": "pred_rgb"},
                        "gt_rgb": {"available": True, "directory": "gt_rgb"},
                    },
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
                    "scripts/srd_gs/build_material_view_manifest_m40.py",
                    "--manifest",
                    str(manifest),
                    "--eval_pairs_dir",
                    str(eval_pairs_dir),
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
                output_dir / "material_view_manifest.json",
                output_dir / "material_view_manifest.csv",
                output_dir / "material_view_contract_summary.json",
                output_dir / "material_view_contract_report.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "material_view_contract_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertFalse(summary["material_consistency_computed"])
            self.assertFalse(summary["source_metrics_overwritten"])
            self.assertEqual(summary["material_view_count"], 2)
            self.assertEqual(summary["contract_status"], "ready_for_future_material_consistency_compute")
            self.assertIn("Milestone 41", summary["recommended_next_milestone"])

            manifest_payload = json.loads((output_dir / "material_view_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["schema_version"], 1)
            self.assertEqual(len(manifest_payload["material_views"]), 2)
            self.assertEqual(manifest_payload["metric_scope"], "material_view_manifest_only")

            report = (output_dir / "material_view_contract_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Material consistency computed: false", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
