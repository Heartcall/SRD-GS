from pathlib import Path
import inspect
import unittest

from utils.mesh_utils import GaussianExtractor


class SurfaceOnlyMeshContractTest(unittest.TestCase):
    def setUp(self):
        self.mesh_source = Path("utils/mesh_utils.py").read_text(encoding="utf-8")
        self.renderer_source = Path("gaussian_renderer/__init__.py").read_text(encoding="utf-8")
        self.script_path = Path("extract_surface_mesh.py")

    def test_gaussian_extractor_accepts_surface_only_and_mesh_mode(self):
        signature = inspect.signature(GaussianExtractor.__init__)

        self.assertIn("surface_only", signature.parameters)
        self.assertIn("mesh_mode", signature.parameters)
        self.assertTrue(signature.parameters["surface_only"].default)
        self.assertEqual(signature.parameters["mesh_mode"].default, "surface")

    def test_reconstruction_prefers_surface_buffers(self):
        expected_tokens = [
            "self.surface_only",
            "self.mesh_mode",
            "render_pkg.get('surface_rgb'",
            "render_pkg.get('surface_alpha'",
            "render_pkg.get('surface_depth'",
            "render_pkg.get('surface_normal'",
            "render_pkg.get('specular_rgb'",
            "render_pkg.get('branch_gate_map'",
            "self.specularmaps",
            "self.branch_gatemaps",
            "depth[(alpha < 0.5)] = 0",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.mesh_source)

    def test_renderer_exposes_surface_aliases(self):
        expected_tokens = [
            "'surface_alpha'",
            "'surface_depth'",
            "'surface_normal'",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.renderer_source)

    def test_extract_surface_mesh_script_contract(self):
        self.assertTrue(self.script_path.exists())
        source = self.script_path.read_text(encoding="utf-8")
        expected_tokens = [
            "choices=['surface', 'unified', 'all_branch']",
            "GaussianExtractor(",
            "surface_only=args.mesh_mode == 'surface'",
            "mesh_mode=args.mesh_mode",
            "max_views",
            "train_views[:args.max_views]",
            "extract_mesh_bounded",
            "post_process_mesh",
            "o3d.io.write_triangle_mesh",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
