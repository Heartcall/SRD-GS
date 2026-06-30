# Proposed Method

## Method Name
`SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping`

## One-sentence Summary
Potential Hypothesis: `SRD-GS` extends Ref-GS by separating geometry-bearing surface Gaussians from view-dependent reflection transport, so mesh and UV/PBR material maps are exported from a specular-free surface branch while a reflection branch explains specular residual for rendering.

## Target Problem
Derived Analysis: Ref-GS improves reflective rendering, but its public code stores surface support, albedo/roughness, directional feature and specular rendering in one Gaussian set. This leaves an asset-level gap: reflective geometry and texture/material maps may still be polluted by view-dependent specular transport.

## Core Hypothesis
Potential Hypothesis: If view-dependent specular residual is represented by a branch that is forbidden to contribute to mesh extraction, and cross-view constraints are applied to surface/material/transport variables rather than raw specular RGB, reflective-region mesh and albedo quality will improve without sacrificing competitive NVS.

## Main Contributions
Contribution 1: Surface-reflection decoupled Gaussian representation.
- Problem solved: view-dependent reflection can corrupt mesh-bearing Gaussians.
- Method: split Ref-GS into `G_surface` and `G_reflection`. `G_surface` stores position, scale, rotation, opacity, normal, diffuse albedo, roughness, material feature and mesh confidence. `G_reflection` stores view-dependent residual/transport features, local reflection support and specular weight, but has no mesh opacity.
- Why it works: surface support becomes view-independent, while specular residual has a designated view-dependent path.
- How to verify experimentally: compare all-Gaussian mesh extraction vs surface-only mesh extraction; report reflective Chamfer/F-score/normal MAE and floating Gaussian counts.

Contribution 2: Reflection-transport consistency instead of specular RGB consistency.
- Problem solved: naive cross-view equality of specular RGB is physically invalid.
- Method: enforce consistency over `normal`, `roughness`, `albedo`, `reflection direction` and `transport feature` only for visibility-validated correspondences. Raw specular RGB consistency is included only as a negative ablation.
- Why it works: material and geometry variables are stable for a surface point, while specular RGB changes with view.
- How to verify experimentally: ablate no consistency / naive RGB consistency / transport consistency; measure Refl-LPIPS, normal MAE, mesh metrics and highlight sharpness.

Contribution 3: Specular-free texture and PBR material export.
- Problem solved: texture baking can bake highlights into albedo.
- Method: after mesh extraction from `G_surface`, bake UV maps by robustly aggregating surface-branch diffuse predictions and downweighting pixels with high reflection residual or high view-dependent variance. Export albedo, roughness, normal, optional metallic/specular/F0 and residual/specular mask maps.
- Why it works: texel values are estimated from view-independent diffuse/material fields rather than final RGB.
- How to verify experimentally: highlight leakage score, relighting PSNR/LPIPS if novel-light GT exists, albedo error where GT exists, and external renderer qualitative panels.

Contribution 4: Asset-level reflective evaluation protocol.
- Problem solved: global rendering metrics hide mesh/material failures.
- Method: report global NVS, reflective-region NVS, geometry, mesh, texture/material and relighting metrics, with explicit supporting/refuting conditions.
- Why it works: the evaluation matches the method claim rather than only image fitting.
- How to verify experimentally: show cases where baseline PSNR is competitive but mesh/material metrics fail; proposed method should improve targeted asset metrics.

## Method Overview
### Representation Design
Potential Hypothesis:
- `G_surface = {x, s, R, alpha_s, n_s, rho_d, roughness, metallic/F0 optional, f_mat, c_mesh}`
- `G_reflection = {x_r or tied x_s, alpha_r_nonmesh, f_ref, w_ref, local_reflection_feature, uncertainty}`

`G_reflection` can either share projected support with `G_surface` through a per-surface branch gate or use a sparse residual Gaussian/cache. The first implementation should use shared support plus extra branch attributes to minimize code disruption.

