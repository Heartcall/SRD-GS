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


class OpacityTradeoffSummaryTest(unittest.TestCase):
    def test_summary_outputs_no_go_tradeoff_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            case_summary = tmp / "case_summary.csv"
            parameter_deltas = tmp / "parameter_deltas.csv"
            output_dir = tmp / "summary"

            _write_csv(
                case_summary,
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
                        "label": "M18_render_gate_delay_i30",
                        "psnr": "4.0",
                        "refl_psnr": "2.7",
                        "chamfer_distance": "0.42",
                        "f_score": "0.0",
                        "normal_mae": "86.0",
                        "highlight_leakage_score": "0.001",
                    },
                    {
                        "label": "M24_reflection_freeze_i300",
                        "psnr": "2.8",
                        "refl_psnr": "1.7",
                        "chamfer_distance": "0.28",
                        "f_score": "0.0",
                        "normal_mae": "74.0",
                        "highlight_leakage_score": "0.000001",
                    },
                    {
                        "label": "M25_opacity_freeze_i300",
                        "psnr": "3.6",
                        "refl_psnr": "2.3",
                        "chamfer_distance": "0.39",
                        "f_score": "0.0",
                        "normal_mae": "73.0",
                        "highlight_leakage_score": "0.0002",
                    },
                    {
                        "label": "M26_opacity_quarter_i300",
                        "psnr": "3.1",
                        "refl_psnr": "1.9",
                        "chamfer_distance": "0.32",
                        "f_score": "0.0",
                        "normal_mae": "68.0",
                        "highlight_leakage_score": "0.000007",
                    },
                ],
            )
            _write_csv(
                parameter_deltas,
                [
                    "baseline_label",
                    "comparison_label",
                    "opacity_activated_mean_delta_vs_baseline",
                    "reflection_feature_abs_mean_delta_vs_baseline",
                    "specular_weight_activated_mean_delta_vs_baseline",
                ],
                [
                    {
                        "baseline_label": "M18_render_gate_delay_i30",
                        "comparison_label": "M24_reflection_freeze_i300",
                        "opacity_activated_mean_delta_vs_baseline": "0.16",
                        "reflection_feature_abs_mean_delta_vs_baseline": "-0.01",
                        "specular_weight_activated_mean_delta_vs_baseline": "0.0",
                    },
                    {
                        "baseline_label": "M18_render_gate_delay_i30",
                        "comparison_label": "M25_opacity_freeze_i300",
                        "opacity_activated_mean_delta_vs_baseline": "-0.07",
                        "reflection_feature_abs_mean_delta_vs_baseline": "-0.01",
                        "specular_weight_activated_mean_delta_vs_baseline": "0.0",
                    },
                    {
                        "baseline_label": "M18_render_gate_delay_i30",
                        "comparison_label": "M26_opacity_quarter_i300",
                        "opacity_activated_mean_delta_vs_baseline": "0.007",
                        "reflection_feature_abs_mean_delta_vs_baseline": "-0.01",
                        "specular_weight_activated_mean_delta_vs_baseline": "0.0",
                    },
                ],
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/summarize_opacity_tradeoff.py",
                    "--case_summary",
                    str(case_summary),
                    "--parameter_deltas",
                    str(parameter_deltas),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "opacity_tradeoff_summary.csv",
                output_dir / "opacity_tradeoff_summary.json",
                output_dir / "opacity_tradeoff_summary.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            with (output_dir / "opacity_tradeoff_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["label"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["M25_opacity_freeze_i300"]["is_best_rendering"], "true")
            self.assertEqual(rows["M24_reflection_freeze_i300"]["is_best_chamfer"], "true")
            self.assertEqual(rows["M26_opacity_quarter_i300"]["is_best_normal_mae"], "true")
            self.assertEqual(rows["M26_opacity_quarter_i300"]["is_closest_opacity_to_baseline"], "true")

            summary = json.loads((output_dir / "opacity_tradeoff_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertTrue(summary["f_score_blocker"])
            self.assertEqual(summary["best_rendering_label"], "M25_opacity_freeze_i300")
            self.assertEqual(summary["best_geometry_chamfer_label"], "M24_reflection_freeze_i300")
            self.assertEqual(summary["best_normal_mae_label"], "M26_opacity_quarter_i300")
            self.assertEqual(summary["closest_opacity_label"], "M26_opacity_quarter_i300")

            report = (output_dir / "opacity_tradeoff_summary.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
