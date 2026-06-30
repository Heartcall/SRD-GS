# Theory Derivation

## Notation
Let `x` be a surface point, `v` the outgoing view direction toward camera, `n(x)` the surface normal, `rho(x)` diffuse albedo, `alpha_s` surface opacity, `m(x)` material parameters such as roughness and metallic/F0, and `T_ref(x, r)` a reflection transport feature indexed by reflection direction `r`.

Let `G_surface` denote geometry-bearing Gaussians and `G_reflection` denote view-dependent reflection residual / transport branch.

## Rendering Decomposition
From Literature: In reflective inverse rendering, outgoing radiance can be written as:

```math
L_o(x, v) =
\int_{\Omega} f_r(x, \omega_i, v) L_i(x, \omega_i) V(x, \omega_i)
(n_x \cdot \omega_i) d\omega_i.
```

Derived Analysis: For implementation on Ref-GS, use a practical decomposition:

```math
\hat I(p, v) = D_s(p) + g_r(p) S_r(p, v),
```

where `D_s` is the surface diffuse/PBR base rendered from `G_surface`, `S_r` is the reflection residual predicted by `G_reflection`, and `g_r` is a reflection gate.

Potential Hypothesis: Geometry should be optimized primarily through `D_s`, alpha/depth/normal and mesh consistency; view-dependent residual should be optimized through `S_r`.

## Gaussian Representation
Surface branch:

```text
G_surface:
  position x_s
  scale s_s
  rotation R_s
  opacity alpha_s
  normal n_s
  diffuse albedo rho_d
  roughness alpha_m
  optional metallic/F0
  material feature f_mat
  mesh confidence c_mesh
```

Reflection branch:

```text
G_reflection:
  tied or residual position x_r
  non-mesh opacity alpha_r
  reflection feature f_ref
  specular weight w_ref
  transport feature T_ref
  uncertainty u_ref
```

Potential Hypothesis: Initial implementation should tie `x_r` to `x_s` through shared rasterized support and add reflection attributes to reduce complexity. A later version may use separate sparse residual Gaussians.

## Surface / Reflection Separation
Define:

```math
D_s = R_s(G_surface; \rho, n, roughness)
```

```math
S_r = R_r(G_surface, G_reflection; r, roughness, T_ref)
```

Only `G_surface` is used for:
- mesh extraction;
- UV unwrapping;
- diffuse albedo / roughness / normal map baking.

`G_reflection` is forbidden from:
- increasing mesh opacity;
- entering TSDF/Poisson/marching extraction;
- being baked into diffuse texture.

## Reflection Direction
For a surface normal `n` and outgoing view direction `v`, define reflected direction:

```math
r = 2(n \cdot v)n - v.
```

From Literature: Ref-NeRF and Ref-GS motivate reflection-direction parameterization for glossy/view-dependent appearance.

Derived Analysis: Wrong normal causes wrong `r`, so reflective rendering quality is coupled to normal quality. This means a model can improve highlights either by correcting normals or by distorting normals; the proposed method constrains normals through `G_surface` and moves residual appearance into `G_reflection`.

## Why Naive Specular Consistency Is Wrong
For the same surface point:

```math
S(x, v_1) \neq S(x, v_2)
```

in general, because different views see different reflected directions and environment content.

Therefore, the method should not enforce:

```math
S(x, v_1) \approx S(x, v_2).
```

Potential Hypothesis: Instead enforce consistency on:

```math
\rho(x), n(x), roughness(x), T_ref(x, r), c_mesh(x)
```

or on reflected-source features only when two rays correspond to the same physical source under a valid reflection/visibility mapping.

## Loss Functions
### Photometric Reconstruction Loss
```math
L_photo = ||\hat I - I||_1 + \lambda_{ssim}(1 - SSIM(\hat I, I)).
```
- input tensors: predicted final image `I_hat`, target image `I`.
- output tensor: scalar.
- differentiability: differentiable except SSIM window ops are differentiable in PyTorch.
- application level: per-pixel.
- branch: both branches through final rendering.
- stage: all stages, with reflection component delayed in Stage B.
- risk: can still reward wrong attribution; controlled by separation and staged training.
- ablation: remove other losses and show PSNR may improve while mesh/material fails.

### Surface Normal-depth Consistency
```math
L_geo = mean_p M_s(p) [1 - n_rend(p) \cdot n_depth(p)] + \lambda_d L_depth_smooth.
```
- input tensors: `rend_normal`, `surf_normal`, `surf_depth`, `rend_alpha`, optional reflective uncertainty mask.
- output tensor: scalar.
- differentiability: differentiable through rendered normals/depth.
- application level: per-pixel / per-surface projection.
- branch: `G_surface` only.
- stage: Stage A and B; strongest in Stage A.
- failure addressed: unstable normal/depth and mesh holes.
- risk: over-smoothing real high-frequency geometry.
- ablation: without normal-depth consistency -> higher normal MAE / worse mesh.

