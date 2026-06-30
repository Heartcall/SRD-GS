from pathlib import Path
from types import SimpleNamespace
import unittest

from train import get_srd_training_stage, should_apply_srd_losses


class SRDStageScheduleTest(unittest.TestCase):
    def test_baseline_mode_disables_srd_losses(self):
        dataset = SimpleNamespace(enable_srd_gs=False, srd_stage=0, srd_reflection_warmup=100)

        self.assertEqual(get_srd_training_stage(dataset, 150), "baseline")
        self.assertFalse(should_apply_srd_losses(dataset, 150))

    def test_auto_stage_schedule_switches_by_iteration(self):
        dataset = SimpleNamespace(enable_srd_gs=True, srd_stage=0, srd_reflection_warmup=100)

        self.assertEqual(get_srd_training_stage(dataset, 50), "stage_a")
        self.assertEqual(get_srd_training_stage(dataset, 150), "stage_b")
        self.assertEqual(get_srd_training_stage(dataset, 250), "stage_c")

    def test_manual_stage_override(self):
        dataset = SimpleNamespace(enable_srd_gs=True, srd_stage=2, srd_reflection_warmup=100)

        self.assertEqual(get_srd_training_stage(dataset, 1), "stage_b")
        self.assertTrue(should_apply_srd_losses(dataset, 1))

    def test_train_source_gates_srd_losses(self):
        source = Path("train.py").read_text(encoding="utf-8")

        expected_tokens = [
            "if should_apply_srd_losses(dataset, iteration):",
            "branch_separation_loss(",
            "material_consistency_loss(",
            "transport_consistency_loss(",
            "highlight_leakage_loss(",
            "specular_sparsity_loss(",
            "loss_photo",
            "loss_geo",
            "loss_sep",
            "loss_ref",
            "loss_mat",
            "loss_tex",
            "specular_energy",
            "branch_gate_mean",
            "surface_alpha_mean",
        ]
        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
