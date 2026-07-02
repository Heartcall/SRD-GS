from pathlib import Path
import csv
import json
import subprocess
import tempfile
import unittest

from scripts.srd_gs.preflight_instrumented_runtime import (
    build_torch_probe_command,
    collect_torch_cuda_probe,
    parse_nvidia_smi_gpu_rows,
    summarize_preflight,
)
import scripts.srd_gs.preflight_instrumented_runtime as preflight


class InstrumentedRuntimePreflightTest(unittest.TestCase):
    def test_gpu_parser_handles_no_units_rows(self):
        rows = parse_nvidia_smi_gpu_rows("0, 12, 0\n2, 6794, 98\n")

        self.assertEqual(rows[2]["memory_used_mb"], 6794)
        self.assertEqual(rows[2]["utilization_percent"], 98)

    def test_torch_probe_prefers_explicit_env_python(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_root = Path(tmp_dir)
            python_path = env_root / "bin" / "python"
            python_path.parent.mkdir(parents=True)
            python_path.write_text("", encoding="utf-8")

            command = build_torch_probe_command(env_root)

        self.assertEqual(command[0], str(python_path))

    def test_torch_probe_falls_back_to_conda_when_direct_env_python_is_false_negative(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_root = Path(tmp_dir)
            python_path = env_root / "bin" / "python"
            python_path.parent.mkdir(parents=True)
            python_path.write_text("", encoding="utf-8")
            calls = []

            def fake_run_command(command):
                calls.append(command)
                if command[0] == str(python_path):
                    return "False\n0\n"
                if command[:4] == ["conda", "run", "-n", "ref_gs"]:
                    return "True\n8\n"
                return ""

            original_run_command = preflight._run_command
            try:
                preflight._run_command = fake_run_command
                torch_cuda_available, torch_device_count = collect_torch_cuda_probe(env_root=env_root)
            finally:
                preflight._run_command = original_run_command

        self.assertTrue(torch_cuda_available)
        self.assertEqual(torch_device_count, 8)
        self.assertEqual(calls[0][0], str(python_path))
        self.assertEqual(calls[1][:4], ["conda", "run", "-n", "ref_gs"])

    def test_summary_blocks_busy_training_gpu_and_missing_contract(self):
        summary = summarize_preflight(
            label="M30",
            result_root=Path("/tmp/missing"),
            gpu_rows={2: {"index": 2, "memory_used_mb": 6794, "utilization_percent": 98}},
            torch_cuda_available=True,
            torch_device_count=8,
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

    def test_torch_visible_gpu_without_nvidia_rows_blocks_as_utilization_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_root = Path(tmp_dir)
            (result_root / "train_command.txt").write_text(
                "python train.py --srd_loss_log_path result/loss_log.csv\n",
                encoding="utf-8",
            )
            for name in ["mesh_command.txt", "texture_command.txt", "render_eval_pairs_command.txt", "eval_gt_mesh_command.txt"]:
                (result_root / name).write_text("command\n", encoding="utf-8")
            (result_root / "eval_with_gt_mesh" / "failure_case_panels").mkdir(parents=True)

            summary = summarize_preflight(
                label="M31",
                result_root=result_root,
                gpu_rows={},
                torch_cuda_available=True,
                torch_device_count=8,
                training_gpu_index=2,
                min_workspace_free_gb=25.0,
                workspace_free_gb=31.0,
                process_matches=[],
                max_gpu_utilization_percent=50,
            )

        self.assertFalse(summary["runtime_go"])
        self.assertTrue(summary["torch_cuda_available"])
        self.assertEqual(summary["torch_device_count"], 8)
        self.assertIn("gpu_utilization_unavailable", summary["blockers"])
        self.assertNotIn("training_gpu_not_visible", summary["blockers"])

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
                    "--torch_cuda_available",
                    "true",
                    "--torch_device_count",
                    "8",
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