### Branch Separation Loss
```math
L_sep = mean_p [ max(0, E_spec(p) - g_r(p)) + \beta |S_r(p)|_1 (1 - M_spec(p)) ].
```
- input tensors: reflection gate `g_r`, specular residual `S_r`, specular evidence `E_spec` from view variance or residual, optional specular mask.
- output tensor: scalar.
- differentiability: differentiable except external mask is fixed.
- application level: per-pixel and per-Gaussian gate.
- branch: separates `G_surface` and `G_reflection`.
- stage: Stage B and C.
- failure addressed: branch collapse and specular leakage into surface.
- risk: suppressing real reflection if mask is poor.
- ablation: without `L_sep` -> higher albedo leakage or reflection branch collapse.

### Reflection Transport Consistency Loss
For a matched surface point observed in views `i` and `j`:

```math
L_ref =
sum_{(i,j,p)} w_{ij}(p)
|| T_ref(x, r_i) - T_ref(x, r_j^*) ||_1,
```

where `r_j^*` is used only if correspondence indicates the same reflected source feature; otherwise only material/geometry variables are constrained.
- input tensors: surface correspondence, normal, view direction, roughness, transport features, visibility weights.
- output tensor: scalar.
- differentiability: differentiable through sampled transport features; correspondence weights can be detached.
- application level: per-surface point / per-pixel correspondence.
- branch: reflection branch and surface normals.
- stage: after geometry warm-up.
- failure addressed: physically wrong consistency on specular RGB.
- risk: noisy correspondence.
- ablation: naive RGB specular consistency vs transport consistency.

### Material Consistency Loss
```math
L_mat = sum_{(i,j,p)} w_{ij}(p)
(||\rho_i(p)-\rho_j(p)||_1 + \lambda_r ||rough_i(p)-rough_j(p)||_1).
```
- input tensors: rasterized albedo, roughness, visibility/correspondence masks.
- output tensor: scalar.
- differentiability: differentiable through surface branch attributes.
- application level: per-surface point / per-pixel.
- branch: `G_surface`.
- stage: Stage B and C.
- failure addressed: material flicker and highlight baking.
- risk: wrong correspondences can smear texture.
- ablation: remove material consistency and evaluate material map stability.

### Texture De-specularization Loss
```math
L_tex = sum_t sum_{i \in V(t)} w_{it}
|| A(t) - D_i(\pi_i(t)) ||_1
+ \lambda_h H(A, M_spec),
```

where `A(t)` is baked albedo texel and `H` penalizes highlight leakage.
- input tensors: UV texel samples, diffuse predictions, specular residual weights, visibility weights.
- output tensor: scalar or offline baking objective.
- differentiability: differentiable if UV sampling is in training; can also be post-training optimization.
- application level: per-texel.
- branch: surface branch.
- stage: Stage C.
- failure addressed: baked highlights in albedo.
- risk: under single illumination, albedo-light ambiguity remains.
- ablation: direct RGB baking vs diffuse/residual-aware baking.

## Full Objective
```math
L =
L_photo
+ \lambda_{geo} L_geo
+ \lambda_{sep} L_sep
+ \lambda_{ref} L_ref
+ \lambda_{mat} L_mat
+ \lambda_{tex} L_tex
+ \lambda_{reg} L_reg.
```

Weight schedule:
- Stage A: high `lambda_geo`, zero/small `lambda_ref`, no texture loss.
- Stage B: enable `lambda_sep`, `lambda_ref`, `lambda_mat`; optionally detach specular path from `xyz/scaling/rotation/opacity`.
- Stage C: enable `lambda_tex`, lower geometry LR, export mesh/material maps.

Tuning risk:
- too high `lambda_sep`: suppressed reflection.
- too high `lambda_geo`: oversmoothed geometry and lower NVS.
- too high `lambda_mat`: texture blur.
- too low `lambda_ref`: reflection branch overfits per-view residual.

## Optimization Strategy
Potential Hypothesis:
1. Initialize from Ref-GS or train Ref-GS-compatible surface branch.
2. Geometry warm-up for 3k-7k iterations depending scene.
3. Enable reflection branch and branch separation.
4. Freeze or reduce geometry LR after stable normal/depth.
5. Fine-tune material/texture maps after mesh extraction.

## Theoretical Motivation
Derived Analysis: The decomposition is physically motivated because surface geometry and diffuse/material properties are view-independent under fixed scene/object geometry, while specular radiance is view-dependent and governed by reflection direction, BRDF and visible incident radiance. Separating these variables reduces the incentive for geometry to explain moving highlights.

## Assumptions and Limitations
- Assumption: camera poses are accurate enough for surface correspondences.
- Assumption: fixed lighting during capture unless relighting dataset is used.
- Assumption: specular evidence can be estimated from residual/view variance or learned gate.
- Limitation: roughness/metallic are underconstrained without GT or multi-light data.
- Limitation: near-field mirror reflection may require explicit local reflection Gaussians or ray tracing.
- Needs Verification: all equations require implementation and ablation before scientific claims.
