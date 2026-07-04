import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class RuntimeCostLoggingContractTest(unittest.TestCase):
    def test_defines_runtime_cost_contract_without_launching_or_computing_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result"
            output_dir = tmp / "m43"
            result_root.mkdir()
            (result_root / "train_command.txt").write_text("conda run -n ref_gs python train.py --iterations 30\n", encoding="utf-8")
            (result_root / "render_eval_pairs_command.txt").write_text("conda run -n ref_gs python render_eval_pairs.py --max_views 2\n", encoding="utf-8")
            metrics_csv = tmp / "metrics.csv"
            _write_csv(
                metrics_csv,
                ["category", "name", "value", "supports_hypothesis", "higher_is_better", "not_available_reason"],
                [
                    {
                        "category": "runtime",
                        "name": "training_time",
                        "value": "",
                        "supports_hypothesis": "runtime_cost",
                        "higher_is_better": "False",
                        "not_available_reason": "training_time_not_available",
                    },
                    {
                        "category": "runtime",
                        "name": "peak_memory",
                        "value": "",
                        "supports_hypothesis": "runtime_cost",
                        "higher_is_better": "False",
                        "not_available_reason": "peak_memory_not_available",
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

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/define_runtime_cost_logging_m43.py",
                    "--result_root",
                    str(result_root),
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
                output_dir / "runtime_cost_logging_contract.csv",
                output_dir / "runtime_cost_logging_contract.json",
                output_dir / "runtime_cost_logging_contract.md",
                output_dir / "runtime_cost_manifest_template.json",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "runtime_cost_logging_contract.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertEqual(summary["instrumentable_contract_count"], 3)
            self.assertEqual(summary["logged_metric_count"], 0)
            self.assertIn("Milestone 44", summary["recommended_next_milestone"])

            with (output_dir / "runtime_cost_logging_contract.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["runtime/training_time"]["status"], "contract_defined_needs_future_runtime")
            self.assertEqual(rows["runtime/peak_memory"]["required_log"], "runtime_cost/gpu_memory_trace.csv")
            self.assertEqual(rows["runtime/render_fps"]["source_command_available"], "true")

            report = (output_dir / "runtime_cost_logging_contract.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Metrics computed: false", report)
            self.assertIn("No train/render/eval runtime launched", report)


if __name__ == "__main__":
    unittest.main()
