import torch

from utils.srd_branch_policy import get_srd_branch_map_policy


def pack_srd_raster_features(
    roughness,
    reflection_feature,
    branch_gate=None,
    specular_weight=None,
    transport_feature=None,
    rasterize_branch_maps=False,
):
    if not rasterize_branch_maps:
        return torch.cat([roughness, reflection_feature], dim=-1), {
            "rasterize_branch_maps": False,
            "roughness": (0, 1),
            "reflection_feature": (1, 1 + reflection_feature.shape[-1]),
        }

    required = {
        "branch_gate": branch_gate,
        "specular_weight": specular_weight,
        "transport_feature": transport_feature,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ValueError("missing_srd_branch_raster_inputs:{}".format(",".join(missing)))

    feature_start = 1
    feature_end = feature_start + reflection_feature.shape[-1]
    branch_start = feature_end
    branch_end = branch_start + branch_gate.shape[-1]
    specular_start = branch_end
    specular_end = specular_start + specular_weight.shape[-1]
    transport_start = specular_end
    transport_end = transport_start + transport_feature.shape[-1]
    packed = torch.cat(
        [roughness, reflection_feature, branch_gate, specular_weight, transport_feature],
        dim=-1,
    )
    return packed, {
        "rasterize_branch_maps": True,
        "roughness": (0, 1),
        "reflection_feature": (feature_start, feature_end),
        "branch_gate": (branch_start, branch_end),
        "specular_weight": (specular_start, specular_end),
        "transport_feature": (transport_start, transport_end),
    }


def _slice_or_default(feature_map, start, end, default):
    if feature_map.shape[-1] >= end:
        return feature_map[..., start:end]
    return default


def unpack_srd_raster_maps(
    feature_map,
    gsfeat_dim,
    transport_dim,
    rasterize_branch_maps=False,
    use_branch_gate_requested=False,
):
    feature_end = 1 + gsfeat_dim
    default_scalar = torch.ones_like(feature_map[..., :1])
    default_transport = torch.zeros(
        feature_map.shape[0],
        feature_map.shape[1],
        transport_dim,
        dtype=feature_map.dtype,
        device=feature_map.device,
    )
    if rasterize_branch_maps:
        expected_channels = feature_end + 2 + transport_dim
        branch_gate = _slice_or_default(feature_map, feature_end, feature_end + 1, default_scalar)
        specular_weight = _slice_or_default(feature_map, feature_end + 1, feature_end + 2, default_scalar)
        transport_feature = _slice_or_default(
            feature_map,
            feature_end + 2,
            expected_channels,
            default_transport,
        )
        policy = get_srd_branch_map_policy(
            use_branch_gate_requested=use_branch_gate_requested,
            rasterize_branch_maps=feature_map.shape[-1] >= expected_channels,
        )
    else:
        branch_gate = default_scalar
        specular_weight = default_scalar
        transport_feature = default_transport
        policy = get_srd_branch_map_policy(use_branch_gate_requested=use_branch_gate_requested)

    return {
        "branch_gate_map": branch_gate,
        "specular_weight_map": specular_weight,
        "transport_feature_map": transport_feature,
    }, policy
