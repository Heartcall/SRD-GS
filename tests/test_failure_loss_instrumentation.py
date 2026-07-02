from pathlib import Path
import csv
import json
import subprocess
import tempfile
import unittest


class FailureLossInstrumentationTest(unittest.TestCase):
    def test_inspector_reports_dry_run_loss_and_failure_panel_contract(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result"
            (result_root / "eval_with_gt_mesh" / "failure_case_panels").mkdir(parents=True)
            (result_root / "train_command.txt").write_text(
                "conda run -n ref_gs python train.py --srd_loss_log_path "
                f"{result_root}/loss_log.csv\n",
                encoding="utf-8",
            )
            for name in ["mesh_command.txt", "texture_command.txt", "render_eval_pairs_command.txt", "eval_gt_mesh_command.txt"]:
                (result_root / name).write_text("command without loss log\n", encoding="utf-8")

            output_dir = tmp / "summary"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/inspect_failure_loss_instrumentation.py",
                    "--result_root",
                    str(result_root),
                    "--label",
                    "M29_dryrun",
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            with (output_dir / "failure_loss_instrumentation.csv").open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            summary = json.loads((output_dir / "failure_loss_instrumentation.json").read_text(encoding="utf-8"))
            report = (output_dir / "failure_loss_instrumentation.md").read_text(encoding="utf-8")

            self.assertEqual(row["loss_log_path_in_train_command"], "true")
            self.assertEqual(row["loss_log_path_leaks_to_non_train_commands"], "false")
            self.assertEqual(row["failure_panel_output_dir_expected"], "true")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertIn("dry-run", report)


if __name__ == "__main__":
    unittest.main()