### Rendering Pipeline
Potential Hypothesis:
1. Rasterize `G_surface` to get `alpha_s`, `surf_depth`, `n_s`, `rho_d`, `roughness`, `f_mat`.
2. Compute reflection direction `r = 2(n_s dot v)n_s - v`.
3. Query Ref-GS-style `SphMipEncoding(r, roughness)` and a reflection transport feature.
4. Predict `S(x,v)` from `G_reflection`.
5. Compose `I_hat = D_surface + g_ref * S_reflection`, where `D_surface` is diffuse/PBR base and `g_ref` is a learned reflection gate.

### Geometry Modeling
Potential Hypothesis:
- Mesh extraction uses only `G_surface` depth/normal/opacity.
- Normal-depth consistency applies only to `G_surface`.
- Reflection branch gradients to `surface xyz/scale/rotation/opacity` are delayed or detached in early stages.

### Reflection / Specular Modeling
Potential Hypothesis:
- Ref-GS `SphMipEncoding` is retained as the directional backbone.
- `G_reflection` adds residual transport capacity for high-frequency/near-field reflection.
- The model never enforces `S(x,v1) = S(x,v2)` directly.

### Material / BRDF / Lighting Modeling
Potential Hypothesis:
- Minimal publishable version: diffuse albedo, roughness, normal, specular weight.
- Full version: add metallic/F0 and environment/local reflection feature.
- Lighting is not claimed as fully recovered unless relighting GT or controlled illumination exists.

### Loss Design
Potential Hypothesis:
- `L_photo`: final RGB reconstruction.
- `L_geo`: normal-depth consistency and optional depth/mask consistency on `G_surface`.
- `L_sep`: branch separation and residual sparsity.
- `L_ref`: reflection transport consistency on stable variables/features.
- `L_mat`: albedo/roughness/material cross-view consistency.
- `L_tex`: texture de-specularization after mesh/UV baking.

### Training Strategy
Potential Hypothesis:
1. Stage A geometry warm-up: train `G_surface` with geometry/diffuse losses, weak or disabled reflection branch.
2. Stage B reflection residual: enable `G_reflection`, freeze or damp geometry gradients from specular path.
3. Stage C material/texture fine-tuning: optimize surface material maps and texel consistency; keep mesh extraction branch stable.

### Mesh Extraction Path
Potential Hypothesis: Replace baseline `GaussianExtractor` usage with `surface_only=True`, where `render_surface()` returns `surface_rgb`, `surface_alpha`, `surface_depth`, `surface_normal`. TSDF/Poisson/2DGS extraction uses only this branch.

### Texture / Material Output Path
Potential Hypothesis: Add `utils/texture_baking.py`:
- project mesh texels to training views;
- sample diffuse albedo, roughness and normal;
- weight views by visibility, grazing angle, alpha, residual specular probability and reprojection confidence;
- export `albedo.png`, `roughness.png`, `normal.png`, optional `specular_weight.png`, and `highlight_leakage_mask.png`.

## Relation to Selected Baseline
From Code Inspection: Ref-GS already provides `SphMipEncoding`, `light_mlp`, `albedo`, `roughness`, reflection direction and `pbr_rgb`; SRD-GS reuses these modules but changes branch responsibility and output path.

## Key Difference from Prior Work
Derived Analysis: Compared with Ref-GS, the novelty is not another directional encoding; it is an asset-oriented separation rule: specular residual branch is explicitly excluded from mesh/material export. Compared with Texture-GS, it is not generic texture editing; it targets specular-free PBR map export. Compared with Ref-DGS, it anchors the separation to mesh/material metrics and Ref-GS public code.

## Why It Is Novel
Potential Hypothesis: The method combines three pieces that are individually present in prior art but not fully integrated in Ref-GS public-code context: surface-only mesh branch, physically valid reflection-transport consistency, and specular-free PBR texture baking with reflective-region evaluation.

## Why It Is Feasible
From Code Inspection: Ref-GS already exposes the main insertion points:
- attributes and optimizer groups in `scene/gaussian_model.py`;
- directional renderer and buffers in `gaussian_renderer/__init__.py`;
- training losses in `train.py`;
- mesh extraction scaffolding in `utils/mesh_utils.py`.

Needs Verification: Feasibility requires repairing missing `utils.render_utils`, building CUDA extensions, and validating runtime memory on at least one scene.
