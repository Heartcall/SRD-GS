import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class RuntimeCostWrapperValidationTest(unittest.TestCase):
    def test_validates_dry_run_wrapper_plan_without_launching_runtime(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "result"
            output_dir = tmp / "m44"
            result_root.mkdir()
            train_command = result_root / "train_command.txt"
            render_command = result_root / "render_eval_pairs_command.txt"
            train_command.write_text("conda run -n ref_gs python train.py --iterations 30\n", encoding="utf-8")
            render_command.write_text(
                "conda run -n ref_gs python render_eval_pairs.py --max_views 2\n",
                encoding="utf-8",
            )
            contract_json = tmp / "runtime_cost_logging_contract.json"
            manifest_template = tmp / "runtime_cost_manifest_template.json"
            _write_json(
                contract_json,
                {
                    "milestone": "M43",
                    "paper_scale_gate": "NO-GO",
                    "contract_count": 3,
                    "instrumentable_contract_count": 3,
                    "metrics_computed": False,
                    "runtime_launched": False,
                },
            )
            _write_json(
                manifest_template,
                {
                    "schema_version": 1,
                    "milestone": "M43",
                    "paper_scale_gate": "NO-GO",
                    "runtime_launched": False,
                    "metrics_computed": False,
                    "entries": [
                        {
                            "metric_id": "runtime/training_time",
                            "command_file": str(train_command),
                            "required_log": str(result_root / "runtime_cost" / "train_timing.json"),
                            "collection_method": "wrap train command with wall-clock timer",
                            "expected_parser": "future_bounded_runtime_cost_parser",
                        },
                        {
                            "metric_id": "runtime/peak_memory",
                            "command_file": str(train_command),
                            "required_log": str(result_root / "runtime_cost" / "gpu_memory_trace.csv"),
                            "collection_method": "sample nvidia-smi during train command",
                            "expected_parser": "future_bounded_runtime_cost_parser",
                        },
                        {
                            "metric_id": "runtime/render_fps",
                            "command_file": str(render_command),
                            "required_log": str(result_root / "runtime_cost" / "render_timing.json"),
                            "collection_method": "wrap render-eval-pairs command",
                            "expected_parser": "future_bounded_runtime_cost_parser",
                        },
                    ],
                },
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/validate_runtime_cost_wrapper_m44.py",
                    "--contract_json",
                    str(contract_json),
                    "--manifest_template",
                    str(manifest_template),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "runtime_cost_wrapper_plan.csv",
                output_dir / "runtime_cost_wrapper_plan.json",
                output_dir / "runtime_cost_wrapper_plan.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "runtime_cost_wrapper_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["milestone"], "M44")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["training_launched"])
            self.assertFalse(summary["rendering_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertFalse(summary["supports_runtime_cost_claim"])
            self.assertEqual(summary["wrapper_plan_ready_count"], 3)
            self.assertEqual(summary["blocked_wrapper_count"], 0)
            self.assertIn("Milestone 45", summary["recommended_next_milestone"])

            with (output_dir / "runtime_cost_wrapper_plan.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["runtime/training_time"]["wrapper_status"], "wrapper_plan_ready")
            self.assertEqual(rows["runtime/peak_memory"]["source_command_available"], "true")
            self.assertEqual(rows["runtime/render_fps"]["runtime_launch_required_for_m44"], "false")

            report = (output_dir / "runtime_cost_wrapper_plan.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("No train/render/eval runtime launched", report)
            self.assertIn("Runtime-cost metric values: unavailable", report)


if __name__ == "__main__":
    unittest.main()
