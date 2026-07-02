import json
from pathlib import Path
import subprocess
import tempfile
import unittest


class DiagnosticDirectionDecisionTest(unittest.TestCase):
    def test_decision_matrix_recommends_material_artifact_plumbing_without_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            summary_path = tmp / "m33_synthesis_summary.json"
            output_dir = tmp / "decision"
            summary_path.write_text(
                json.dumps(
                    {
                        "m32_psnr_rank": 1,
                        "m32_refl_psnr_rank": 1,
                        "m32_chamfer_rank": 7,
                        "m32_normal_mae_rank": 7,
                        "f_score_blocker": True,
                        "loss_rows": 3,
                        "total_loss_monotonic_nonincreasing": False,
                        "unavailable_metric_count": 10,
                        "paper_scale_gate": "NO-GO",
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/decide_diagnostic_direction_m34.py",
                    "--m33_summary",
                    str(summary_path),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "diagnostic_direction_matrix.csv",
                output_dir / "diagnostic_direction_decision.json",
                output_dir / "diagnostic_direction_decision.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            decision = json.loads((output_dir / "diagnostic_direction_decision.json").read_text(encoding="utf-8"))
            self.assertEqual(decision["paper_scale_gate"], "NO-GO")
            self.assertFalse(decision["supports_paper_claim"])
            self.assertEqual(decision["recommended_direction"], "eval_material_artifact_plumbing")
            self.assertIn("stage_bc_activation", decision["deferred_directions"])
            self.assertIn("opacity_schedule", decision["deferred_directions"])

            report = (output_dir / "diagnostic_direction_decision.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)
            self.assertIn("eval_material_artifact_plumbing", report)


if __name__ == "__main__":
    unittest.main()
