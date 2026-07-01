from argparse import ArgumentParser
from pathlib import Path
import unittest

from arguments import ModelParams
from utils.srd_schedule import compute_srd_branch_gate_weight


class SRDBranchGateScheduleTest(unittest.TestCase):
    def test_branch_gate_weight_is_backward_compatible_by_default(self):
        self.assertEqual(
            compute_srd_branch_gate_weight(
                use_branch_gate=True,
                iteration=1,
                start_iter=0,
                ramp_iters=0,
            ),
            1.0,
        )
        self.assertEqual(
            compute_srd_branch_gate_weight(
                use_branch_gate=False,
                iteration=100,
                start_iter=0,
                ramp_iters=0,
            ),
            0.0,
        )

    def test_branch_gate_weight_supports_delay_and_linear_ramp(self):
        kwargs = {
            "use_branch_gate": True,
            "start_iter": 10,
            "ramp_iters": 20,
        }

        self.assertEqual(compute_srd_branch_gate_weight(iteration=9, **kwargs), 0.0)
        self.assertEqual(compute_srd_branch_gate_weight(iteration=10, **kwargs), 0.0)
        self.assertEqual(compute_srd_branch_gate_weight(iteration=20, **kwargs), 0.5)
        self.assertEqual(compute_srd_branch_gate_weight(iteration=30, **kwargs), 1.0)
        self.assertEqual(compute_srd_branch_gate_weight(iteration=40, **kwargs), 1.0)

    def test_cli_flags_exist_with_neutral_defaults(self):
        parser = ArgumentParser()
        ModelParams(parser)
        args = parser.parse_args([])

        self.assertEqual(args.srd_branch_gate_start_iter, 0)
        self.assertEqual(args.srd_branch_gate_ramp_iters, 0)

    def test_render_and_export_paths_use_checkpoint_iteration_for_schedule(self):
        render_source = Path("gaussian_renderer/__init__.py").read_text(encoding="utf-8")
        render_eval_source = Path("render_eval_pairs.py").read_text(encoding="utf-8")
        texture_source = Path("export_pbr_textures.py").read_text(encoding="utf-8")
        mesh_source = Path("extract_surface_mesh.py").read_text(encoding="utf-8")
        mesh_utils_source = Path("utils/mesh_utils.py").read_text(encoding="utf-8")

        self.assertIn("compute_srd_branch_gate_weight(", render_source)
        self.assertIn("branch_gate_weight", render_source)
        self.assertIn("iteration=iteration", render_eval_source)
        self.assertIn("render_iteration=scene.loaded_iter", texture_source)
        self.assertIn("render_iteration=scene.loaded_iter", mesh_source)
        self.assertIn("render_iteration", mesh_utils_source)


if __name__ == "__main__":
    unittest.main()
