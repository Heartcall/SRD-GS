from pathlib import Path
import tempfile
import unittest

import numpy as np

from utils.geometry_eval_utils import (
    build_geometry_protocol,
    compute_geometry_metrics_from_paths,
    load_point_cloud_xyz,
)


def _write_ascii_ply(path, points):
    lines = [
        "ply",
        "format ascii 1.0",
        "element vertex {}".format(len(points)),
        "property float x",
        "property float y",
        "property float z",
        "end_header",
    ]
    lines.extend("{} {} {}".format(*point) for point in points)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class GeometryEvalUtilsTest(unittest.TestCase):
    def test_shiny_ball_protocol_finds_candidate_but_does_not_silently_accept_it(self):
        protocol = build_geometry_protocol("/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball")

        self.assertEqual(protocol["dataset"], "Shiny Blender Synthetic")
        self.assertTrue(protocol["raw_coordinate_evaluation"])
        self.assertFalse(protocol["icp_enabled_by_default"])
        self.assertEqual(protocol["acceptance_status"], "accepted_gt")
        self.assertIsNone(protocol["not_available_reason"])
        self.assertIn("ball_gt_mesh.ply", protocol["candidate_gt_geometry_path"])
        self.assertEqual(protocol["points3d_source_policy"]["gt_acceptance"], "not_accepted")

    def test_explicit_point_cloud_paths_produce_geometry_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            pred_path = root / "pred.ply"
            gt_path = root / "gt.ply"
            points = np.array(
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                dtype=np.float32,
            )
            _write_ascii_ply(pred_path, points)
            _write_ascii_ply(gt_path, points)

            loaded = load_point_cloud_xyz(str(gt_path))
            self.assertEqual(loaded.shape, (3, 3))

            metrics = compute_geometry_metrics_from_paths(
                pred_geometry_path=str(pred_path),
                gt_geometry_path=str(gt_path),
                accept_gt_geometry=True,
                sample_count=3,
                fscore_threshold=0.01,
            )
            by_name = {metric["name"]: metric for metric in metrics}

            self.assertIsNotNone(by_name["chamfer_distance"]["value"])
            self.assertIsNotNone(by_name["f_score"]["value"])
            self.assertEqual(by_name["f_score"]["value"], 1.0)
            self.assertIsNone(by_name["normal_mae"]["value"])

    def test_source_path_accepted_gt_mesh_enables_geometry_metrics_without_points3d_override(self):
        gt_path = "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball/ball_gt_mesh.ply"

        metrics = compute_geometry_metrics_from_paths(
            pred_geometry_path=gt_path,
            source_path="/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball",
            sample_count=128,
            fscore_threshold=0.01,
        )
        by_name = {metric["name"]: metric for metric in metrics}

        self.assertIsNotNone(by_name["chamfer_distance"]["value"])
        self.assertEqual(by_name["f_score"]["value"], 1.0)


if __name__ == "__main__":
    unittest.main()
