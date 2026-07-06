#!/usr/bin/env python3
"""Round3 CLI behavior tests for the limitation-analysis helpers."""

import json
import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]


class Round3PipelineTests(unittest.TestCase):
    def test_export_dry_run_accepts_component_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "scene"
            model = tmp_path / "model"
            source.mkdir()
            cmd = [
                sys.executable,
                "experiments/ref_gs_limitation_analysis/export_pbr_views.py",
                "--dry-run",
                "--source_path",
                str(source),
                "--model_path",
                str(model),
                "--checkpoint",
                str(model / "chkpnt2.pth"),
                "--split",
                "test",
                "--max_views",
                "1",
                "--return_components",
                "--render_func",
                "auto",
                "--save_npz",
                "--save_png",
                "--out_dir",
                str(tmp_path / "export"),
            ]
            result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((tmp_path / "export" / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["dry_run"])
            self.assertTrue(manifest["return_components"])
            self.assertEqual(manifest["render_func"], "auto")

    def test_evaluate_pbr_reports_render_gap_and_missing_buffers(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            export = tmp_path / "export"
            view_dir = export / "views" / "00000_r_0"
            view_dir.mkdir(parents=True)
            gt = view_dir / "gt.png"
            pbr = view_dir / "pbr_rgb.png"
            render = view_dir / "render.png"
            Image.new("RGB", (1, 1), (128, 128, 128)).save(gt)
            Image.new("RGB", (1, 1), (128, 128, 128)).save(pbr)
            Image.new("RGB", (1, 1), (0, 0, 0)).save(render)
            manifest = {
                "dry_run": False,
                "views": [
                    {
                        "image_name": "r_0",
                        "index": 0,
                        "buffers": {
                            "gt": {"exported": True, "path": str(gt)},
                            "pbr_rgb": {"exported": True, "path": str(pbr)},
                            "render": {"exported": True, "path": str(render)},
                            "specular": {"exported": False, "missing": True, "reason": "not returned"},
                        },
                        "files": {
                            "gt": str(gt),
                            "pbr_rgb": str(pbr),
                            "render": str(render),
                        },
                    }
                ],
            }
            (export / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            out = tmp_path / "metrics"
            cmd = [
                sys.executable,
                "experiments/ref_gs_limitation_analysis/evaluate_pbr.py",
                "--export_dir",
                str(export),
                "--out",
                str(out),
                "--skip-lpips",
            ]
            result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads((out / "summary_metrics.json").read_text(encoding="utf-8"))
            self.assertIn("pbr_rgb_vs_render_gap", summary)
            self.assertEqual(summary["pbr_rgb_vs_render_gap"]["psnr_delta"], "inf")
            self.assertTrue((out / "missing_buffers.md").exists())

    def test_export_mesh_accepts_strict_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "scene"
            model = tmp_path / "model"
            source.mkdir()
            cmd = [
                sys.executable,
                "experiments/ref_gs_limitation_analysis/export_mesh.py",
                "--source_path",
                str(source),
                "--model_path",
                str(model),
                "--checkpoint",
                str(model / "chkpnt2.pth"),
                "--out_mesh",
                str(tmp_path / "mesh" / "mesh.ply"),
                "--dry-run",
                "--strict",
            ]
            result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_timing_probe_strict_returns_training_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [
                "bash",
                "experiments/ref_gs_limitation_analysis/run_timing_probe.sh",
                "--script",
                "definitely_missing_train_script.py",
                "--scene",
                str(Path(tmp) / "scene"),
                "--model",
                str(Path(tmp) / "model"),
                "--iterations",
                "1",
                "--strict",
            ]
            result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_component_sanity_strict_returns_nonzero_on_failed_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env.update(
                {
                    "STRICT": "1",
                    "ROUND_NAME": "unit_strict",
                    "RUN_TRAIN": "1",
                    "RUN_EXPORT": "0",
                    "RUN_EVAL": "0",
                    "RUN_MESH": "0",
                    "SANITY_SCRIPT": "definitely_missing_train_script.py",
                    "SCENE_PATH": str(Path(tmp) / "scene"),
                    "MODEL_PATH": str(Path(tmp) / "model"),
                    "SANITY_ITER": "1",
                }
            )
            result = subprocess.run(
                ["bash", "experiments/ref_gs_limitation_analysis/run_component_sanity.sh"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
