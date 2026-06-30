from pathlib import Path
import subprocess
import tempfile
import unittest


class PaperScalePackageContractTest(unittest.TestCase):
    def test_paper_scale_summary_generator_creates_required_outputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_root = Path(tmp_dir) / "srd_gs_experiments"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/make_paper_scale_package.py",
                    "--smoke_root",
                    "outputs/srd_gs_smoke",
                    "--output_root",
                    str(output_root),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            required_paths = [
                output_root / "raw_logs",
                output_root / "metrics",
                output_root / "tables",
                output_root / "figures",
                output_root / "failure_cases",
                output_root / "experiment_summary.md",
                output_root / "tables" / "paper_scale_dry_run_matrix.csv",
                output_root / "tables" / "smoke_metrics_summary.csv",
                output_root / "figures" / "smoke_highlight_leakage.png",
                output_root / "failure_cases" / "claim_gate_status.png",
            ]
            for path in required_paths:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = (output_root / "experiment_summary.md").read_text(encoding="utf-8")
            required_questions = [
                "SRD-GS 是否降低 reflective-region normal MAE？",
                "SRD-GS 是否降低 reflective-region mesh Chamfer / 提高 F-score？",
                "SRD-GS 是否降低 albedo highlight leakage？",
                "SRD-GS 是否保持接近 Ref-GS 的 PSNR/SSIM/LPIPS？",
                "哪个消融最关键？",
                "有没有反驳主假设的结果？",
                "下一步该改代码还是改论文 claim？",
                "Paper-scale claim gate: NO-GO",
            ]
            for text in required_questions:
                self.assertIn(text, summary)


if __name__ == "__main__":
    unittest.main()
