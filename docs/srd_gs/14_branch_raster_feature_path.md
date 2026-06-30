# Milestone 14: Branch-map Raster Feature Path

## Status

Status: implementation GO for an explicit branch-map raster feature path; runtime claim remains `Needs Runtime Verification`.

This milestone adds a feature-flagged path that packs SRD branch maps into the existing diff-surfel feature-channel rasterization input. It does not replace the conservative default config and does not claim CUDA backward support until a real training/render smoke verifies it.

## Changed Files

- `arguments/__init__.py`
- `scene/gaussian_model.py`
- `gaussian_renderer/__init__.py`
- `utils/srd_branch_policy.py`
- `tests/test_ablation_system_contract.py`
- `tests/test_srd_gaussian_model_static.py`
- `tests/test_srd_render_contract_static.py`

## New Files

- `utils/srd_branch_maps.py`
- `tests/test_srd_branch_raster_features.py`
- `configs/srd_gs/full_srd_gs_branch_raster.yaml`
- `docs/srd_gs/14_branch_raster_feature_path.md`

## Implementation

New CLI flag:

```text
--srd_rasterize_branch_maps
```

Default:

```text
False
```

When disabled, SRD-GS keeps the previous neutral fallback behavior:

```text
branch_gate_map: 1.0
specular_weight_map: 1.0
transport_feature_map: 0.0
```

When enabled, `gaussian_renderer.render()` calls `pack_srd_raster_features()` to concatenate:

```text
roughness
reflection_feature
branch_gate
specular_weight
transport_feature
```

into `language_feature_precomp`. After rasterization, `unpack_srd_raster_maps()` slices the output feature tensor back into:

```text
branch_gate_map
specular_weight_map
transport_feature_map
```

If the rasterizer output does not contain the expected extra channels, unpacking falls back to neutral maps and the policy reports fallback status.

## New Config

```text
configs/srd_gs/full_srd_gs_branch_raster.yaml
```

The dry-run train command contains:

```text
--enable_srd_gs --srd_rasterize_branch_maps --srd_use_branch_gate
```

The existing `configs/srd_gs/full_srd_gs.yaml` remains conservative and does not enable branch-map rasterization.

## Claim Boundary

Supported:

```text
The codebase now has an explicit, feature-flagged path for packing SRD branch-gate, specular-weight, and transport-feature tensors into rasterized feature channels.
```

Not yet supported:

```text
The CUDA rasterizer backward pass has been proven to propagate gradients to SRD branch maps.
SRD branch-map rasterization improves geometry/material metrics.
Paper-scale SRD-GS claims are allowed.
```

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_srd_branch_raster_features tests.test_srd_gaussian_model_static tests.test_srd_branch_map_fallback_policy tests.test_srd_render_contract_static
conda run -n ref_gs python -m unittest tests.test_ablation_system_contract
scripts/srd_gs/run_one_scene.sh --config configs/srd_gs/full_srd_gs_branch_raster.yaml --source_path /tmp/srd_dummy_scene --output_root /tmp/srd_branch_raster_dryrun --scene_name dummy --iterations 10
```

Result:

- focused branch raster tests: passed, 16 tests.
- ablation config contract: passed, 3 tests.
- dry-run command generation: passed.

## Needs Runtime Verification

- Run a bounded CUDA render/training smoke with `--srd_rasterize_branch_maps`.
- Inspect `srd_branch_map_policy` in exported render manifests.
- Confirm branch map tensors are non-fallback and do not crash CUDA backward.
- Only after that, compare accepted-GT geometry metrics against fallback full SRD-GS.

## Next Recommended Milestone

Milestone 15 should be a bounded single-scene branch-raster smoke, preferably on `ball` with `eval=True`, short iterations, accepted GT mesh metrics, and no paper-scale claim upgrade.
