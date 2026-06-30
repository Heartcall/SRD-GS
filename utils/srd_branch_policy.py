def get_srd_branch_map_policy(use_branch_gate_requested=False):
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
