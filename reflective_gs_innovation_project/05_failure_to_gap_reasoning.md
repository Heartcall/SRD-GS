# Failure-to-Gap Reasoning

## Observed Failure
Derived Analysis: Existing method `Ref-GS` improves reflective 2DGS rendering and geometry-aware appearance, but it can still fail for asset reconstruction under strong glossy / mirror-like regions because the same geometry-bearing Gaussians store surface support, albedo/roughness, feature maps and specular directional output.

Concrete formulation:

`Ref-GS improves reflective NVS and directional factorization, but it still lacks an explicit mechanism that prevents view-dependent specular residual from influencing mesh-bearing surface Gaussians. This can cause reflection-shaped geometry/normal artifacts and baked highlights in albedo-like outputs, preventing reliable mesh extraction and PBR material mapping.`

## Root Cause
- From Literature: Reflective surfaces violate diffuse multi-view consistency because specular color varies with viewpoint (`Ref-NeRF`, `NeRFReN`, `NeRO`).
- From Code Inspection: In Ref-GS, `render()` rasterizes the same `means3D`, `opacity`, `scales`, `rotations` for albedo, roughness/features, alpha, normals and depth (`external_repos/Ref-GS/gaussian_renderer/__init__.py:75-100`).
- From Code Inspection: The final reconstruction loss is applied to `pbr_rgb`, which equals `linear2srgb(spec_light + diff_light)` (`gaussian_renderer/__init__.py:163-174`; `train.py:82-85`).
- Derived Analysis: Because gradients from `pbr_rgb` can update geometry-bearing variables, specular residual can still shape opacity/position/normal indirectly.

## Baseline Limitation
From Code Inspection:
- no `G_surface` / `G_reflection` branch in `GaussianModel`.
- no explicit reflection residual branch that is excluded from mesh extraction.
- no `diffuse_consistency_loss`, `branch_separation_loss`, `reflection_transport_consistency_loss`, or `texture_de_specularization_loss`.
- mesh extraction utility consumes rendered RGB/depth/normal, not a protected surface-only output (`utils/mesh_utils.py:90-172`).
- UV/PBR material export is not implemented in baseline.

## Technical Contradiction
Derived Analysis: The baseline wants one representation to satisfy two incompatible requirements:

1. Surface branch requirement: stable, view-independent geometry and material variables for mesh extraction and texture/material maps.
2. Reflection branch requirement: high-frequency, view-dependent specular residual for realistic rendering.

Potential Hypothesis: If both requirements share the same opacity/position/normal support, photometric optimization can reward geometry distortions that explain highlights. A separate reflection branch should explain view-dependent residual without contributing to mesh opacity or surface extraction.

## Research Gap
Derived Analysis: Current public-code reflective GS baselines do not fully provide an asset-oriented pipeline where:

- mesh is extracted only from a protected surface representation;
- albedo/roughness/normal maps are baked without specular highlights;
- specular residual is modeled by a separate view-dependent transport branch;
- consistency is applied to stable variables, not raw specular RGB;
- experiments explicitly measure reflective-region mesh/material failures.

## Proposed Hypothesis
Potential Hypothesis: `SRD-GS` can improve reflective asset reconstruction by decomposing Ref-GS into:

- `G_surface`: surface 2D Gaussians for geometry, depth, normal, diffuse albedo and mesh/material export.
- `G_reflection`: reflection transport/residual Gaussians or feature field for view-dependent specular residual, excluded from mesh extraction.

Expected measurable effects:
- lower reflective-region normal MAE;
- lower reflective-region mesh Chamfer / higher F-score;
- fewer floating Gaussians near reflective surfaces;
- lower albedo highlight leakage;
- better relighting PSNR/LPIPS when material GT or novel-light GT is available;
- competitive global PSNR/SSIM/LPIPS.

## Why This Gap Is Worth Solving
Derived Analysis: A top-tier paper needs a gap that is not only aesthetic. Reflective asset reconstruction fails when geometry and material maps are polluted; this blocks downstream editing, relighting, AR/game asset use and robotics perception. The proposed gap is falsifiable because it can be tested with mesh metrics, material/texture metrics and failure-case visualizations.

## Evidence from Literature
- From Literature: 2DGS shows surface-oriented primitives are better for geometry than 3DGS (`https://arxiv.org/abs/2403.17888`).
- From Literature: Ref-NeRF and Ref-GS support reflection-direction modeling rather than raw view-direction color fitting (`https://arxiv.org/abs/2112.03907`, `https://arxiv.org/abs/2412.00905`).
- From Literature: NeRFReN supports layer/branch separation as a way to avoid treating reflected content as real geometry (`https://arxiv.org/abs/2111.15234`).
- From Literature: Texture-GS motivates texture output from GS but does not solve specular-free PBR material maps by itself (`https://arxiv.org/abs/2403.10050`).
- From Literature: Ref-DGS supports the general idea of dual geometry/reflection Gaussians, but mesh/material export still needs verification (`https://arxiv.org/abs/2603.07664`).

## Evidence from Code Inspection
- From Code Inspection: `GaussianModel` stores `_albedo`, `_roughness`, `_mask`, `_language_feature` on the same object as `_xyz`, `_scaling`, `_rotation`, `_opacity` (`scene/gaussian_model.py:97-144`, `:229-280`).
- From Code Inspection: `render()` computes `spec_light` and `diff_light`, then merges them into `pbr_rgb` (`gaussian_renderer/__init__.py:151-174`).
- From Code Inspection: `train.py` optimizes `pbr_rgb` with photometric loss and normal-depth loss, but not branch separation or material consistency (`train.py:82-102`).
- From Code Inspection: `GaussianExtractor` uses render outputs for TSDF mesh extraction and does not expose a surface-only branch (`utils/mesh_utils.py:90-172`).

## Expected Failure Cases
| Failure | Expected cause | Baseline behavior | Proposed method behavior | Metric / visualization | Supporting result | Refuting result |
|---|---|---|---|---|---|---|
| specular highlight baked into texture | albedo receives view-dependent residual | albedo-like map has bright streaks | surface albedo excludes residual | highlight leakage, albedo map | leakage lower than Ref-GS | leakage unchanged |
| reflection mistaken as geometry | RGB loss changes normals/opacity | mesh dents follow reflected pattern | reflection branch explains residual | normal MAE, Chamfer, mesh overlay | lower reflective Chamfer | mesh no better or worse |
| floating Gaussians | densification fits reflection | off-surface points near highlights | reflection branch constrained off mesh | Gaussian depth distribution | fewer off-surface Gaussians | same distribution |
| noisy normal/depth | specular gradients bias geometry | unstable reflection direction | normal-depth + transport consistency | normal/depth maps | lower Refl-Normal-MAE | normal oversmoothed |
| high PSNR poor mesh | appearance capacity hides geometry errors | rendering improves but mesh fails | mesh/material metrics improve | NVS + geometry table | mesh improves at similar PSNR | only PSNR improves |
| naive consistency blur | enforces specular RGB equality | highlights blurred/suppressed | consistency on material/transport | RGB consistency ablation | transport > RGB consistency | RGB consistency equals/better |
