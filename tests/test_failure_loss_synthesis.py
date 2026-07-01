import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_file(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_complete_case(root, *, with_loss_log=False, with_failure_panel=False):
    _write_file(root / "train_command.txt", "python train.py --enable_srd_gs\n")
    _write_file(root / "mesh_surface.ply", "ply\n")
    _write_json(root / "pbr_textures_specular_free" / "baking_report.json", {"highlight_leakage_score": 0.1})
    _write_json(root / "eval_with_gt_mesh" / "metrics.json", {"metrics": []})
    _write_json(
        root / "render_eval_pairs" / "render_eval_manifest.json",
        {
            "frames": [
                {
                    "pred_rgb": "pred_rgb/00000.png",
                    "gt_rgb": "gt_rgb/00000.png",
                    "diffuse_rgb": "diffuse_rgb/00000.png",
                    "specular_rgb": "specular_rgb/00000.png",
                    "branch_gate_map": "branch_gate_map/00000.png",
                    "roughness_map": "roughness_map/00000.png",
                    "surface_depth": "surface_depth/00000.tiff",
                    "surface_normal": "surface_normal/00000.png",
                    "reflective_mask": "reflective_mask/00000.png",
                }
            ]
        },
    )
    for rel_path in [
        "pred_rgb/00000.png",
        "gt_rgb/00000.png",
        "diffuse_rgb/00000.png",
        "specular_rgb/00000.png",
        "branch_gate_map/00000.png",
        "roughness_map/00000.png",
        "surface_depth/00000.tiff",
        "surface_normal/00000.png",
        "reflective_mask/00000.png",
    ]:
        _write_file(root / "render_eval_pairs" / rel_path)
    if with_loss_log:
        _write_file(root / "loss_log.csv", "iter,total\n0,1.0\n")
    if with_failure_panel:
        _write_file(root / "failure_cases" / "panel.png")


class FailureLossSynthesisTest(unittest.TestCase):
    def test_outputs_artifact_matrix_and_no_go_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            complete = tmp / "complete"
            missing = tmp / "missing"
            _write_complete_case(complete, with_loss_log=False, with_failure_panel=False)
            _write_file(missing / "train_command.txt", "python train.py\n")

            output_dir = tmp / "summary"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/summarize_failure_loss_artifacts.py",
                    "--case",
                    f"M26={complete}",
                    "--case",
                    f"broken={missing}",
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "failure_loss_artifact_matrix.csv",
                output_dir / "failure_loss_synthesis.json",
                output_dir / "failure_loss_synthesis.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            with (output_dir / "failure_loss_artifact_matrix.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["label"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["M26"]["core_artifact_chain_complete"], "true")
            self.assertEqual(rows["M26"]["loss_log_available"], "false")
            self.assertEqual(rows["M26"]["failure_panel_available"], "false")
            self.assertEqual(rows["broken"]["core_artifact_chain_complete"], "false")

            summary = json.loads((output_dir / "failure_loss_synthesis.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["paper_scale_gate"], "NO-GO")
            self.assertFalse(summary["supports_paper_claim"])
            self.assertTrue(summary["needs_loss_log_instrumentation"])
            self.assertTrue(summary["needs_failure_panel_generation"])
            self.assertEqual(summary["complete_core_artifact_cases"], ["M26"])

            report = (output_dir / "failure_loss_synthesis.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
