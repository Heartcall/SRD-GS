from pathlib import Path
import unittest


class RefGSRenderContractStaticTest(unittest.TestCase):
    def test_renderer_source_contains_expected_output_contract(self):
        source = Path("gaussian_renderer/__init__.py").read_text(encoding="utf-8")
        expected_tokens = [
            "pbr_rgb",
            "rend_alpha",
            "rend_normal",
            "surf_depth",
            "surf_normal",
            "roughness",
            "spec_light",
            "diff_light",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
