from pathlib import Path
import unittest

from gaussian_renderer import get_srd_branch_map_policy


class SRDBranchMapFallbackPolicyTest(unittest.TestCase):
    def test_branch_map_fallback_is_explicit_and_neutral(self):
        policy = get_srd_branch_map_policy(use_branch_gate_requested=True)

        self.assertEqual(policy["policy"], "fallback_neutral_gate")
        self.assertFalse(policy["branch_gate_map"]["rasterized"])
        self.assertFalse(policy["specular_weight_map"]["rasterized"])
        self.assertFalse(policy["transport_feature_map"]["rasterized"])
        self.assertFalse(policy["branch_gate_map"]["backward_to_gaussian"])
        self.assertFalse(policy["specular_weight_map"]["backward_to_gaussian"])
        self.assertFalse(policy["transport_feature_map"]["backward_to_gaussian"])
        self.assertEqual(policy["branch_gate_map"]["fallback_value"], 1.0)
        self.assertFalse(policy["gate_applied"])
        self.assertIn("Needs Runtime Verification", policy["warning"])

    def test_full_srd_config_does_not_enable_branch_gate_while_fallback_is_active(self):
        text = Path("configs/srd_gs/full_srd_gs.yaml").read_text(encoding="utf-8")

        self.assertIn("--enable_srd_gs", text)
        self.assertNotIn("--srd_use_branch_gate", text)
        self.assertIn("branch_gate_policy:", text)
        self.assertIn("fallback_neutral_gate", text)


if __name__ == "__main__":
    unittest.main()
