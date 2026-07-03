import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class LpipsComputePlumbingTest(unittest.TestCase):
    def test_dry_run_then_compute_writes_separate_augmented_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            eval_pairs = tmp / "render_eval_pairs"
            eval_dir = tmp / "eval_with_gt_mesh"
            dry_run_dir = tmp / "m38_dryrun"
            output_dir = tmp / "m38"
            eval_pairs.mkdir()
            eval_dir.mkdir()

            for field in ["pred_rgb", "gt_rgb", "reflective_mask"]:
                field_dir = eval_pairs / field
                field_dir.mkdir()
                for index in ["00000", "00001"]:
                    (field_dir / f"{index}.png").write_bytes(b"png")

            manifest_path = eval_pairs / "render_eval_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
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
                    }
                ),
                encoding="utf-8",
            )

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
                    "category": "rendering",
                    "name": "psnr",
                    "value": "4.0",
                    "supports_hypothesis": "rendering_fidelity",
                    "higher_is_better": "True",
                    "not_available_reason": "",
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
                json.dumps({"metrics": [{**row, "value": None if row["value"] == "" else float(row["value"])} for row in metrics_rows]}),
                encoding="utf-8",
            )

            gate_json = tmp / "lpips_dependency_gate.json"
            gate_json.write_text(
                json.dumps(
                    {
                        "dependency_gate_status": "ready_for_bounded_compute",
                        "paper_scale_gate": "NO-GO",
                        "metrics_computed": False,
                    }
                ),
                encoding="utf-8",
            )
            metric_values = tmp / "lpips_values.json"
            metric_values.write_text(
                json.dumps(
                    {
                        "frames": [
                            {"frame_index": 0, "lpips": 0.11, "refl_lpips": 0.21, "reflective_mask_pixels": 3},
                            {"frame_index": 1, "lpips": 0.13, "refl_lpips": 0.23, "reflective_mask_pixels": 4},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            base_cmd = [
                "python",
                "scripts/srd_gs/compute_lpips_augmented_metrics_m38.py",
                "--metrics_csv",
                str(metrics_csv),
                "--metrics_json",
                str(metrics_json),
                "--manifest",
                str(manifest_path),
                "--eval_pairs_dir",
                str(eval_pairs),
                "--gate_json",
                str(gate_json),
                "--metric_values_json",
                str(metric_values),
            ]
            subprocess.run(
                base_cmd + ["--dry_run", "--output_dir", str(dry_run_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            subprocess.run(
                base_cmd + ["--output_dir", str(output_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.assertTrue((dry_run_dir / "lpips_compute_plan.json").exists())
            self.assertFalse((dry_run_dir / "lpips_augmented_metrics.csv").exists())
            for path in [
                output_dir / "lpips_frame_metrics.csv",
                output_dir / "lpips_augmented_metrics.csv",
                output_dir / "lpips_augmented_metrics.json",
                output_dir / "lpips_compute_summary.json",
                output_dir / "lpips_compute_summary.md",
            ]:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "lpips_compute_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertTrue(summary["dry_run_first_required"])
            self.assertTrue(summary["metrics_computed"])
            self.assertFalse(summary["source_metrics_overwritten"])
            self.assertEqual(summary["frame_count"], 2)
            self.assertAlmostEqual(summary["lpips"], 0.12)
            self.assertAlmostEqual(summary["refl_lpips"], 0.22)

            with (output_dir / "lpips_augmented_metrics.csv").open(newline="", encoding="utf-8") as handle:
                rows = {
                    f"{row['category']}/{row['name']}": row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(rows["rendering/lpips"]["value"], "0.12")
            self.assertEqual(rows["rendering/lpips"]["not_available_reason"], "")
            self.assertEqual(rows["rendering/lpips"]["metric_scope"], "bounded_lpips_compute")
            self.assertEqual(rows["reflective_region/refl_lpips"]["value"], "0.22")

            source_payload = json.loads(metrics_json.read_text(encoding="utf-8"))
            source_rows = {f"{row['category']}/{row['name']}": row for row in source_payload["metrics"]}
            self.assertEqual(source_rows["rendering/lpips"]["not_available_reason"], "lpips_not_available")
            self.assertIsNone(source_rows["rendering/lpips"]["value"])

            report = (output_dir / "lpips_compute_summary.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Source metrics overwritten: false", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
