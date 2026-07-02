from pathlib import Path
import json
import tempfile
import unittest

import numpy as np

from utils.metric_utils import (
    compute_geometry_metrics,
    compute_reflective_asset_metrics,
    compute_texture_material_metrics,
    write_metrics_outputs,
)


class ReflectiveAssetMetricsTest(unittest.TestCase):
    def test_rendering_and_reflective_metrics_are_reported_with_hypothesis_flags(self):
        gt = np.zeros((4, 4, 3), dtype=np.float32)
        pred = gt.copy()
        pred[0, 0] = 0.5
        reflective_mask = np.zeros((4, 4), dtype=bool)
        reflective_mask[0, 0] = True

        metrics = compute_reflective_asset_metrics(
            pred_rgb=pred,
            gt_rgb=gt,
            reflective_mask=reflective_mask,
        )
        by_name = {metric["name"]: metric for metric in metrics}

        for name in ("psnr", "ssim", "refl_psnr", "refl_ssim", "lpips", "refl_lpips"):
            self.assertIn(name, by_name)
            self.assertIn("supports_hypothesis", by_name[name])

        self.assertIsNotNone(by_name["psnr"]["value"])
        self.assertIsNotNone(by_name["refl_psnr"]["value"])
        self.assertIsNone(by_name["lpips"]["value"])
        self.assertEqual(by_name["lpips"]["not_available_reason"], "lpips_not_available")

    def test_missing_geometry_ground_truth_is_explicitly_null(self):
        metrics = compute_geometry_metrics(pred_points=np.zeros((2, 3), dtype=np.float32))
        by_name = {metric["name"]: metric for metric in metrics}

        for name in ("chamfer_distance", "f_score", "normal_mae", "depth_error"):
            self.assertIn(name, by_name)
            self.assertIsNone(by_name[name]["value"])
            self.assertIsNotNone(by_name[name]["not_available_reason"])

    def test_highlight_leakage_mask_png_scale_is_normalized(self):
        mask = np.full((2, 2), 128, dtype=np.uint8)

        metrics = compute_texture_material_metrics(highlight_leakage_mask=mask)
        by_name = {metric["name"]: metric for metric in metrics}

        self.assertLess(by_name["highlight_leakage_score"]["value"], 1.0)

    def test_metrics_outputs_include_json_csv_and_auto_mask_visualization(self):
        gt = np.zeros((4, 4, 3), dtype=np.float32)
        pred = gt.copy()
        pred[0, 0] = 1.0
        reflective_mask = np.zeros((4, 4), dtype=bool)
        reflective_mask[0, 0] = True
        metrics = compute_reflective_asset_metrics(pred, gt, reflective_mask)

        with tempfile.TemporaryDirectory() as tmp_dir:
            outputs = write_metrics_outputs(
                metrics,
                output_dir=tmp_dir,
                reflective_mask=reflective_mask,
                mask_source="auto_residual_threshold",
            )

            self.assertTrue(Path(outputs["metrics_json"]).exists())
            self.assertTrue(Path(outputs["metrics_csv"]).exists())
            self.assertTrue(Path(outputs["qualitative_panels"]).is_dir())
            self.assertTrue(Path(outputs["failure_case_panels"]).is_dir())
            self.assertTrue((Path(outputs["failure_case_panels"]) / "failure_summary.md").exists())
            self.assertTrue(Path(outputs["reflective_mask"]).exists())

            payload = json.loads(Path(outputs["metrics_json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["reflective_mask"]["source"], "auto_residual_threshold")
            self.assertIn("metrics", payload)


if __name__ == "__main__":
    unittest.main()
