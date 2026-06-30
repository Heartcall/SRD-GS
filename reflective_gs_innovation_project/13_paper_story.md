# Paper Story

## Title Candidates
1. `Surface-Reflection Decoupled Gaussian Splatting for Reflective Mesh Reconstruction and PBR Material Mapping`
2. `Specular-Free Reflective Gaussian Splatting for Mesh and Material Asset Reconstruction`
3. `From Reflective Gaussian Rendering to Relightable Assets via Surface-Reflection Decoupling`

## Abstract Draft
Reflective objects remain difficult for Gaussian Splatting because the image evidence used for high-fidelity rendering is not the same evidence needed for stable surface and material reconstruction. Existing reflective GS methods improve novel-view rendering by modeling view-dependent appearance, but the resulting Gaussian attributes can still entangle specular transport with mesh-bearing geometry and diffuse texture. We propose `SRD-GS`, a surface-reflection decoupled Gaussian framework that assigns geometry, normals and diffuse/PBR material maps to a protected surface branch, while a separate reflection branch models view-dependent residual transport and is excluded from mesh extraction. The method combines surface-only geometry optimization, reflection-transport consistency over physically stable variables, and robust specular-free texture baking. The hypothesis is evaluated through reflective-region mesh, normal, texture leakage and relighting metrics, in addition to standard PSNR/SSIM/LPIPS. This design turns reflective GS from a view synthesis representation into a testable mesh/material asset pipeline, with explicit limitations where GT material or lighting is unavailable.

## Core Motivation
From Literature: GS is efficient and high fidelity for novel-view synthesis. Reflective objects require geometry, material and reflection reasoning because specular appearance is view-dependent.

Derived Analysis: The failure that matters for asset reconstruction is not only poor rendering; it is wrong mesh, unstable normal and baked highlight in albedo.

## Problem Statement
Existing reflective GS methods improve rendering but can still entangle specular appearance with geometry or material. This harms mesh extraction and texture/material mapping.

## Key Insight
Potential Hypothesis: View-dependent reflection should not be stored in geometry-bearing Gaussians. Consistency should be applied to physically stable variables such as normal, roughness, albedo and transport features, not raw specular RGB.

## Method Story
The method starts from Ref-GS because Ref-GS already provides 2DGS surface rendering and reflection-direction factorization. SRD-GS changes the representation contract: `G_surface` is responsible for geometry, mesh and material maps; `G_reflection` is responsible for view-dependent residual. Training proceeds in stages so geometry is stabilized before reflection residual and material export. Mesh extraction uses `G_surface` only. Texture/material maps are baked from diffuse/material buffers with residual-aware weights so highlights are not baked into albedo.

## Contribution Statement
1. A surface-reflection decoupled Gaussian representation for reflective mesh/material reconstruction.
2. A physically motivated reflection-transport consistency that avoids naive specular RGB equality.
3. A specular-free mesh and PBR material export path from Gaussian assets.
4. A reflective-region evaluation protocol for geometry, mesh, texture/material and relighting.

Each contribution is measurable and can be refuted by targeted ablation.

## Why Reviewers Should Care
Derived Analysis: Reflective GS has rapidly improved visual quality, but production/robotics/AR use requires editable mesh and material assets. A method that improves rendering while leaving mesh/material contaminated does not solve the full reconstruction task. SRD-GS gives the field a stricter and more useful target.

## Expected Figures
1. Failure motivation: Ref-GS render looks good but mesh/albedo fails in reflective regions.
2. Pipeline diagram: surface branch, reflection branch, losses, mesh/material export.
3. Quantitative table: global NVS vs reflective geometry/material metrics.
4. Ablation table: branch/loss/stage contributions.
5. Texture panel: direct RGB baking vs specular-free baking.
6. Relighting panel: exported PBR maps under novel illumination.
7. Failure case panel: floating Gaussians, noisy normal, holes, highlight leakage.

## Paper Outline
1. Introduction: GS efficiency, reflective asset challenge, problem of entanglement.
2. Related Work: surface GS, reflective GS, inverse rendering, texture/material mapping.
3. Method: representation, rendering, losses, staged training, mesh/material export.
4. Experiments: baselines, datasets, metrics, main results, ablations.
5. Discussion: assumptions, limitations, real-scene risk, future work.

## Claim-Evidence Boundary
- Can claim after experiments: improved reflective-region mesh/material metrics if measured.
- Cannot claim now: state-of-the-art performance, universal material correctness, fully physical lighting recovery.
- Needs Verification: all numerical results and venue/code status for some 2025/2026 works.
