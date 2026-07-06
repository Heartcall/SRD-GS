import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeCostCollectionPackageM46Test(unittest.TestCase):
    def test_clones_runtime_cost_commands_to_fresh_root_and_passes_preflight(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            immutable_root = tmp / "outputs" / "srd_gs_instrumented_runtime_m32_i30"
            source_result_root = immutable_root / "results" / "ball" / "full_srd"
            source_model_root = immutable_root / "models" / "ball" / "full_srd"
            target_output_root = tmp / "outputs" / "srd_gs_runtime_cost_collection_m46"
            target_result_root = target_output_root / "results" / "ball" / "full_srd"
            target_model_root = target_output_root / "models" / "ball" / "full_srd"
            output_dir = tmp / "m46"
            source_result_root.mkdir(parents=True)
            source_model_root.mkdir(parents=True)

            train_command = source_result_root / "train_command.txt"
            render_command = source_result_root / "render_eval_pairs_command.txt"
            train_command.write_text(
                f"conda run -n ref_gs python train.py -m {source_model_root} "
                f"--srd_loss_log_path {source_result_root / 'loss_log.csv'}\n",
                encoding="utf-8",
            )
            render_command.write_text(
                f"conda run -n ref_gs python render_eval_pairs.py -m {source_model_root} "
                f"--output_dir {source_result_root / 'render_eval_pairs'}\n",
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
                        "required_log": str(source_result_root / "runtime_cost" / "train_timing.json"),
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
                        "required_log": str(source_result_root / "runtime_cost" / "gpu_memory_trace.csv"),
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
                        "required_log": str(source_result_root / "runtime_cost" / "render_timing.json"),
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
                    "scripts/srd_gs/prepare_runtime_cost_collection_m46.py",
                    "--wrapper_plan_csv",
                    str(wrapper_plan),
                    "--source_result_root",
                    str(source_result_root),
                    "--source_model_root",
                    str(source_model_root),
                    "--target_result_root",
                    str(target_result_root),
                    "--target_model_root",
                    str(target_model_root),
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
                output_dir / "fresh_runtime_cost_wrapper_plan.csv",
                output_dir / "fresh_runtime_cost_wrapper_plan.json",
                output_dir / "fresh_runtime_cost_wrapper_plan.md",
                output_dir / "preflight" / "runtime_cost_collection_preflight.csv",
                output_dir / "preflight" / "runtime_cost_collection_preflight.json",
                output_dir / "preflight" / "runtime_cost_collection_preflight.md",
                target_result_root / "train_command.txt",
                target_result_root / "render_eval_pairs_command.txt",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            cloned_train = (target_result_root / "train_command.txt").read_text(encoding="utf-8")
            cloned_render = (target_result_root / "render_eval_pairs_command.txt").read_text(encoding="utf-8")
            self.assertIn(str(target_model_root), cloned_train)
            self.assertIn(str(target_result_root / "loss_log.csv"), cloned_train)
            self.assertIn(str(target_result_root / "render_eval_pairs"), cloned_render)
            self.assertNotIn(str(source_model_root), cloned_train)
            self.assertNotIn(str(source_result_root), cloned_render)

            summary = json.loads((output_dir / "fresh_runtime_cost_wrapper_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["milestone"], "M46")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["runtime_launched"])
            self.assertFalse(summary["metrics_computed"])
            self.assertFalse(summary["supports_runtime_cost_claim"])
            self.assertEqual(summary["fresh_wrapper_entry_count"], 3)
            self.assertTrue(summary["preflight_collection_safe_to_launch"])
            self.assertEqual(summary["preflight_overwrite_blocker_count"], 0)

            preflight = json.loads(
                (output_dir / "preflight" / "runtime_cost_collection_preflight.json").read_text(encoding="utf-8")
            )
            self.assertTrue(preflight["collection_safe_to_launch"])
            self.assertEqual(preflight["overwrite_blocker_count"], 0)
            self.assertFalse(preflight["runtime_launched"])

            with (output_dir / "fresh_runtime_cost_wrapper_plan.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["runtime/training_time"]["wrapper_status"], "fresh_root_plan_ready")
            self.assertEqual(rows["runtime/render_fps"]["required_log_available"], "false")
            self.assertEqual(rows["runtime/peak_memory"]["runtime_launched"], "false")


if __name__ == "__main__":
    unittest.main()
