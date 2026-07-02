from pathlib import Path
import csv
import json
import subprocess
import tempfile
import unittest

from scripts.srd_gs.preflight_instrumented_runtime import (
    parse_nvidia_smi_gpu_rows,
    summarize_preflight,
)


class InstrumentedRuntimePreflightTest(unittest.TestCase):
    def test_gpu_parser_handles_no_units_rows(self):
        rows = parse_nvidia_smi_gpu_rows("0, 12, 0\n2, 6794, 98\n")

        self.assertEqual(rows[2]["memory_used_mb"], 6794)
        self.assertEqual(rows[2]["utilization_percent"], 98)

    def test_summary_blocks_busy_training_gpu_and_missing_contract(self):
        summary = summarize_preflight(
            label="M30",
            result_root=Path("/tmp/missing"),
            gpu_rows={2: {"index": 2, "memory_used_mb": 6794, "utilization_percent": 98}},
            training_gpu_index=2,
            min_workspace_free_gb=25.0,
            workspace_free_gb=19.0,
            process_matches=[],
            max_gpu_utilization_percent=50,
        )

        self.assertFalse(summary["runtime_go"])
        self.assertIn("training_gpu_busy", summary["blockers"])
        self.assertIn("workspace_free_below_threshold", summary["blockers"])
        self.assertIn("instrumentation_contract_not_ready", summary["blockers"])
        self.assertEqual(summary["paper_scale_gate"], "NO-GO")

    def test_cli_writes_no_go_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result"
            result_root.mkdir()
            (result_root / "train_command.txt").write_text(
                "python train.py --srd_loss_log_path result/loss_log.csv\n",
                encoding="utf-8",
            )
            for name in ["mesh_command.txt", "texture_command.txt", "render_eval_pairs_command.txt", "eval_gt_mesh_command.txt"]:
                (result_root / name).write_text("command\n", encoding="utf-8")
            (result_root / "eval_with_gt_mesh" / "failure_case_panels").mkdir(parents=True)
            output_dir = tmp / "out"

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/preflight_instrumented_runtime.py",
                    "--result_root",
                    str(result_root),
                    "--label",
                    "M30_test",
                    "--output_dir",
                    str(output_dir),
                    "--gpu_rows_text",
                    "2, 1, 99",
                    "--workspace_free_gb",
                    "10",
                    "--min_workspace_free_gb",
                    "25",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            with (output_dir / "instrumented_runtime_preflight.csv").open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            summary = json.loads((output_dir / "instrumented_runtime_preflight.json").read_text(encoding="utf-8"))

            self.assertEqual(row["runtime_go"], "false")
            self.assertFalse(summary["runtime_go"])
            self.assertIn("training_gpu_busy", summary["blockers"])
            self.assertTrue((output_dir / "instrumented_runtime_preflight.md").exists())


if __name__ == "__main__":
    unittest.main()
