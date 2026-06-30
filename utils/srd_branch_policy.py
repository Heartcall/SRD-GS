def get_srd_branch_map_policy(use_branch_gate_requested=False, rasterize_branch_maps=False):
    if rasterize_branch_maps:
        return {
            "policy": "raster_feature_channels",
            "warning": (
                "Needs Runtime Verification: SRD branch maps are packed into "
                "the diff-surfel feature-channel path. CUDA backward support "
                "must be verified on a real training/render smoke."
            ),
            "use_branch_gate_requested": bool(use_branch_gate_requested),
            "gate_applied": bool(use_branch_gate_requested),
            "branch_gate_map": {
                "rasterized": True,
                "backward_to_gaussian": True,
                "fallback_value": None,
            },
            "specular_weight_map": {
                "rasterized": True,
                "backward_to_gaussian": True,
                "fallback_value": None,
            },
            "transport_feature_map": {
                "rasterized": True,
                "backward_to_gaussian": True,
                "fallback_value": None,
            },
        }
    return {
        "policy": "fallback_neutral_gate",
        "warning": (
            "Needs Runtime Verification: SRD branch maps are not rasterized by "
            "the current diff-surfel feature-channel path. Branch gate falls "
            "back to a neutral value so specular contribution is not suppressed."
        ),
        "use_branch_gate_requested": bool(use_branch_gate_requested),
        "gate_applied": False,
        "branch_gate_map": {
            "rasterized": False,
            "backward_to_gaussian": False,
            "fallback_value": 1.0,
        },
        "specular_weight_map": {
            "rasterized": False,
            "backward_to_gaussian": False,
            "fallback_value": 1.0,
        },
        "transport_feature_map": {
            "rasterized": False,
            "backward_to_gaussian": False,
            "fallback_value": 0.0,
        },
    }
