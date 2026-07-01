import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np
from plyfile import PlyData, PlyElement


def _write_checkpoint(root, *, iteration, opacity, specular_weight, branch_gate, scale):
    point_dir = root / "point_cloud" / f"iteration_{iteration}"
    point_dir.mkdir(parents=True)
    vertex_count = 3
    dtype = [
        ("x", "f4"),
        ("y", "f4"),
        ("z", "f4"),
        ("opacity", "f4"),
        ("scale_0", "f4"),
        ("scale_1", "f4"),
        ("scale_2", "f4"),
        ("surface_roughness_0", "f4"),
        ("reflection_feature_0", "f4"),
        ("reflection_feature_1", "f4"),
        ("specular_weight_0", "f4"),
        ("branch_gate_0", "f4"),
        ("transport_feature_0", "f4"),
        ("transport_feature_1", "f4"),
    ]
    data = np.zeros(vertex_count, dtype=dtype)
    data["x"] = np.array([0.0, 1.0, 2.0], dtype=np.float32)
    data["y"] = np.array([0.0, 0.5, 1.0], dtype=np.float32)
    data["z"] = np.array([0.0, 0.0, 0.5], dtype=np.float32)
    data["opacity"] = opacity
    for name in ["scale_0", "scale_1", "scale_2"]:
        data[name] = scale
    data["surface_roughness_0"] = -2.0
    data["reflection_feature_0"] = specular_weight
    data["reflection_feature_1"] = specular_weight * 0.5
    data["specular_weight_0"] = specular_weight
    data["branch_gate_0"] = branch_gate
    data["transport_feature_0"] = branch_gate
    data["transport_feature_1"] = branch_gate * 0.5
    PlyData([PlyElement.describe(data, "vertex")]).write(point_dir / "point_cloud.ply")

    (root / "cfg_args").write_text(
        "Namespace(enable_srd_gs=True, eval=True, srd_reflection_warmup=3000, "
        f"srd_render_gate_start_iter={iteration}, srd_render_gate_ramp_iters=0)",
        encoding="utf-8",
    )


class CheckpointDriftDiagnosisTest(unittest.TestCase):
    def test_checkpoint_diagnosis_reports_parameter_drift_without_claim_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            m18 = tmp / "m18_model"
            m20 = tmp / "m20_model"
            m21 = tmp / "m21_model"
            _write_checkpoint(m18, iteration=30, opacity=-2.0, specular_weight=-3.0, branch_gate=-3.0, scale=-4.0)
            _write_checkpoint(m20, iteration=300, opacity=-1.0, specular_weight=0.0, branch_gate=-2.0, scale=-3.0)
            _write_checkpoint(m21, iteration=300, opacity=-1.2, specular_weight=-0.5, branch_gate=-2.0, scale=-3.1)

            output_dir = tmp / "diagnosis"
            subprocess.run(
                [
                    "python",
                    "scripts/srd_gs/diagnose_checkpoint_drift.py",
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
                output_dir / "checkpoint_summary.csv",
                output_dir / "parameter_stats.csv",
                output_dir / "parameter_deltas.csv",
                output_dir / "checkpoint_diagnosis_summary.json",
                output_dir / "checkpoint_diagnosis_report.md",
            ]
            for path in expected_outputs:
                with self.subTest(path=path):
                    self.assertTrue(path.exists())

            with (output_dir / "checkpoint_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["label"] for row in rows], ["M18", "M20", "M21"])
            self.assertEqual(rows[0]["gaussian_count"], "3")
            self.assertEqual(rows[1]["iteration"], "300")

            with (output_dir / "parameter_deltas.csv").open(newline="", encoding="utf-8") as handle:
                deltas = {row["comparison_label"]: row for row in csv.DictReader(handle)}
            self.assertGreater(float(deltas["M20"]["specular_weight_activated_mean_delta_vs_baseline"]), 0.0)
            self.assertGreater(float(deltas["M20"]["scale_exp_mean_delta_vs_baseline"]), 0.0)

            summary = json.loads((output_dir / "checkpoint_diagnosis_summary.json").read_text(encoding="utf-8"))
            self.assertIn("no_gaussian_count_growth", summary["diagnosis_flags"])
            self.assertIn("branch_or_specular_parameter_drift_present", summary["diagnosis_flags"])

            report = (output_dir / "checkpoint_diagnosis_report.md").read_text(encoding="utf-8")
            self.assertIn("Paper-scale gate: NO-GO", report)
            self.assertIn("Complete root cause: unsupported", report)


if __name__ == "__main__":
    unittest.main()
