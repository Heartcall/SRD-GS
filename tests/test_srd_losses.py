import unittest

import torch

from utils.loss_utils import (
    branch_separation_loss,
    highlight_leakage_loss,
    material_consistency_loss,
    specular_sparsity_loss,
    transport_consistency_loss,
)


class SRDLossesTest(unittest.TestCase):
    def assert_scalar_backward(self, loss, tensors):
        self.assertEqual(loss.dim(), 0)
        self.assertTrue(torch.isfinite(loss).item())
        loss.backward()
        for tensor in tensors:
            self.assertIsNotNone(tensor.grad)
            self.assertTrue(torch.isfinite(tensor.grad).all().item())

    def test_branch_separation_loss_is_scalar_and_differentiable(self):
        branch_gate = torch.full((1, 4, 4), 0.5, requires_grad=True)
        specular_weight = torch.full((1, 4, 4), 0.25, requires_grad=True)

        loss = branch_separation_loss(branch_gate, specular_weight)

        self.assert_scalar_backward(loss, [branch_gate, specular_weight])

    def test_material_consistency_loss_is_scalar_and_differentiable(self):
        material = torch.rand(3, 4, 4, requires_grad=True)
        reference = torch.zeros_like(material).requires_grad_(True)
        confidence = torch.ones(1, 4, 4)

        loss = material_consistency_loss(material, reference, confidence)

        self.assert_scalar_backward(loss, [material, reference])

    def test_transport_consistency_loss_is_scalar_and_differentiable(self):
        transport = torch.rand(4, 4, 4, requires_grad=True)
        reference = torch.zeros_like(transport).requires_grad_(True)
        confidence = torch.ones(1, 4, 4)

        loss = transport_consistency_loss(transport, reference, confidence)

        self.assert_scalar_backward(loss, [transport, reference])

    def test_highlight_leakage_loss_is_scalar_and_differentiable(self):
        diffuse_rgb = torch.rand(3, 4, 4, requires_grad=True)
        specular_rgb = torch.rand(3, 4, 4, requires_grad=True)
        branch_gate = torch.full((1, 4, 4), 0.5)

        loss = highlight_leakage_loss(diffuse_rgb, specular_rgb, branch_gate)

        self.assert_scalar_backward(loss, [diffuse_rgb, specular_rgb])

    def test_specular_sparsity_loss_is_scalar_and_differentiable(self):
        specular_rgb = torch.rand(3, 4, 4, requires_grad=True)
        confidence = torch.ones(1, 4, 4)

        loss = specular_sparsity_loss(specular_rgb, confidence)

        self.assert_scalar_backward(loss, [specular_rgb])


if __name__ == "__main__":
    unittest.main()
