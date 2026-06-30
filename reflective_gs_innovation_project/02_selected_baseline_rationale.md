# Selected Baseline Rationale

## Selected Paper
`Ref-GS: Directional Factorization for 2D Gaussian Splatting`

- From Literature: arXiv `https://arxiv.org/abs/2412.00905` describes Ref-GS as directional light factorization for 2D Gaussian Splatting with deferred surface directional encoding, spherical Mip-grid, and geometry-lighting factorization.
- From Literature: GitHub README `https://github.com/YoujiaZhang/Ref-GS` marks it as `[CVPR 2025] Ref-GS : Directional Factorization for 2D Gaussian Splatting`.

## Selected Code Repository
`https://github.com/YoujiaZhang/Ref-GS`

- From Code Inspection: cloned successfully to `external_repos/Ref-GS`.
- From Code Inspection: cloned commit `bf843b7 Update README.md`.
- From Code Inspection: cloned files match existing local checkout for `scene/gaussian_model.py`, `gaussian_renderer/__init__.py`, and `train.py`.

## Why This Baseline Is Suitable
- From Literature: It directly targets reflective / glossy 2DGS, not generic NVS.
- From Literature: It uses 2DGS-style surface representation, which is closer to mesh extraction than vanilla 3DGS.
- From Literature: README says mesh extraction follows 2DGS, so the code has an explicit route to geometry/mesh outputs.
- From Code Inspection: `scene/gaussian_model.py` contains `SphMipEncoding`, per-Gaussian `_albedo`, `_roughness`, `_mask`, `_language_feature`, and `light_mlp` (`external_repos/Ref-GS/scene/gaussian_model.py:97`, `:124`, `:130`, `:253-256`).
- From Code Inspection: `gaussian_renderer.render()` computes `wo = reflect(-viewdirs, normals)`, uses roughness as `spec_level`, queries `dir_encoding`, predicts `spec_light`, and combines `pbr_rgb = spec_light + diff_light` (`external_repos/Ref-GS/gaussian_renderer/__init__.py:125-173`).

## Why Its Limitation Matters
Derived Analysis: Ref-GS is an excellent reflective rendering baseline, but the code uses one Gaussian set for both surface-bearing attributes and reflection appearance. The same `means3D`, `opacity`, `scales`, and `rotations` drive rasterization for albedo/material-like maps, normals/depth, alpha, and specular rendering (`external_repos/Ref-GS/gaussian_renderer/__init__.py:75-100`). This creates a measurable risk: specular residual can still influence geometry-bearing primitives and downstream mesh extraction.

Derived Analysis: For an asset pipeline, final quality requires clean mesh and specular-free albedo/roughness/normal maps, not only `pbr_rgb` image quality. Ref-GS code saves per-Gaussian `albedo` and `roughness` into PLY (`external_repos/Ref-GS/scene/gaussian_model.py:324-351`), but does not export UV albedo/roughness/metallic/normal maps.

## Why This Limitation Is Not Fully Solved by Existing Work
- From Literature: SuGaR, GOF, 2DGS and Gaussian Surfels improve geometry/surface extraction, but are not reflective material decomposition methods.
- From Literature: GS-IR, R3DG, Ref-Gaussian, IRGS and GlossyGS model inverse rendering or inter-reflection, but many are not mesh/texture export pipelines and some code status is `Needs Verification`.
- From Literature: Texture-GS maps GS appearance to texture, but its abstract focuses on appearance editing and does not claim specular-free PBR material export.
- Derived Analysis: Ref-DGS is conceptually close because it has dual geometry/reflection Gaussians, but it is a 2026 arXiv preprint and its mesh/material export path needs verification. Ref-GS is a safer public-code anchor for an implementable CVPR-style extension.

## Comparison with Alternative Target Papers
| Candidate | Public Code | Relation | Why Not Selected as Main Target |
|---|---:|---|---|
| 2DGS | yes | surface geometry backbone | not reflective/material specific; would require adding reflection model from scratch. |
| SuGaR | yes | mesh extraction baseline | strong mesh target, but not designed around reflective view-dependent residual. |
| GS-IR | yes | inverse rendering / PBR | closer to material estimation, but 3DGS-based and mesh/UV export not central. |
| Texture-GS | Needs Verification | texture mapping | strong texture bridge, but not reflective-specific and code availability needs verification. |
| Ref-DGS | yes | dual reflective representation | very relevant, but preprint status and mesh/material export path need verification; Ref-GS is more stable as CVPR/public-code baseline. |
| EnvGS | Needs Verification | near-field/high-frequency reflection | reflection rendering focused; mesh/material export not central and code status uncertain. |

## Why It Is a Good Target for a New Paper
Potential Hypothesis: A new method can be implemented as a conservative extension of Ref-GS by adding an explicit `surface branch` and `reflection branch`, modifying renderer outputs to expose diffuse/specular/transport buffers, adding physically valid consistency losses, extracting mesh from surface branch only, and baking specular-free UV/PBR maps.

Derived Analysis: This target is paper-worthy because it turns a clear limitation into falsifiable asset-level claims: lower reflective-region normal MAE, lower reflective mesh Chamfer, fewer floating Gaussians near reflective surfaces, lower albedo highlight leakage, and better relighting, while maintaining competitive global NVS metrics.
