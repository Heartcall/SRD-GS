from pathlib import Path
import unittest

from render_eval_pairs import RENDER_EVAL_FIELDS, build_empty_manifest


class RenderEvalPairsStaticTest(unittest.TestCase):
    def test_script_exists_and_declares_required_artifact_schema(self):
        path = Path("render_eval_pairs.py")
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")

        for dirname in (
            "pred_rgb",
            "gt_rgb",
            "diffuse_rgb",
            "specular_rgb",
            "surface_depth",
            "surface_normal",
            "roughness_map",
            "branch_gate_map",
        ):
            with self.subTest(dirname=dirname):
                self.assertIn(dirname, RENDER_EVAL_FIELDS)
                self.assertIn(dirname, text)

        self.assertNotIn("albedo", RENDER_EVAL_FIELDS)
        self.assertIn("not_available_reason", text)
        self.assertIn("render_pkg.get(\"srd_branch_map_policy\")", text)

    def test_manifest_records_baseline_and_srd_modes(self):
        manifest = build_empty_manifest(
            model_path="model",
            source_path="scene",
            split="test",
            iteration=20,
            enable_srd_gs=False,
            branch_map_policy={"policy": "baseline_no_srd"},
        )

        self.assertEqual(manifest["schema_version"], 1)
        self.assertFalse(manifest["enable_srd_gs"])
        self.assertEqual(manifest["branch_map_policy"]["policy"], "baseline_no_srd")
        self.assertIn("pred_rgb", manifest["fields"])
        self.assertEqual(manifest["fields"]["diffuse_rgb"]["not_available_reason"], "not_rendered_yet")


if __name__ == "__main__":
    unittest.main()
