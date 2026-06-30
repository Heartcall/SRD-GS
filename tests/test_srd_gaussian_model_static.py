import ast
from argparse import ArgumentParser
from pathlib import Path
import unittest

from arguments import ModelParams


GAUSSIAN_MODEL_SOURCE = Path("scene/gaussian_model.py")


class SRDGaussianModelStaticTest(unittest.TestCase):
    def setUp(self):
        self.source = GAUSSIAN_MODEL_SOURCE.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_cli_flags_exist_with_baseline_safe_defaults(self):
        parser = ArgumentParser()
        ModelParams(parser)
        args = parser.parse_args([])

        self.assertFalse(args.enable_srd_gs)
        self.assertEqual(args.srd_stage, 0)
        self.assertEqual(args.srd_reflection_warmup, 3000)
        self.assertFalse(args.srd_detach_specular_geometry)
        self.assertFalse(args.srd_use_branch_gate)
        self.assertFalse(args.srd_rasterize_branch_maps)
        self.assertEqual(args.srd_reflection_dim, 4)
        self.assertEqual(args.srd_transport_dim, 4)

    def test_srd_parameter_names_exist(self):
        expected = [
            "_surface_albedo",
            "_surface_roughness",
            "_reflection_feature",
            "_specular_weight",
            "_branch_gate",
            "_transport_feature",
        ]
        for name in expected:
            with self.subTest(name=name):
                self.assertIn(name, self.source)

    def test_optimizer_group_names_exist(self):
        expected = [
            '"surface_albedo"',
            '"surface_roughness"',
            '"reflection_feature"',
            '"specular_weight"',
            '"branch_gate"',
            '"transport_feature"',
        ]
        for name in expected:
            with self.subTest(name=name):
                self.assertIn(name, self.source)

    def test_baseline_path_is_not_forced_to_use_srd_branch(self):
        expected_tokens = [
            "self.enable_srd_gs = getattr(args, \"enable_srd_gs\", False)",
            "return self.get_albedo if not self.enable_srd_gs else",
            "return self.get_roughness if not self.enable_srd_gs else",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_save_load_backward_compatibility_fallbacks_exist(self):
        expected_tokens = [
            "surface_albedo_names",
            "surface_roughness_names",
            "reflection_feature_names",
            "specular_weight_names",
            "branch_gate_names",
            "transport_feature_names",
            "_load_optional_ply_group",
            "default=self._albedo.detach().cpu().numpy()",
            "default=self._roughness.detach().cpu().numpy()",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.source)


if __name__ == "__main__":
    unittest.main()
