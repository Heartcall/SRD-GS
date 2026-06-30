import json
from pathlib import Path
import tempfile
import unittest

import imageio.v2 as imageio
import numpy as np

from eval_reflective_assets import evaluate_render_eval_pairs_dir


def _write_png(path, array):
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, array)


class EvalPairMetricChainTest(unittest.TestCase):
    def test_eval_pairs_dir_produces_non_null_rendering_and_reflective_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "pairs"
            pred_dir = root / "pred_rgb"
            gt_dir = root / "gt_rgb"
            mask_dir = root / "reflective_mask"

            gt = np.zeros((4, 4, 3), dtype=np.uint8)
            pred = gt.copy()
            pred[0, 0] = np.array([64, 64, 64], dtype=np.uint8)
            mask = np.zeros((4, 4), dtype=np.uint8)
            mask[0, 0] = 255

            _write_png(pred_dir / "00000.png", pred)
            _write_png(gt_dir / "00000.png", gt)
            _write_png(mask_dir / "00000.png", mask)
            _write_png(root / "reflective_mask.png", mask)

            manifest = {
                "schema_version": 1,
                "frames": [
                    {
                        "index": 0,
                        "pred_rgb": "pred_rgb/00000.png",
                        "gt_rgb": "gt_rgb/00000.png",
                        "reflective_mask": "reflective_mask/00000.png",
                    }
                ],
                "fields": {
                    "pred_rgb": {"available": True},
                    "gt_rgb": {"available": True},
                    "reflective_mask": {"available": True},
                },
            }
            (root / "render_eval_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            metrics = evaluate_render_eval_pairs_dir(str(root))
            by_name = {metric["name"]: metric for metric in metrics}

            self.assertIsNotNone(by_name["psnr"]["value"])
            self.assertIsNotNone(by_name["ssim"]["value"])
            self.assertIsNotNone(by_name["refl_psnr"]["value"])
            self.assertIsNotNone(by_name["refl_ssim"]["value"])
            self.assertIsNone(by_name["lpips"]["value"])
            self.assertEqual(by_name["lpips"]["not_available_reason"], "lpips_not_available")


if __name__ == "__main__":
    unittest.main()
