import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import imageio.v2 as imageio
import numpy as np


def _write_png(path, value, shape=(4, 4, 3)):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full(shape, value, dtype=np.uint8)
    imageio.imwrite(path, image)


def _write_case(root, *, iteration, render_gate_weight, psnr, refl_psnr, chamfer, leakage, pred_value):
    eval_dir = root / "eval_with_gt_mesh"
    eval_dir.mkdir(parents=True)
    metrics = {
        "metrics": [
            {"category": "rendering", "name": "psnr", "value": psnr, "higher_is_better": True},
            {"category": "reflective_region", "name": "refl_psnr", "value": refl_psnr, "higher_is_better": True},
            {"category": "geometry", "name": "chamfer_distance", "value": chamfer, "higher_is_better": False},
            {"category": "geometry", "name": "f_score", "value": 0.0, "higher_is_better": True},
            {"category": "geometry", "name": "normal_mae", "value": 75.0, "higher_is_better": False},
        ]
    }
    (eval_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    baking_dir = root / "pbr_textures_specular_free"
    baking_dir.mkdir()
    (baking_dir / "baking_report.json").write_text(
        json.dumps({"highlight_leakage_score": leakage}),
        encoding="utf-8",
    )

    pair_dir = root / "render_eval_pairs"
    for field, value in [
        ("pred_rgb", pred_value),
        ("gt_rgb", 50),
        ("diffuse_rgb", max(pred_value - 10, 0)),
        ("specular_rgb", 8),
        ("branch_gate_map", 255),
        ("roughness_map", 128),
    ]:
        _write_png(pair_dir / field / "00000.png", value)
    _write_png(pair_dir / "reflective_mask" / "00000.png", 255, shape=(4, 4))

    manifest = {
        "schema_version": 1,
        "iteration": iteration,
        "branch_map_policy": {
            "policy": "raster_feature_chunks",
            "gate_applied": render_gate_weight > 0.0,
            "branch_gate_weight": 1.0,
            "render_gate_weight": render_gate_weight,
        },
        "frames": [
            {
                "index": 0,
                "pred_rgb": "pred_rgb/00000.png",
                "gt_rgb": "gt_rgb/00000.png",
                "diffuse_rgb": "diffuse_rgb/00000.png",
                "specular_rgb": "specular_rgb/00000.png",
                "branch_gate_map": "branch_gate_map/00000.png",
                "roughness_map": "roughness_map/00000.png",
                "reflective_mask": "reflective_mask/00000.png",
            }
        ],
    }
    (pair_dir / "render_eval_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class RenderRegressionDiagnosisTest(unittest.TestCase):
    def test_diagnosis_outputs_tables_and_no_overclaim_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            m18 = tmp / "m18"
            m20 = tmp / "m20"
            m21 = tmp / "m21"
            _write_case(m18, iteration=30, render_gate_weight=0.0, psnr=4.0, refl_psnr=2.7, chamfer=0.42, leakage=0.001, pred_value=60)
            _write_case(m20, iteration=300, render_gate_weight=1.0, psnr=2.9, refl_psnr=1.5, chamfer=0.31, leakage=0.006, pred_value=30)
            _write_case(m21, iteration=300, render_gate_weight=0.0, psnr=2.8, refl_psnr=1.5, chamfer=0.30, leakage=0.003, pred_value=28)

            output_dir = tmp / "diagnosis"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/diagnose_render_regression.py",
                    "--case",
                    f"M18={m18}",
                    "--case",
                    f"M20={m20}",
                    "--case",
                    f"M21={m21}",
                    "--output_dir",
                    str(output_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            expected_outputs = [
                output_dir / "case_summary.csv",
                output_dir / "map_stats.csv",
                output_dir / "pairwise_deltas.csv",
                output_dir / "diagnosis_summary.json",
                output_dir / "diagnosis_report.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            with (output_dir / "case_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["label"] for row in rows], ["M18", "M20", "M21"])
            self.assertEqual(rows[2]["render_gate_weight"], "0.0")

            with (output_dir / "pairwise_deltas.csv").open(newline="", encoding="utf-8") as handle:
                deltas = {row["comparison_label"]: row for row in csv.DictReader(handle)}
            self.assertLess(float(deltas["M21"]["psnr_delta_vs_baseline"]), 0.0)
            self.assertLess(float(deltas["M21"]["refl_psnr_delta_vs_baseline"]), 0.0)

            summary = json.loads((output_dir / "diagnosis_summary.json").read_text(encoding="utf-8"))
            self.assertIn("render_gate_activation_not_sole_cause", summary["diagnosis_flags"])

            report = (output_dir / "diagnosis_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("SRD-GS superiority: unsupported", report)


if __name__ == "__main__":
    unittest.main()
