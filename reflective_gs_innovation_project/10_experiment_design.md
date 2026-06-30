# Experiment Design

## Main Comparison
Compared methods:
- 3DGS baseline.
- 2DGS baseline.
- SuGaR or GOF for mesh extraction.
- GS-IR / R3DG for inverse rendering where available.
- Texture-GS for texture mapping where available.
- Ref-GS selected baseline.
- Ref-DGS as a strong dual-representation comparator if runnable.
- proposed `SRD-GS`.

Hypothesis:
Potential Hypothesis: SRD-GS improves reflective-region mesh/material metrics while maintaining competitive rendering.

Experimental setup:
Train all baselines on the same scenes and use comparable train/test splits. Use same mesh extraction when possible; if method-specific extraction is used, report both native and common extraction protocols.

Metrics:
PSNR, SSIM, LPIPS, Refl-PSNR, Refl-LPIPS, Chamfer, F-score, normal MAE, depth error, highlight leakage, relighting PSNR/LPIPS, runtime/memory.

Expected supporting result:
SRD-GS has lower reflective Chamfer/normal MAE and lower albedo highlight leakage than Ref-GS, with similar global PSNR/SSIM/LPIPS.

Refuting result:
SRD-GS improves only PSNR or visual highlights but not mesh/material metrics.

Failure interpretation:
Branch separation did not isolate geometry or material-light ambiguity dominates.

## Geometry Evaluation
Hypothesis:
Surface-only branch improves mesh extraction in reflective regions.

Experimental setup:
Use scenes with GT mesh or point cloud; evaluate full mesh and reflective-mask subset. Extract mesh from Ref-GS unified output vs SRD-GS surface-only output.

Metrics:
Chamfer Distance, F-score, normal MAE, depth error, normal-depth consistency, floating Gaussian count near surface.

Expected supporting result:
Reflective-region Chamfer decreases and F-score increases; normal MAE decreases.

Refuting result:
Surface-only extraction is no better or creates holes.

Failure interpretation:
Reflection branch may have removed useful surface evidence or geometry warm-up locked wrong shape.

## Reflective Region Evaluation
Hypothesis:
Reflective-region metrics reveal improvements hidden by global metrics.

Experimental setup:
Use provided reflective masks if available; otherwise estimate masks from view variance/specular residual and manually validate a subset.

Metrics:
Refl-PSNR, Refl-SSIM, Refl-LPIPS, Refl-Normal-MAE, Refl-Mesh-Chamfer, reflection residual energy.

Expected supporting result:
SRD-GS improves reflective metrics more than global metrics.

Refuting result:
Gains occur only in diffuse regions or masks are unstable.

Failure interpretation:
Specular mask/correspondence protocol is insufficient.

## Texture / Material Evaluation
Hypothesis:
Specular-free baking reduces highlight leakage and improves relighting.

Experimental setup:
Export mesh and material maps from Ref-GS-like direct RGB baking, Texture-GS if available, and SRD-GS. Render under original and novel lighting in Blender or differentiable renderer.

Metrics:
Albedo MSE/PSNR if GT exists, roughness error if GT exists, highlight leakage score, material consistency across views, relighting PSNR/LPIPS.

Expected supporting result:
Lower highlight leakage and better relighting under novel light.

Refuting result:
Albedo maps still contain highlights or relighting error does not improve.

Failure interpretation:
Single-light ambiguity or residual mask failure.

## Real-world Generalization
Hypothesis:
Surface-reflection decoupling reduces typical real reflective artifacts under imperfect capture.

Experimental setup:
Use Shiny Blender Real / real glossy captures where camera poses and masks exist. No-GT evaluation uses visual panels, reflective consistency proxies and mesh diagnostics.

Metrics:
Visual mesh/normal/albedo panels, Refl-LPIPS if held-out views exist, proxy normal-depth consistency, hole count, highlight leakage.

Expected supporting result:
Cleaner mesh/albedo and fewer floating artifacts than Ref-GS.

Refuting result:
Method fails due calibration/mask errors or overfits synthetic assumptions.

Failure interpretation:
Need uncertainty-aware correspondences or local reflection modeling.

## Runtime and Memory
Hypothesis:
Shared-support reflection branch keeps overhead acceptable relative to Ref-GS.

Experimental setup:
Measure training time, peak GPU memory, render FPS and export time.

Metrics:
minutes/iterations, peak GB, FPS, number of Gaussians, texture export time.

Expected supporting result:
Overhead <= 1.5x for minimal branch version.

Refuting result:
Overhead too high for practical baseline comparison.

Failure interpretation:
Need reduce branch feature dimension or stage C offline baking.

## Qualitative Visualization
Panels:
- target image / baseline render / proposed render;
- baseline mesh / proposed mesh / GT mesh overlay;
- normal maps;
- albedo map with leakage heatmap;
- roughness/specular weight;
- specular residual branch;
- novel relighting.

Expected supporting result:
Artifacts match quantitative improvements and are localized to reflective failures.

Refuting result:
Visual differences are unrelated to claimed mechanism.

## What Results Would Support the Claim
- Lower reflective-region mesh Chamfer and normal MAE on multiple scenes.
- Lower albedo highlight leakage.
- Better or comparable relighting under novel illumination.
- Similar global PSNR/SSIM/LPIPS.
- Ablations show each component affects its targeted failure.

## What Results Would Refute the Claim
- Surface-only branch worsens mesh or creates holes.
- Reflection branch hides geometry errors.
- Direct RGB baking and proposed baking have equal leakage.
- Naive RGB consistency performs as well as transport consistency.
- Gains are not reproducible across scenes.

## Failure Case Evaluation
| Failure | Expected cause | Baseline behavior | Proposed method behavior | Metric / visualization | Supporting result | Refuting result |
|---|---|---|---|---|---|---|
| specular highlight baked into texture | final RGB used as texture | white streak fixed in albedo | residual removed before baking | leakage heatmap | lower leakage | unchanged leakage |
| reflection mistaken as geometry | photometric loss alters normals | dents/bumps follow reflection | surface branch protected | mesh overlay | lower Chamfer | worse mesh |
| floating Gaussians | densification fits reflection | off-surface points | non-mesh residual branch | point-depth histogram | fewer outliers | no reduction |
| unstable normal/depth | specular gradients | flickering normals | geometry loss + detach | normal video/MAE | lower MAE | oversmoothed normals |
| noisy mesh extraction | polluted opacity/depth | holes/noise | surface-only TSDF | hole count | fewer holes | more holes |
| albedo with baked highlight | view-dependent color in albedo | bright fixed texture | robust texel aggregation | albedo panel | clean albedo | same artifacts |
| rendering improves but mesh degrades | appearance overfit | high PSNR low F-score | asset losses | metric table | geometry improves | only PSNR improves |
| naive consistency wrong | specular RGB equality | blur/suppression | transport consistency | ablation panel | transport wins | RGB consistency wins |
