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


def pack_srd_raster_feature_chunks(
    roughness,
    reflection_feature,
    branch_gate,
    specular_weight,
    transport_feature,
    channel_limit,
):
    if channel_limit <= 0:
        raise ValueError("channel_limit must be positive")
    primary = torch.cat([roughness, reflection_feature], dim=-1)
    if primary.shape[-1] != channel_limit:
        raise ValueError(
            "primary_srd_raster_channel_mismatch:{}!={}".format(primary.shape[-1], channel_limit)
        )

    extra = torch.cat([branch_gate, specular_weight, transport_feature], dim=-1)
    chunks = []
    ranges = []
    for start in range(0, extra.shape[-1], channel_limit):
        end = min(start + channel_limit, extra.shape[-1])
        chunk = extra[..., start:end]
        if chunk.shape[-1] < channel_limit:
            pad = torch.zeros(
                chunk.shape[0],
                channel_limit - chunk.shape[-1],
                dtype=chunk.dtype,
                device=chunk.device,
            )
            chunk = torch.cat([chunk, pad], dim=-1)
        chunks.append(chunk)
        ranges.append((start, end))

    return primary, chunks, {
        "channel_limit": channel_limit,
        "extra_channel_count": extra.shape[-1],
        "extra_chunks": ranges,
        "branch_gate": (0, branch_gate.shape[-1]),
        "specular_weight": (
            branch_gate.shape[-1],
            branch_gate.shape[-1] + specular_weight.shape[-1],
        ),
        "transport_feature": (
            branch_gate.shape[-1] + specular_weight.shape[-1],
            extra.shape[-1],
        ),
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


def unpack_srd_raster_maps_from_chunks(
    primary_feature_map,
    extra_feature_maps,
    gsfeat_dim,
    transport_dim,
    chunk_metadata,
    use_branch_gate_requested=False,
):
    extras = []
    for feature_map, (start, end) in zip(extra_feature_maps, chunk_metadata["extra_chunks"]):
        extras.append(feature_map[..., : end - start])

    if extras:
        extra_map = torch.cat(extras, dim=-1)
    else:
        extra_map = torch.zeros(
            primary_feature_map.shape[0],
            primary_feature_map.shape[1],
            chunk_metadata["extra_channel_count"],
            dtype=primary_feature_map.dtype,
            device=primary_feature_map.device,
        )

    branch_start, branch_end = chunk_metadata["branch_gate"]
    specular_start, specular_end = chunk_metadata["specular_weight"]
    transport_start, transport_end = chunk_metadata["transport_feature"]
    branch_gate = extra_map[..., branch_start:branch_end]
    specular_weight = extra_map[..., specular_start:specular_end]
    transport_feature = extra_map[..., transport_start:transport_end]

    if transport_feature.shape[-1] < transport_dim:
        pad = torch.zeros(
            primary_feature_map.shape[0],
            primary_feature_map.shape[1],
            transport_dim - transport_feature.shape[-1],
            dtype=primary_feature_map.dtype,
            device=primary_feature_map.device,
        )
        transport_feature = torch.cat([transport_feature, pad], dim=-1)
    elif transport_feature.shape[-1] > transport_dim:
        transport_feature = transport_feature[..., :transport_dim]

    policy = get_srd_branch_map_policy(
        use_branch_gate_requested=use_branch_gate_requested,
        rasterize_branch_chunks=True,
    )
    return {
        "branch_gate_map": branch_gate,
        "specular_weight_map": specular_weight,
        "transport_feature_map": transport_feature,
    }, policy
