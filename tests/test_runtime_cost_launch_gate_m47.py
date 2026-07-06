import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeCostLaunchGateM47Test(unittest.TestCase):
    def test_launch_gate_goes_true_for_fresh_package_with_idle_gpu_and_storage(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "outputs" / "srd_gs_runtime_cost_collection_m46" / "results" / "ball" / "full_srd"
            package_dir = tmp / "outputs" / "srd_gs_runtime_cost_collection_m46" / "package"
            preflight_dir = package_dir / "preflight"
            output_dir = tmp / "m47"
            result_root.mkdir(parents=True)
            preflight_dir.mkdir(parents=True)

            train_command = result_root / "train_command.txt"
            render_command = result_root / "render_eval_pairs_command.txt"
            train_command.write_text(
                "conda run -n ref_gs python train.py -m model --srd_loss_log_path result/loss_log.csv\n",
                encoding="utf-8",
            )
            render_command.write_text(
                "conda run -n ref_gs python render_eval_pairs.py -m model --output_dir result/render_eval_pairs\n",
                encoding="utf-8",
            )

            fresh_plan = package_dir / "fresh_runtime_cost_wrapper_plan.csv"
            with fresh_plan.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "metric_id",
                        "wrapper_status",
                        "source_command_file",
                        "source_command_available",
                        "required_log",
                        "required_log_available",
                        "runtime_launch_required_for_m46",
                        "runtime_launched",
                        "planned_wrapper_mode",
                        "collection_method",
                        "failure_condition",
                        "next_action",
                        "source_result_root",
                        "target_result_root",
                        "source_model_root",
                        "target_model_root",
                    ],
                )
                writer.writeheader()
                for metric_id, command_file, required_log in [
                    ("runtime/training_time", train_command, result_root / "runtime_cost" / "train_timing.json"),
                    ("runtime/peak_memory", train_command, result_root / "runtime_cost" / "gpu_memory_trace.csv"),
                    ("runtime/render_fps", render_command, result_root / "runtime_cost" / "render_timing.json"),
                ]:
                    writer.writerow(
                        {
                            "metric_id": metric_id,
                            "wrapper_status": "fresh_root_plan_ready",
                            "source_command_file": str(command_file),
                            "source_command_available": "true",
                            "required_log": str(required_log),
                            "required_log_available": "false",
                            "runtime_launch_required_for_m46": "false",
                            "runtime_launched": "false",
                            "planned_wrapper_mode": "fresh_root_no_launch_package",
                            "collection_method": "bounded runtime-cost collection",
                            "failure_condition": "none",
                            "next_action": "gate before launch",
                            "source_result_root": "old",
                            "target_result_root": str(result_root),
                            "source_model_root": "old_model",
                            "target_model_root": "new_model",
                        }
                    )

            preflight_summary = preflight_dir / "runtime_cost_collection_preflight.json"
            preflight_summary.write_text(
                json.dumps(
                    {
                        "collection_safe_to_launch": True,
                        "overwrite_blocker_count": 0,
                        "safe_collection_entry_count": 3,
                        "runtime_launched": False,
                        "metrics_computed": False,
                        "paper_scale_gate": "NO-GO",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/preflight_runtime_cost_launch_m47.py",
                    "--fresh_plan_csv",
                    str(fresh_plan),
                    "--collection_preflight_json",
                    str(preflight_summary),
                    "--result_root",
                    str(result_root),
                    "--label",
                    "M47_test",
                    "--output_dir",
                    str(output_dir),
                    "--training_gpu_index",
                    "2",
                    "--gpu_rows_text",
                    "2, 100, 0",
                    "--torch_cuda_available",
                    "true",
                    "--torch_device_count",
                    "8",
                    "--workspace_free_gb",
                    "40",
                    "--min_workspace_free_gb",
                    "25",
                    "--skip_process_scan",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "runtime_cost_launch_gate.csv",
                output_dir / "runtime_cost_launch_gate.json",
                output_dir / "runtime_cost_launch_gate.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "runtime_cost_launch_gate.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["milestone"], "M47")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertTrue(summary["runtime_go"])
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertFalse(summary["supports_runtime_cost_claim"])
            self.assertEqual(summary["blockers"], [])
            self.assertEqual(summary["fresh_wrapper_entry_count"], 3)
            self.assertEqual(summary["runtime_cost_log_count"], 0)

            with (output_dir / "runtime_cost_launch_gate.csv").open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["runtime_go"], "true")
            self.assertEqual(row["training_gpu_utilization_percent"], "0")
            self.assertEqual(row["runtime_launched"], "false")

            report = (output_dir / "runtime_cost_launch_gate.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Runtime GO: True", report)
            self.assertIn("Runtime-cost metric values: unavailable", report)


if __name__ == "__main__":
    unittest.main()
