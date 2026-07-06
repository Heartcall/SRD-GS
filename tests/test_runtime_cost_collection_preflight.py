import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeCostCollectionPreflightTest(unittest.TestCase):
    def test_blocks_collection_that_would_write_into_existing_m32_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            immutable_root = tmp / "outputs" / "srd_gs_instrumented_runtime_m32_i30"
            result_root = immutable_root / "results" / "ball" / "full_srd"
            model_root = immutable_root / "models" / "ball" / "full_srd"
            output_dir = tmp / "m45"
            result_root.mkdir(parents=True)
            model_root.mkdir(parents=True)

            train_command = result_root / "train_command.txt"
            render_command = result_root / "render_eval_pairs_command.txt"
            train_command.write_text(
                f"conda run -n ref_gs python train.py -m {model_root} "
                f"--srd_loss_log_path {result_root / 'loss_log.csv'}\n",
                encoding="utf-8",
            )
            render_command.write_text(
                f"conda run -n ref_gs python render_eval_pairs.py -m {model_root} "
                f"--output_dir {result_root / 'render_eval_pairs'}\n",
                encoding="utf-8",
            )

            wrapper_plan = tmp / "runtime_cost_wrapper_plan.csv"
            with wrapper_plan.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "metric_id",
                        "wrapper_status",
                        "source_command_file",
                        "source_command_available",
                        "required_log",
                        "required_log_available",
                        "runtime_launch_required_for_m44",
                        "planned_wrapper_mode",
                        "collection_method",
                        "failure_condition",
                        "next_action",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "metric_id": "runtime/training_time",
                        "wrapper_status": "wrapper_plan_ready",
                        "source_command_file": str(train_command),
                        "source_command_available": "true",
                        "required_log": str(result_root / "runtime_cost" / "train_timing.json"),
                        "required_log_available": "false",
                        "runtime_launch_required_for_m44": "false",
                        "planned_wrapper_mode": "dry_run_validation_only",
                        "collection_method": "wrap train command with wall-clock timer",
                        "failure_condition": "",
                        "next_action": "",
                    }
                )
                writer.writerow(
                    {
                        "metric_id": "runtime/peak_memory",
                        "wrapper_status": "wrapper_plan_ready",
                        "source_command_file": str(train_command),
                        "source_command_available": "true",
                        "required_log": str(result_root / "runtime_cost" / "gpu_memory_trace.csv"),
                        "required_log_available": "false",
                        "runtime_launch_required_for_m44": "false",
                        "planned_wrapper_mode": "dry_run_validation_only",
                        "collection_method": "sample nvidia-smi during train command",
                        "failure_condition": "",
                        "next_action": "",
                    }
                )
                writer.writerow(
                    {
                        "metric_id": "runtime/render_fps",
                        "wrapper_status": "wrapper_plan_ready",
                        "source_command_file": str(render_command),
                        "source_command_available": "true",
                        "required_log": str(result_root / "runtime_cost" / "render_timing.json"),
                        "required_log_available": "false",
                        "runtime_launch_required_for_m44": "false",
                        "planned_wrapper_mode": "dry_run_validation_only",
                        "collection_method": "wrap render-eval-pairs command",
                        "failure_condition": "",
                        "next_action": "",
                    }
                )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/preflight_runtime_cost_collection_m45.py",
                    "--wrapper_plan_csv",
                    str(wrapper_plan),
                    "--immutable_root",
                    str(immutable_root),
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "runtime_cost_collection_preflight.csv",
                output_dir / "runtime_cost_collection_preflight.json",
                output_dir / "runtime_cost_collection_preflight.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "runtime_cost_collection_preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["milestone"], "M45")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["training_launched"])
            self.assertFalse(summary["rendering_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertFalse(summary["collection_safe_to_launch"])
            self.assertFalse(summary["supports_runtime_cost_claim"])
            self.assertEqual(summary["overwrite_blocker_count"], 3)
            self.assertIn("Milestone 46", summary["recommended_next_milestone"])

            with (output_dir / "runtime_cost_collection_preflight.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(
                rows["runtime/training_time"]["collection_status"],
                "blocked_existing_output_target",
            )
            self.assertEqual(rows["runtime/peak_memory"]["collection_safe_to_launch"], "false")
            self.assertEqual(rows["runtime/render_fps"]["runtime_launched"], "false")

            report = (output_dir / "runtime_cost_collection_preflight.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("blocked_existing_output_target", report)
            self.assertIn("Runtime-cost metric values: unavailable", report)


if __name__ == "__main__":
    unittest.main()
