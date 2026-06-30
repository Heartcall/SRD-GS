# SRD-GS Training Losses and Stage Schedule

## Scope

本文件记录 Milestone 4。当前阶段实现 SRD-GS 的基础 loss、`train.py` staged training hook 和日志字段。未运行真实训练，未修改 mesh extraction，未实现 texture baking。

## Repository

- Repository path: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Branch: `srd-gs-dev`
- Conda env used for verification: `ref_gs`

## Files Modified

- `utils/loss_utils.py`
- `train.py`
- `arguments/__init__.py`

`train-NeRF.py`、`train-NeRO.py`、`train-real.py` 本阶段未接入 SRD loss；它们保持 baseline 兼容，后续如果需要多入口训练再做轻量适配。

## New Loss Functions

Added in `utils/loss_utils.py`:

- `branch_separation_loss(branch_gate_map, specular_weight_map, confidence=None)`
  - Input tensors: branch gate and specular weight maps.
  - Output: scalar overlap penalty.
  - Differentiability: differentiable w.r.t. both inputs.
  - Application level: per-pixel SRD renderer buffers.
  - Stage: Stage B and Stage C.
  - Risk: high weight can suppress valid glossy reflections.

- `material_consistency_loss(material, reference_material, confidence=None)`
  - Input tensors: material buffers such as surface/diffuse RGB or roughness maps.
  - Output: scalar L1 consistency loss.
  - Differentiability: differentiable w.r.t. material and reference tensors.
  - Application level: per-pixel or per-texel material buffers.
  - Stage: Stage B and Stage C.
  - Risk: invalid references can over-smooth material.

- `transport_consistency_loss(transport_feature, reference_feature=None, confidence=None)`
  - Input tensors: reflection transport feature and optional reference feature.
  - Output: scalar feature consistency or spatial smoothness proxy.
  - Differentiability: differentiable w.r.t. transport feature and reference feature when provided.
  - Application level: per-pixel reflection transport features.
  - Stage: Stage B and Stage C.
  - Risk: spatial smoothness is only a proxy until visibility-aware correspondence is implemented.

- `highlight_leakage_loss(diffuse_rgb, specular_rgb, branch_gate_map, confidence=None)`
  - Input tensors: diffuse RGB, specular RGB, branch gate map.
  - Output: scalar proxy penalty for specular highlight leakage into diffuse output.
  - Differentiability: differentiable w.r.t. diffuse and specular RGB.
  - Application level: per-pixel rendered buffers.
  - Stage: Stage C.
  - Risk: inaccurate specular prediction can suppress valid diffuse texture.

- `specular_sparsity_loss(specular_rgb, confidence=None)`
  - Input tensors: specular RGB and optional confidence mask.
  - Output: scalar L1 sparsity loss.
  - Differentiability: differentiable w.r.t. specular RGB.
  - Application level: per-pixel rendered specular residual.
  - Stage: Stage B and Stage C.
  - Risk: excessive sparsity can underfit broad glossy lobes.

## Stage Schedule

Added in `train.py`:

- `get_srd_training_stage(dataset, iteration)`
- `should_apply_srd_losses(dataset, iteration)`

Behavior:

- `enable_srd_gs=False`: `baseline`, no SRD losses.
- `enable_srd_gs=True`, `srd_stage=0`: automatic schedule.
- `iteration <= srd_reflection_warmup`: `stage_a`.
- `srd_reflection_warmup < iteration <= 2 * srd_reflection_warmup`: `stage_b`.
- later iterations: `stage_c`.
- manual `srd_stage=1/2/3` overrides automatic schedule.

## Training Integration

In `train.py::training()`:

- Existing `loss_pbr`, alpha loss, normal loss, distance loss remain.
- SRD losses are only added when `should_apply_srd_losses(dataset, iteration)` is true.
- Stage A keeps the baseline geometry/photo path without SRD residual losses.
- Stage B adds separation, transport, material, and specular sparsity losses.
- Stage C additionally adds highlight leakage / texture proxy loss.

## New Optimization Parameters

Added in `arguments/__init__.py::OptimizationParams`:

- `lambda_srd_sep = 0.02`
- `lambda_srd_ref = 0.01`
- `lambda_srd_mat = 0.01`
- `lambda_srd_tex = 0.01`
- `lambda_srd_sparsity = 0.005`

These values are initial defaults only and require tuning.

## Logging Fields

Added TensorBoard/progress fields in `train.py`:

- `loss_photo`
- `loss_geo`
- `loss_sep`
- `loss_ref`
- `loss_mat`
- `loss_tex`
- `specular_energy`
- `branch_gate_mean`
- `surface_alpha_mean`

## Tests Run

```bash
conda run -n ref_gs python -m unittest tests.test_srd_losses
conda run -n ref_gs python -m unittest tests.test_srd_stage_schedule
conda run -n ref_gs python -m unittest discover -s tests
conda run -n ref_gs python -m py_compile utils/loss_utils.py train.py arguments/__init__.py
```

## Tests Passed

- `tests.test_srd_losses`: passed
- `tests.test_srd_stage_schedule`: passed
- full unittest discovery: passed, 21 tests
- py_compile for changed training/loss/argument files: passed

## Tests Failed

None after implementation.

## Needs Runtime Verification

- Real `train.py` smoke run with `--enable_srd_gs`.
- Stage A/B/C transition during actual training.
- Whether SRD losses are numerically stable with real renderer buffers.
- Whether `highlight_leakage_loss` suppresses true diffuse texture on glossy objects.
- Whether loss weights need scene-specific tuning.
- `train-NeRF.py`, `train-NeRO.py`, and `train-real.py` SRD training compatibility.

## Not Implemented in Milestone 4

- Visibility-aware multi-view transport correspondence.
- Surface-only mesh extraction.
- Texture baking and PBR export.
- Real experiment execution.
