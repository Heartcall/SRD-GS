import unittest

from utils.geometry_eval_utils import (
    build_geometry_protocol,
    inspect_blender_split_policy,
    inspect_points3d_source_policy,
)


BALL_PATH = "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball"


class DatasetSplitAndGTProtocolTest(unittest.TestCase):
    def test_eval_false_explains_empty_test_split_without_data_missing(self):
        policy = inspect_blender_split_policy(BALL_PATH, eval_flag=False)

        self.assertTrue(policy["transforms_train_exists"])
        self.assertTrue(policy["transforms_test_exists"])
        self.assertEqual(policy["transforms_train_frames"], 100)
        self.assertEqual(policy["transforms_test_frames"], 200)
        self.assertEqual(policy["effective_test_frames"], 0)
        self.assertEqual(policy["empty_test_reason"], "eval_false_merges_test_into_train")

    def test_eval_true_keeps_dataset_test_split(self):
        policy = inspect_blender_split_policy(BALL_PATH, eval_flag=True)

        self.assertEqual(policy["effective_train_frames"], 100)
        self.assertEqual(policy["effective_test_frames"], 200)
        self.assertIsNone(policy["empty_test_reason"])

    def test_points3d_is_dataset_generated_candidate_not_accepted_gt(self):
        policy = inspect_points3d_source_policy(BALL_PATH)

        self.assertTrue(policy["points3d_exists"])
        self.assertEqual(policy["gt_acceptance"], "not_accepted")
        self.assertFalse(policy["can_be_used_as_gt_without_manual_verification"])
        self.assertIn("random point cloud", policy["source_evidence"])

        protocol = build_geometry_protocol(BALL_PATH)
        self.assertEqual(protocol["points3d_source_policy"]["gt_acceptance"], "not_accepted")
        self.assertFalse(protocol["points3d_source_policy"]["can_be_used_as_gt_without_manual_verification"])

    def test_scene_gt_mesh_is_accepted_gt_geometry_when_present(self):
        protocol = build_geometry_protocol(BALL_PATH)

        self.assertEqual(protocol["acceptance_status"], "accepted_gt")
        self.assertTrue(protocol["candidate_exists"])
        self.assertEqual(protocol["gt_geometry_type"], "mesh")
        self.assertTrue(protocol["candidate_gt_geometry_path"].endswith("ball_gt_mesh.ply"))
        self.assertIsNone(protocol["not_available_reason"])


if __name__ == "__main__":
    unittest.main()
