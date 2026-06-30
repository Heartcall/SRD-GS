import unittest

import torch

from utils.srd_branch_maps import (
    pack_srd_raster_feature_chunks,
    pack_srd_raster_features,
    unpack_srd_raster_maps,
    unpack_srd_raster_maps_from_chunks,
)
from utils.srd_branch_policy import get_srd_branch_map_policy


class SRDBranchRasterFeatureTest(unittest.TestCase):
    def test_pack_and_unpack_branch_maps_when_enabled(self):
        roughness = torch.full((2, 1), 0.2)
        reflection = torch.arange(8, dtype=torch.float32).reshape(2, 4)
        branch_gate = torch.full((2, 1), 0.3)
        specular_weight = torch.full((2, 1), 0.4)
        transport = torch.arange(6, dtype=torch.float32).reshape(2, 3)

        packed, metadata = pack_srd_raster_features(
            roughness,
            reflection,
            branch_gate,
            specular_weight,
            transport,
            rasterize_branch_maps=True,
        )

        self.assertEqual(tuple(packed.shape), (2, 10))
        self.assertEqual(metadata["branch_gate"], (5, 6))
        self.assertEqual(metadata["specular_weight"], (6, 7))
        self.assertEqual(metadata["transport_feature"], (7, 10))

        feature_map = packed.reshape(1, 2, 10)
        unpacked, policy = unpack_srd_raster_maps(
            feature_map,
            gsfeat_dim=4,
            transport_dim=3,
            rasterize_branch_maps=True,
            use_branch_gate_requested=True,
        )

        self.assertTrue(policy["branch_gate_map"]["rasterized"])
        self.assertTrue(policy["branch_gate_map"]["backward_to_gaussian"])
        self.assertTrue(policy["gate_applied"])
        self.assertTrue(torch.equal(unpacked["branch_gate_map"], branch_gate.reshape(1, 2, 1)))
        self.assertTrue(torch.equal(unpacked["specular_weight_map"], specular_weight.reshape(1, 2, 1)))
        self.assertTrue(torch.equal(unpacked["transport_feature_map"], transport.reshape(1, 2, 3)))

    def test_default_policy_remains_fallback_and_neutral(self):
        policy = get_srd_branch_map_policy(use_branch_gate_requested=True)

        self.assertEqual(policy["policy"], "fallback_neutral_gate")
        self.assertFalse(policy["branch_gate_map"]["rasterized"])
        self.assertEqual(policy["branch_gate_map"]["fallback_value"], 1.0)

    def test_disabled_pack_excludes_branch_channels(self):
        roughness = torch.full((2, 1), 0.2)
        reflection = torch.zeros(2, 4)
        branch_gate = torch.full((2, 1), 0.3)
        specular_weight = torch.full((2, 1), 0.4)
        transport = torch.zeros(2, 3)

        packed, metadata = pack_srd_raster_features(
            roughness,
            reflection,
            branch_gate,
            specular_weight,
            transport,
            rasterize_branch_maps=False,
        )

        self.assertEqual(tuple(packed.shape), (2, 5))
        self.assertFalse(metadata["rasterize_branch_maps"])
        self.assertNotIn("branch_gate", metadata)

    def test_chunked_pack_keeps_each_cuda_feature_pass_within_base_channel_limit(self):
        roughness = torch.full((2, 1), 0.2)
        reflection = torch.arange(8, dtype=torch.float32).reshape(2, 4)
        branch_gate = torch.full((2, 1), 0.3)
        specular_weight = torch.full((2, 1), 0.4)
        transport = torch.arange(8, dtype=torch.float32).reshape(2, 4)

        primary, extra_chunks, metadata = pack_srd_raster_feature_chunks(
            roughness,
            reflection,
            branch_gate,
            specular_weight,
            transport,
            channel_limit=5,
        )

        self.assertEqual(tuple(primary.shape), (2, 5))
        self.assertEqual(len(extra_chunks), 2)
        self.assertTrue(all(chunk.shape == (2, 5) for chunk in extra_chunks))
        self.assertEqual(metadata["extra_channel_count"], 6)
        self.assertEqual(metadata["extra_chunks"], [(0, 5), (5, 6)])

        primary_map = primary.reshape(1, 2, 5)
        extra_maps = [chunk.reshape(1, 2, 5) for chunk in extra_chunks]
        unpacked, policy = unpack_srd_raster_maps_from_chunks(
            primary_map,
            extra_maps,
            gsfeat_dim=4,
            transport_dim=4,
            chunk_metadata=metadata,
            use_branch_gate_requested=True,
        )

        self.assertEqual(policy["policy"], "raster_feature_chunks")
        self.assertTrue(policy["branch_gate_map"]["rasterized"])
        self.assertTrue(torch.equal(unpacked["branch_gate_map"], branch_gate.reshape(1, 2, 1)))
        self.assertTrue(torch.equal(unpacked["specular_weight_map"], specular_weight.reshape(1, 2, 1)))
        self.assertTrue(torch.equal(unpacked["transport_feature_map"], transport.reshape(1, 2, 4)))


if __name__ == "__main__":
    unittest.main()
