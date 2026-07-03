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


class LpipsAugmentedDiagnosticSynthesisTest(unittest.TestCase):
    def test_synthesis_integrates_m33_m36_m37_m38_without_claim_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            output_dir = tmp / "m39"
            m33_summary = tmp / "m33_synthesis_summary.json"
            m33_metric_comparison = tmp / "m32_metric_comparison.csv"
            m36_summary = tmp / "highlight_leakage_diagnostic_summary.json"
            m36_diagnostic_csv = tmp / "highlight_leakage_diagnostic_summary.csv"
            m37_gate = tmp / "lpips_dependency_gate.json"
            m38_summary = tmp / "lpips_compute_summary.json"
            m38_augmented = tmp / "lpips_augmented_metrics.csv"

            _write_json(
                m33_summary,
                {
                    "paper_scale_gate": "NO-GO",
                    "supports_paper_claim": False,
                    "m32_psnr_rank": 1,
                    "m32_refl_psnr_rank": 1,
                    "m32_chamfer_rank": 7,
                    "m32_normal_mae_rank": 7,
                    "f_score_blocker": True,
                    "unavailable_metric_count": 10,
                    "render_eval_frames": 2,
                    "loss_rows": 3,
                },
            )
            _write_csv(
                m33_metric_comparison,
                ["label", "psnr", "refl_psnr", "chamfer_distance", "f_score", "normal_mae", "highlight_leakage_score"],
                [
                    {
                        "label": "M18_render_gate_delay_i30",
                        "psnr": "4.08",
                        "refl_psnr": "2.77",
                        "chamfer_distance": "0.43",
                        "f_score": "0",
                        "normal_mae": "86.4",
                        "highlight_leakage_score": "0.0017",
                    },
                    {
                        "label": "M32_instrumented_i30",
                        "psnr": "4.34",
                        "refl_psnr": "2.94",
                        "chamfer_distance": "0.49",
                        "f_score": "0",
                        "normal_mae": "87.3",
                        "highlight_leakage_score": "",
                    },
                ],
            )
            _write_json(
                m36_summary,
                {
                    "paper_scale_gate": "NO-GO",
                    "supports_pbr_material_accuracy": False,
                    "bridged_diagnostic_count": 1,
                    "remaining_metric_blocker_count": 9,
                },
            )
            _write_csv(
                m36_diagnostic_csv,
                ["category", "name", "value", "diagnostic_scope", "source_artifact", "claim_boundary"],
                [
                    {
                        "category": "texture_material_export_diagnostic",
                        "name": "highlight_leakage_score",
                        "value": "0.000975149334408",
                        "diagnostic_scope": "export_diagnostic",
                        "source_artifact": "baking_report.json;highlight_leakage_mask.png",
                        "claim_boundary": "not_gt_pbr_material_accuracy",
                    }
                ],
            )
            _write_json(
                m37_gate,
                {
                    "paper_scale_gate": "NO-GO",
                    "dependency_gate_status": "ready_for_bounded_compute",
                    "ready_metric_count": 2,
                    "metrics_computed": False,
                    "runtime_launched": False,
                },
            )
            _write_json(
                m38_summary,
                {
                    "paper_scale_gate": "NO-GO",
                    "supports_paper_claim": False,
                    "runtime_launched": False,
                    "training_launched": False,
                    "rendering_launched": False,
                    "mesh_texture_eval_launched": False,
                    "metrics_computed": True,
                    "source_metrics_overwritten": False,
                    "lpips": 0.9455429017543793,
                    "refl_lpips": 0.8390642702579498,
                    "frame_count": 2,
                    "source_unavailable_lpips_count": 2,
                },
            )
            _write_csv(
                m38_augmented,
                ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason", "metric_scope", "source_metric_state"],
                [
                    {
                        "category": "rendering",
                        "name": "lpips",
                        "value": "0.945542901754",
                        "supports_hypothesis": "rendering_fidelity",
                        "higher_is_better": "False",
                        "not_available_reason": "",
                        "metric_scope": "bounded_lpips_compute",
                        "source_metric_state": "augmented_from_m38",
                    },
                    {
                        "category": "reflective_region",
                        "name": "refl_lpips",
                        "value": "0.839064270258",
                        "supports_hypothesis": "reflective_region_fidelity",
                        "higher_is_better": "False",
                        "not_available_reason": "",
                        "metric_scope": "bounded_lpips_compute",
                        "source_metric_state": "augmented_from_m38",
                    },
                    {
                        "category": "geometry",
                        "name": "f_score",
                        "value": "0.0",
                        "supports_hypothesis": "surface_geometry_quality",
                        "higher_is_better": "True",
                        "not_available_reason": "",
                        "metric_scope": "",
                        "source_metric_state": "copied",
                    },
                ],
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/synthesize_lpips_augmented_diagnostics_m39.py",
                    "--m33_summary",
                    str(m33_summary),
                    "--m33_metric_comparison",
                    str(m33_metric_comparison),
                    "--m36_summary",
                    str(m36_summary),
                    "--m36_diagnostic_csv",
                    str(m36_diagnostic_csv),
                    "--m37_gate_json",
                    str(m37_gate),
                    "--m38_summary",
                    str(m38_summary),
                    "--m38_augmented_metrics",
                    str(m38_augmented),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "lpips_augmented_diagnostic_summary.csv",
                output_dir / "lpips_augmented_diagnostic_summary.json",
                output_dir / "lpips_augmented_diagnostic_report.md",
                output_dir / "m39_metric_position.csv",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "lpips_augmented_diagnostic_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["supports_paper_claim"])
            self.assertFalse(summary["supports_rendering_recovery"])
            self.assertEqual(summary["quality_interpretation"], "mixed_or_unresolved")
            self.assertTrue(summary["f_score_blocker"])
            self.assertAlmostEqual(summary["lpips"], 0.9455429017543793)
            self.assertAlmostEqual(summary["refl_lpips"], 0.8390642702579498)
            self.assertIn("rendering/lpips", summary["metrics_integrated"])
            self.assertIn("reflective_region/refl_lpips", summary["metrics_integrated"])
            self.assertIn("texture_material_export_diagnostic/highlight_leakage_score", summary["metrics_integrated"])

            report = (output_dir / "lpips_augmented_diagnostic_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)
            self.assertIn("Rendering recovery: unsupported", report)
            self.assertIn("F-score remains zero", report)


if __name__ == "__main__":
    unittest.main()
