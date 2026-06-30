from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from utils.texture_baking import (
    bake_image_space_materials,
    compute_baking_weights,
    create_baking_report,
    save_baking_outputs,
)


class TextureBakingWeightsTest(unittest.TestCase):
    def test_high_specular_and_branch_gate_lower_observation_weight(self):
        alpha = torch.ones(1, 2, 2)
        normal = torch.zeros(3, 2, 2)
        normal[2] = 1.0
        viewdir = torch.zeros(3, 2, 2)
        viewdir[2] = 1.0
        specular_rgb = torch.zeros(3, 2, 2)
        branch_gate = torch.zeros(1, 2, 2)

        low_spec_weight = compute_baking_weights(
            alpha=alpha,
            normal=normal,
            viewdir=viewdir,
            specular_rgb=specular_rgb,
            branch_gate_map=branch_gate,
        )

        specular_rgb[:, 0, 0] = 1.0
        branch_gate[:, 0, 0] = 1.0
        high_spec_weight = compute_baking_weights(
            alpha=alpha,
            normal=normal,
            viewdir=viewdir,
            specular_rgb=specular_rgb,
            branch_gate_map=branch_gate,
        )

        self.assertLess(high_spec_weight[0, 0, 0].item(), low_spec_weight[0, 0, 0].item())
        self.assertGreater(high_spec_weight[0, 1, 1].item(), high_spec_weight[0, 0, 0].item())

    def test_specular_free_baking_uses_surface_rgb_not_final_rgb(self):
        render_pkg = {
            "surface_rgb": torch.full((3, 2, 2), 0.2),
            "pbr_rgb": torch.full((3, 2, 2), 0.9),
            "roughness_map": torch.full((1, 2, 2), 0.4),
            "surface_normal": torch.zeros(3, 2, 2),
            "surface_alpha": torch.ones(1, 2, 2),
            "specular_rgb": torch.zeros(3, 2, 2),
            "branch_gate_map": torch.zeros(1, 2, 2),
            "specular_weight_map": torch.full((1, 2, 2), 0.3),
        }
        render_pkg["surface_normal"][2] = 1.0
        direct_rgb = bake_image_space_materials([render_pkg], mode="direct_rgb")
        specular_free = bake_image_space_materials([render_pkg], mode="specular_free")

        self.assertTrue(torch.allclose(direct_rgb["albedo"], torch.full((3, 2, 2), 0.9)))
        self.assertTrue(torch.allclose(specular_free["albedo"], torch.full((3, 2, 2), 0.2)))

    def test_output_paths_and_report_schema(self):
        render_pkg = {
            "surface_rgb": torch.full((3, 2, 2), 0.25),
            "pbr_rgb": torch.full((3, 2, 2), 0.75),
            "roughness_map": torch.full((1, 2, 2), 0.5),
            "surface_normal": torch.zeros(3, 2, 2),
            "surface_alpha": torch.ones(1, 2, 2),
            "specular_rgb": torch.zeros(3, 2, 2),
            "branch_gate_map": torch.zeros(1, 2, 2),
            "specular_weight_map": torch.full((1, 2, 2), 0.2),
        }
        render_pkg["surface_normal"][2] = 1.0
        outputs = bake_image_space_materials([render_pkg], mode="specular_free")

        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = save_baking_outputs(outputs, tmp_dir)
            report = create_baking_report(outputs, paths, mode="specular_free")

            expected_files = {
                "albedo": "albedo.png",
                "roughness": "roughness.png",
                "normal": "normal.png",
                "specular_weight": "specular_weight.png",
                "highlight_leakage_mask": "highlight_leakage_mask.png",
                "report": "baking_report.json",
            }
            for key, filename in expected_files.items():
                self.assertEqual(Path(paths[key]).name, filename)
                self.assertTrue(Path(paths[key]).exists())

            self.assertEqual(report["mode"], "specular_free")
            self.assertEqual(report["output_type"], "image_space_material_maps")
            self.assertIn("highlight_leakage_score", report)
            self.assertIn("observation_count", report)
            self.assertTrue(np.isfinite(report["highlight_leakage_score"]))


if __name__ == "__main__":
    unittest.main()
