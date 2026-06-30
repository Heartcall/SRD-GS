from pathlib import Path
import unittest

import torch

from gaussian_renderer import _slice_feature_or_default


class SRDRenderContractStaticTest(unittest.TestCase):
    def setUp(self):
        self.source = Path("gaussian_renderer/__init__.py").read_text(encoding="utf-8")

    def test_srd_mode_is_gated_by_gaussian_model_flag(self):
        expected_tokens = [
            "enable_srd_gs = getattr(pc, \"enable_srd_gs\", False)",
            "use_branch_gate = getattr(pc, \"srd_use_branch_gate\", False)",
            "if enable_srd_gs:",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_srd_renderer_output_keys_exist(self):
        expected_keys = [
            "'surface_rgb'",
            "'diffuse_rgb'",
            "'specular_rgb'",
            "'roughness_map'",
            "'reflection_dir'",
            "'branch_gate_map'",
            "'specular_weight_map'",
            "'transport_feature_map'",
            "'reflection_residual'",
        ]
        for key in expected_keys:
            with self.subTest(key=key):
                self.assertIn(key, self.source)

    def test_srd_uses_surface_and_reflection_attributes(self):
        expected_tokens = [
            "pc.get_surface_albedo",
            "pc.get_surface_roughness",
            "pc.get_reflection_feature",
            "pc.get_branch_gate",
            "pc.get_specular_weight",
            "pc.get_transport_feature",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_srd_does_not_send_extra_branch_channels_into_current_rasterizer(self):
        self.assertNotIn("[gs_roughness, gs_feature, gs_branch_gate", self.source)
        self.assertIn("rasterizer_extra_channels_unsupported", self.source)

    def test_specular_geometry_detach_contract_exists(self):
        expected_tokens = [
            "getattr(pc, \"srd_detach_specular_geometry\", False)",
            "normals_for_specular = normals.detach()",
            "reflection_dir = reflection_dir.detach()",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_missing_srd_extra_channels_fall_back_to_default_maps(self):
        feature_map = torch.zeros(2, 3, 5)
        default = torch.ones(2, 3, 1)

        sliced = _slice_feature_or_default(feature_map, 5, 1, default)

        self.assertEqual(tuple(sliced.shape), (2, 3, 1))
        self.assertTrue(torch.equal(sliced, default))


if __name__ == "__main__":
    unittest.main()
