import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class InstrumentedRuntimeSynthesisTest(unittest.TestCase):
    def test_synthesis_compares_m32_and_preserves_no_go_boundary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            prior = tmp / "prior_case_summary.csv"
            metrics = tmp / "metrics.csv"
            loss_log = tmp / "loss_log.csv"
            manifest = tmp / "render_eval_manifest.json"
            failure_summary = tmp / "failure_summary.md"
            output_dir = tmp / "summary"

            _write_csv(
                prior,
                [
                    "label",
                    "psnr",
                    "refl_psnr",
                    "chamfer_distance",
                    "f_score",
                    "normal_mae",
                    "highlight_leakage_score",
                ],
                [
                    {
                        "label": "M18",
                        "psnr": "4.0",
                        "refl_psnr": "2.5",
                        "chamfer_distance": "0.40",
                        "f_score": "0.0",
                        "normal_mae": "80.0",
                        "highlight_leakage_score": "0.001",
                    },
                    {
                        "label": "M26",
                        "psnr": "3.0",
                        "refl_psnr": "1.9",
                        "chamfer_distance": "0.32",
                        "f_score": "0.0",
                        "normal_mae": "68.0",
                        "highlight_leakage_score": "0.000007",
                    },
                ],
            )
            _write_csv(
                metrics,
                ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason"],
                [
                    {
                        "category": "rendering",
                        "name": "psnr",
                        "value": "4.3",
                        "supports_hypothesis": "rendering_fidelity",
                        "higher_is_better": "True",
                        "not_available_reason": "",
                    },
                    {
                        "category": "reflective_region",
                        "name": "refl_psnr",
                        "value": "2.9",
                        "supports_hypothesis": "reflective_region_fidelity",
                        "higher_is_better": "True",
                        "not_available_reason": "",
                    },
                    {
                        "category": "geometry",
                        "name": "chamfer_distance",
                        "value": "0.49",
                        "supports_hypothesis": "surface_geometry_quality",
                        "higher_is_better": "False",
                        "not_available_reason": "",
                    },
                    {
                        "category": "geometry",
                        "name": "f_score",
                        "value": "0.0",
                        "supports_hypothesis": "surface_geometry_quality",
                        "higher_is_better": "True",
                        "not_available_reason": "",
                    },
                    {
                        "category": "geometry",
                        "name": "normal_mae",
                        "value": "87.0",
                        "supports_hypothesis": "normal_stability",
                        "higher_is_better": "False",
                        "not_available_reason": "",
                    },
                    {
                        "category": "rendering",
                        "name": "lpips",
                        "value": "",
                        "supports_hypothesis": "rendering_fidelity",
                        "higher_is_better": "False",
                        "not_available_reason": "lpips_not_available",
                    },
                    {
                        "category": "runtime",
                        "name": "render_fps",
                        "value": "",
                        "supports_hypothesis": "runtime_cost",
                        "higher_is_better": "True",
                        "not_available_reason": "render_fps_not_available",
                    },
                ],
            )
            _write_csv(
                loss_log,
                ["iteration", "stage", "total_loss", "loss_photo", "loss_geo", "surface_alpha_mean", "gaussian_count"],
                [
                    {
                        "iteration": "10",
                        "stage": "stage_a",
                        "total_loss": "0.57",
                        "loss_photo": "0.13",
                        "loss_geo": "0.048",
                        "surface_alpha_mean": "0.39",
                        "gaussian_count": "100000",
                    },
                    {
                        "iteration": "20",
                        "stage": "stage_a",
                        "total_loss": "0.50",
                        "loss_photo": "0.12",
                        "loss_geo": "0.047",
                        "surface_alpha_mean": "0.45",
                        "gaussian_count": "100000",
                    },
                    {
                        "iteration": "30",
                        "stage": "stage_a",
                        "total_loss": "0.56",
                        "loss_photo": "0.21",
                        "loss_geo": "0.047",
                        "surface_alpha_mean": "0.46",
                        "gaussian_count": "100000",
                    },
                ],
            )
            _write_json(
                manifest,
                {
                    "iteration": 30,
                    "branch_map_policy": {
                        "policy": "raster_feature_chunks",
                        "branch_gate_weight": 1.0,
                        "render_gate_weight": 0.0,
                        "gate_applied": False,
                    },
                    "fields": {
                        "pred_rgb": {"available": True},
                        "gt_rgb": {"available": True},
                        "surface_depth": {"available": True},
                    },
                    "frames": [{"index": 0}, {"index": 1}],
                },
            )
            failure_summary.write_text(
                "# Failure Summary\n\n"
                "## Unavailable Metrics\n\n"
                "- rendering/lpips: lpips_not_available\n"
                "- runtime/render_fps: render_fps_not_available\n",
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/synthesize_instrumented_runtime_m33.py",
                    "--prior_case_summary",
                    str(prior),
                    "--m32_metrics",
                    str(metrics),
                    "--m32_loss_log",
                    str(loss_log),
                    "--m32_manifest",
                    str(manifest),
                    "--m32_failure_summary",
                    str(failure_summary),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "m32_metric_comparison.csv",
                output_dir / "m32_loss_progression_summary.csv",
                output_dir / "m32_unavailable_metrics.csv",
                output_dir / "m32_manifest_summary.csv",
                output_dir / "m33_synthesis_summary.json",
                output_dir / "m33_synthesis_report.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "m33_synthesis_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertEqual(summary["m32_psnr_rank"], 1)
            self.assertTrue(summary["f_score_blocker"])
            self.assertEqual(summary["loss_rows"], 3)
            self.assertFalse(summary["total_loss_monotonic_nonincreasing"])
            self.assertEqual(summary["unavailable_metric_count"], 2)
            self.assertEqual(summary["render_eval_frames"], 2)

            report = (output_dir / "m33_synthesis_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
