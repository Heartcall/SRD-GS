import csv
import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class RuntimeCostCollectionM48Test(unittest.TestCase):
    def test_collects_one_bounded_runtime_cost_run_and_keeps_claim_boundary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            result_root = tmp / "outputs" / "srd_gs_runtime_cost_collection_m46" / "results" / "ball" / "full_srd"
            package_dir = tmp / "outputs" / "srd_gs_runtime_cost_collection_m46" / "package"
            output_dir = tmp / "m48"
            result_root.mkdir(parents=True)
            package_dir.mkdir(parents=True)

            fake_train = tmp / "fake_train.py"
            fake_train.write_text(
                textwrap.dedent(
                    """
                    from pathlib import Path
                    root = Path(r"{result_root}")
                    root.mkdir(parents=True, exist_ok=True)
                    (root / "train_marker.txt").write_text("trained", encoding="utf-8")
                    """
                ).format(result_root=result_root),
                encoding="utf-8",
            )
            fake_render = tmp / "fake_render.py"
            fake_render.write_text(
                textwrap.dedent(
                    """
                    import json
                    from pathlib import Path
                    pair_dir = Path(r"{result_root}") / "render_eval_pairs"
                    pair_dir.mkdir(parents=True, exist_ok=True)
                    payload = {{"frames": [{{"index": 0}}, {{"index": 1}}]}}
                    (pair_dir / "render_eval_manifest.json").write_text(json.dumps(payload), encoding="utf-8")
                    """
                ).format(result_root=result_root),
                encoding="utf-8",
            )

            train_command = result_root / "train_command.txt"
            render_command = result_root / "render_eval_pairs_command.txt"
            train_command.write_text(f"python {fake_train}\n", encoding="utf-8")
            render_command.write_text(f"python {fake_render}\n", encoding="utf-8")

            fresh_plan = package_dir / "fresh_runtime_cost_wrapper_plan.csv"
            with fresh_plan.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "metric_id",
                        "wrapper_status",
                        "source_command_file",
                        "required_log",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "metric_id": "runtime/training_time",
                        "wrapper_status": "fresh_root_plan_ready",
                        "source_command_file": str(train_command),
                        "required_log": str(result_root / "runtime_cost" / "train_timing.json"),
                    }
                )
                writer.writerow(
                    {
                        "metric_id": "runtime/peak_memory",
                        "wrapper_status": "fresh_root_plan_ready",
                        "source_command_file": str(train_command),
                        "required_log": str(result_root / "runtime_cost" / "gpu_memory_trace.csv"),
                    }
                )
                writer.writerow(
                    {
                        "metric_id": "runtime/render_fps",
                        "wrapper_status": "fresh_root_plan_ready",
                        "source_command_file": str(render_command),
                        "required_log": str(result_root / "runtime_cost" / "render_timing.json"),
                    }
                )

            launch_gate = tmp / "runtime_cost_launch_gate.json"
            launch_gate.write_text(
                json.dumps(
                    {
                        "milestone": "M47",
                        "runtime_go": True,
                        "blockers": [],
                        "paper_scale_gate": "NO-GO",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/collect_runtime_cost_m48.py",
                    "--fresh_plan_csv",
                    str(fresh_plan),
                    "--launch_gate_json",
                    str(launch_gate),
                    "--result_root",
                    str(result_root),
                    "--label",
                    "M48_test",
                    "--output_dir",
                    str(output_dir),
                    "--training_gpu_index",
                    "2",
                    "--gpu_rows_text",
                    "2, 100, 0\n2, 200, 0",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                result_root / "runtime_cost" / "train_timing.json",
                result_root / "runtime_cost" / "gpu_memory_trace.csv",
                result_root / "runtime_cost" / "render_timing.json",
                output_dir / "runtime_cost_metrics.csv",
                output_dir / "runtime_cost_metrics.json",
                output_dir / "runtime_cost_metrics.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            summary = json.loads((output_dir / "runtime_cost_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["milestone"], "M48")
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertTrue(summary["runtime_launched"])
            self.assertTrue(summary["training_launched"])
            self.assertTrue(summary["rendering_launched"])
            self.assertFalse(summary["mesh_texture_eval_launched"])
            self.assertTrue(summary["metrics_computed"])
            self.assertTrue(summary["supports_bounded_runtime_cost_measurement"])
            self.assertFalse(summary["supports_runtime_efficiency_claim"])
            self.assertFalse(summary["supports_srd_gs_superiority"])
            self.assertFalse(summary["supports_paper_claim"])
            self.assertEqual(summary["frame_count"], 2)
            self.assertEqual(summary["peak_memory_mb"], 200)

            with (output_dir / "runtime_cost_metrics.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["metric_id"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["runtime/training_time"]["status"], "measured")
            self.assertEqual(rows["runtime/peak_memory"]["value"], "200")
            self.assertEqual(rows["runtime/render_fps"]["status"], "measured")
            self.assertEqual(rows["runtime/render_fps"]["frame_count"], "2")

            report = (output_dir / "runtime_cost_metrics.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
