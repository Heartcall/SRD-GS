# Existing Methods and Limitations

## Route 1: Surface-oriented Gaussian Reconstruction
From Literature: 3DGS represents scenes with anisotropic 3D Gaussians and visibility-aware rasterization, but it is not an explicit surface representation (`https://arxiv.org/abs/2308.04079`).

From Literature: 2DGS replaces volumetric 3D blobs with oriented planar Gaussian disks and adds depth distortion / normal consistency to improve geometry (`https://arxiv.org/abs/2403.17888`).

From Literature: SuGaR introduces surface-aligned regularization and Poisson mesh extraction from 3DGS (`https://arxiv.org/abs/2311.12775`).

From Literature: GOF derives a Gaussian opacity field and adaptive Marching Tetrahedra for surface reconstruction (`https://arxiv.org/abs/2404.10772`).

Derived Analysis: These methods solve a representation mismatch for mesh extraction, but they do not by themselves decide whether high-frequency reflective signals should affect surface geometry. On reflective objects, surface-aligned primitives can still move, split, or densify to explain view-dependent highlights.

Derived Analysis: In reflective regions, likely artifacts include floating Gaussians, surface thickness, noisy normals, and mesh holes. These are not guaranteed to be visible in global PSNR/SSIM/LPIPS.

## Route 2: Reflective / View-dependent Gaussian Rendering
From Literature: Ref-NeRF shows that glossy appearance is better parameterized by reflected direction than raw view direction and uses normal regularization (`https://arxiv.org/abs/2112.03907`).

From Literature: GaussianShader applies shading functions to 3D Gaussians for reflective surfaces and emphasizes normal estimation (`https://arxiv.org/abs/2311.17977`).

From Literature: Ref-GS uses directional factorization on deferred 2DGS surface, spherical Mip-grid, and geometry-lighting factorization for reflective appearance (`https://arxiv.org/abs/2412.00905`, `https://github.com/YoujiaZhang/Ref-GS`).

From Literature: EnvGS models complex reflections through explicit environment Gaussian primitives and ray-tracing-assisted rendering (`https://arxiv.org/abs/2412.15215`).

From Literature: Ref-DGS proposes dual geometry Gaussians and local reflection Gaussians with global environment reflection field (`https://arxiv.org/abs/2603.07664`, `https://github.com/njfan/Ref-DGS`).

Derived Analysis: Directional encoding improves reflective rendering, but rendering improvement alone does not prove that the surface branch is cleaner for mesh/material export. If specular signal is still optimized through geometry-bearing opacity/position/normal, mesh quality can remain unstable.

Derived Analysis: Naive multi-view RGB/specular consistency is physically problematic because a specular highlight is view-dependent. For the same surface point, `S(x, v1) != S(x, v2)` in general. Consistency should be on normal, roughness, albedo, BRDF parameters, or a physically corresponding reflected-source feature.

## Route 3: Inverse Rendering and Material Decomposition
From Literature: NeRFactor recovers normals, light visibility, albedo, BRDF and environment lighting under unknown illumination using priors and re-rendering loss (`https://arxiv.org/abs/2106.01970`).

From Literature: NeRO reconstructs reflective object geometry and BRDF from multiview images with a staged process; it uses split-sum approximation and directional encoding, then fixes geometry for BRDF/light recovery (`https://arxiv.org/abs/2305.17398`).

From Literature: GS-IR extends 3DGS to inverse rendering and introduces depth-derived normal regularization and baking-based occlusion (`https://arxiv.org/abs/2311.16473`, `https://github.com/lzhnb/GS-IR`).

From Literature: R3DG associates normals, BRDF parameters and incident lighting with 3D Gaussians and uses point-based ray tracing visibility (`https://arxiv.org/abs/2311.16043`).

From Literature: IRGS introduces differentiable 2D Gaussian ray tracing for inter-reflective inverse rendering (`https://arxiv.org/abs/2412.15867`).

Derived Analysis: Material decomposition is underconstrained because albedo, roughness, metallic/F0, illumination and visibility can compensate for each other. Without GT material or multi-light supervision, claims should focus on measurable outcomes: relighting error, albedo highlight leakage, material consistency, and ablations, not on unverified semantic correctness.

Derived Analysis: View-independent variables should include geometry support, surface normal, diffuse albedo under fixed lighting approximation, roughness, metallic/F0, and UV material maps. View-dependent variables include specular radiance, reflected source appearance, visibility-conditioned incident light and local inter-reflection residual.

## Route 4: Mesh Extraction and Texture Baking
From Literature: SuGaR and GOF make mesh extraction a primary goal. 2DGS and Gaussian Surfels provide surface-like primitives and normal-depth consistency for geometry extraction.

From Literature: Texture-GS proposes UV mapping MLP and a learnable 2D texture to decouple geometry and texture for editing (`https://arxiv.org/abs/2403.10050`).

Derived Analysis: Mesh extraction often uses Gaussian geometry, alpha/depth, normal maps, opacity fields, TSDF fusion, Poisson reconstruction, or marching tetrahedra. If reflective residual is encoded into those attributes, mesh extraction can produce dents, bumps, floating pieces or holes in reflective regions.

Derived Analysis: Texture baking differs from material mapping. Texture baking may output a color texture tied to the training illumination. Material mapping should output PBR factors such as albedo, roughness, metallic/specular/F0 and normal maps. A baked highlight in albedo is a material failure even if training-view rendering is good.

Derived Analysis: Evaluation must include mesh Chamfer/F-score/normal MAE/depth error and texture/material metrics such as albedo error, highlight leakage and relighting. PSNR/SSIM/LPIPS alone are insufficient.

## Route 5: Multi-view Consistency and Regularization
From Literature: 2DGS and Gaussian Surfels use depth-normal consistency. GS-IR uses depth-derived normal regularization. Ref-GS builds on reflection direction and roughness-aware directional features.

Derived Analysis: Valid consistency constraints depend on the variable. Surface normal, depth, albedo, roughness and material maps are expected to be consistent for a surface point under fixed object geometry; specular RGB is not.

Potential Hypothesis: A reflection-transport consistency loss should compare physically stable variables or physically corresponding reflected-source features, with visibility/confidence masks. A naive loss `||S(x,v1)-S(x,v2)||` should be used only as a negative ablation because it can blur moving highlights.

## Summary of Key Limitations
1. From Literature: 3DGS/2DGS/SuGaR/GOF improve rendering or surface extraction but do not solve reflective material/transport separation.
2. From Literature: Ref-GS improves reflective 2DGS rendering and geometry recovery, but code inspection shows no explicit surface/reflection branch split for mesh/material export.
3. Derived Analysis: Existing methods often evaluate NVS more strongly than exported asset quality.
4. Derived Analysis: Texture mapping methods can bake specular highlights into albedo if they do not explicitly decompose view-dependent residual.
5. Potential Hypothesis: A method that protects mesh-bearing surface Gaussians from specular residual and exports specular-free material maps can address a distinct gap not fully covered by current public-code baselines.
