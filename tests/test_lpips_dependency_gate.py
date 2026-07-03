import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class LpipsDependencyGateTest(unittest.TestCase):
    def test_gate_marks_lpips_metrics_ready_without_computing_or_overwriting_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            eval_pairs = tmp / "render_eval_pairs"
            eval_dir = tmp / "eval_with_gt_mesh"
            output_dir = tmp / "m37"
            eval_pairs.mkdir()
            eval_dir.mkdir()

            for field in ["pred_rgb", "gt_rgb", "reflective_mask"]:
                field_dir = eval_pairs / field
                field_dir.mkdir()
                (field_dir / "00000.png").write_bytes(b"png")
                (field_dir / "00001.png").write_bytes(b"png")

            manifest = {
                "split": "test",
                "frames": [
                    {
                        "index": 0,
                        "pred_rgb": "pred_rgb/00000.png",
                        "gt_rgb": "gt_rgb/00000.png",
                        "reflective_mask": "reflective_mask/00000.png",
                    },
                    {
                        "index": 1,
                        "pred_rgb": "pred_rgb/00001.png",
                        "gt_rgb": "gt_rgb/00001.png",
                        "reflective_mask": "reflective_mask/00001.png",
                    },
                ],
                "fields": {
                    "pred_rgb": {"available": True, "directory": "pred_rgb"},
                    "gt_rgb": {"available": True, "directory": "gt_rgb"},
                },
                "reflective_mask": {"available": True, "path": "reflective_mask.png"},
            }
            manifest_path = eval_pairs / "render_eval_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            metrics_rows = [
                {
                    "category": "rendering",
                    "name": "lpips",
                    "value": "",
                    "supports_hypothesis": "rendering_fidelity",
                    "higher_is_better": "False",
                    "not_available_reason": "lpips_not_available",
                },
                {
                    "category": "reflective_region",
                    "name": "refl_lpips",
                    "value": "",
                    "supports_hypothesis": "reflective_region_fidelity",
                    "higher_is_better": "False",
                    "not_available_reason": "lpips_not_available",
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
                writer.writerows(metrics_rows)

            metrics_json = eval_dir / "metrics.json"
            metrics_json.write_text(
                json.dumps({"metrics": [{**row, "value": None} for row in metrics_rows]}),
                encoding="utf-8",
            )
            probe_json = tmp / "lpips_probe.json"
            probe_json.write_text(
                json.dumps(
                    {
                        "lpips_import_available": True,
                        "lpips_origin": "/fake/site-packages/lpips/__init__.py",
                        "torch_import_available": True,
                        "torch_version": "2.0.0",
                        "model_init_attempted": True,
                        "model_init_available": True,
                        "model_init_error": "",
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/gate_lpips_dependency_m37.py",
                    "--metrics_csv",
                    str(metrics_csv),
                    "--metrics_json",
                    str(metrics_json),
                    "--manifest",
                    str(manifest_path),
                    "--eval_pairs_dir",
                    str(eval_pairs),
                    "--probe_json",
                    str(probe_json),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            for path in [
                output_dir / "lpips_dependency_gate.csv",
                output_dir / "lpips_dependency_gate.json",
                output_dir / "lpips_dependency_gate.md",
            ]:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "lpips_dependency_gate.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertEqual(summary["dependency_gate_status"], "ready_for_bounded_compute")
            self.assertEqual(summary["ready_metric_count"], 2)
            self.assertEqual(summary["source_unavailable_lpips_count"], 2)

            with (output_dir / "lpips_dependency_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = {
                    f"{row['category']}/{row['name']}": row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(rows["rendering/lpips"]["status"], "ready_for_bounded_compute")
            self.assertEqual(rows["reflective_region/refl_lpips"]["status"], "ready_for_bounded_compute")
            self.assertEqual(rows["reflective_region/refl_lpips"]["reflective_mask_available"], "true")

            source_payload = json.loads(metrics_json.read_text(encoding="utf-8"))
            source_rows = {f"{row['category']}/{row['name']}": row for row in source_payload["metrics"]}
            self.assertEqual(source_rows["rendering/lpips"]["not_available_reason"], "lpips_not_available")
            self.assertIsNone(source_rows["rendering/lpips"]["value"])

            report = (output_dir / "lpips_dependency_gate.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("No train/render/mesh/texture/eval runtime launched", report)
            self.assertIn("LPIPS values computed: false", report)


if __name__ == "__main__":
    unittest.main()
