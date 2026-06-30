# Risk and Fallback

## Technical Risks
Risk: reflection branch absorbs geometry error.
Why it matters: branch may hide incorrect surface instead of protecting it.
Early diagnostic: compare surface-only depth/normal against GT or multi-view consistency; inspect residual maps.
Fallback: detach reflection gradients to geometry longer; add surface confidence and residual sparsity; constrain reflection branch to image residual only.

Risk: surface branch still bakes specular highlights.
Why it matters: albedo/texture maps remain unusable for relighting.
Early diagnostic: compute highlight leakage after Stage A and Stage C.
Fallback: strengthen residual-aware weights, use photometric variance masks, add direct albedo consistency, focus claim on normal/mesh if material remains weak.

Risk: geometry loss hurts rendering quality.
Why it matters: reviewers may reject if NVS drops too much.
Early diagnostic: plot PSNR/LPIPS vs normal MAE and mesh Chamfer.
Fallback: lower `lambda_geo`, use delayed normal loss, apply geometry loss only on high-confidence surface pixels.

Risk: branch separation causes reflection suppression.
Why it matters: highlights may become dull or blurred.
Early diagnostic: inspect specular residual energy and Refl-LPIPS.
Fallback: use roughness-dependent gate and only penalize residual outside specular masks.

Risk: codebase lacks robust mesh or texture export.
Why it matters: method depends on asset outputs.
Early diagnostic: import `utils/mesh_utils.py`, run mini extraction after repairing `utils.render_utils`.
Fallback: first implement surface-only depth/normal export and common external TSDF; defer UV baking to minimal albedo map export.

## Experimental Risks
Risk: lack of GT material prevents quantitative material evaluation.
Why it matters: material claims may be weak.
Early diagnostic: dataset audit for albedo/roughness/lighting GT.
Fallback: use custom Blender scenes for material GT; on real data report leakage/relighting proxies only.

Risk: dataset limitations.
Why it matters: reflective masks/GT may be absent or inconsistent.
Early diagnostic: check each dataset for mesh, normal, masks, materials before training.
Fallback: define a small synthetic diagnostic benchmark with full GT and use public real scenes qualitatively.

Risk: reflective-region masks are noisy.
Why it matters: metrics may be unfair.
Early diagnostic: visual mask QA and sensitivity analysis.
Fallback: report mask-free global metrics plus manually verified subset; use multiple mask thresholds.

## Novelty Risks
Risk: novelty overlaps with Ref-DGS dual representation.
Why it matters: reviewers may say the branch idea already exists.
Early diagnostic: compare method contribution against Ref-DGS paper/code.
Fallback: emphasize asset-level mesh/material export, transport consistency, and specular-free texture baking on Ref-GS; include Ref-DGS as baseline if runnable.

Risk: novelty overlaps with GS-IR/R3DG/IRGS inverse rendering.
Why it matters: material decomposition is crowded.
Early diagnostic: write a prior-work distinction table.
Fallback: focus on surface-only mesh extraction plus texture/material baking rather than full inverse rendering.

Risk: method becomes too complex for one paper.
Why it matters: implementation and ablation burden grows.
Early diagnostic: count modules required for minimal claim.
Fallback: minimal publishable version: branch decoupling + surface-only mesh + albedo de-specularization + reflective metrics; leave full metallic/F0/local reflection as future work.

## Reviewer Concerns
Risk: improvements are due to more parameters.
Why it matters: representation claim may be weak.
Early diagnostic: parameter-matched baseline with larger Ref-GS feature/MLP.
Fallback: include parameter-count control and all-branch mesh ablation.

Risk: physical consistency is not truly physical.
Why it matters: overclaimed theory.
Early diagnostic: identify exactly which variables are constrained.
Fallback: call it `physically motivated` not `physically exact`; include naive RGB consistency negative control.

Risk: relighting claims unsupported.
Why it matters: PBR material mapping requires validation.
Early diagnostic: verify novel-light GT.
Fallback: use bounded claim: specular-free texture/material proxy, not full relightable material recovery.

## Fallback Method Variants
1. Minimal branch-gated Ref-GS: shared Gaussian support, separate diffuse/specular attributes, surface-only mesh.
2. Texture-only extension: train Ref-GS normally, then residual-aware specular-free baking.
3. Geometry-only extension: detach specular path from geometry and evaluate mesh/normal, no full PBR export.
4. Benchmark/protocol paper: if method gains are small, package reflective-region mesh/material metrics and diagnostics.

## Minimal Publishable Version
Potential Hypothesis: A bounded but publishable version can target:
- Ref-GS public code extension;
- branch separation with shared support;
- surface-only mesh extraction;
- specular-free albedo/roughness/normal baking;
- reflective-region geometry and leakage metrics;
- ablations against Ref-GS, 2DGS and naive consistency.

No claim should be made about universal SOTA or fully accurate BRDF unless experiments prove it.
