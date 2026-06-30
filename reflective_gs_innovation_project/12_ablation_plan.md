# Ablation Plan

## Ablation Table
| ID | Variant | What it removes or changes | Supports | Could refute |
|---|---|---|---|---|
| A0 | Ref-GS baseline | no proposed modules | baseline reference | if already matches mesh/material metrics, gap weaker |
| A1 | single branch SRD | remove reflection branch | need for geometry-reflection decoupling | if same mesh/material quality, branch unnecessary |
| A2 | no branch separation | remove `L_sep` | branch separation prevents leakage | if no leakage increase, `L_sep` weak |
| A3 | no geometry-aware loss | remove `L_geo` | normal-depth consistency helps mesh | if normal/mesh unchanged |
| A4 | no normal-depth consistency | remove normal-depth term only | normal quality predicts mesh | if mesh unchanged |
| A5 | no reflection transport consistency | remove `L_ref` | physical transport consistency matters | if reflective metrics unchanged |
| A6 | naive specular RGB consistency | replace `L_ref` with `||S(v1)-S(v2)||` | specular RGB equality is wrong | if RGB consistency wins |
| A7 | no material consistency | remove `L_mat` | material stability matters | if material maps unchanged |
| A8 | no texture de-specularization | direct RGB texture baking | de-specularized baking reduces leakage | if leakage unchanged |
| A9 | no staged training | train all terms end-to-end | staged schedule stabilizes optimization | if end-to-end better |
| A10 | reflection branch contributes to mesh | extract mesh from all branches | surface-only extraction is necessary | if all-branch mesh is better |
| A11 | full SRD-GS | all components | final method | if no targeted metric gains |

## Component-wise Ablation
- Without reflection branch: tests whether the added view-dependent branch actually prevents surface pollution.
- Without geometry-reflection decoupling: tests whether gains come from extra parameters or from branch responsibility.
- Surface Gaussians used for mesh vs all Gaussians used for mesh: directly tests the central mesh-export rule.

## Loss-wise Ablation
- `L_geo`: validates normal/depth stability.
- `L_sep`: validates branch separation and residual sparsity.
- `L_ref`: validates transport consistency.
- `L_mat`: validates albedo/roughness consistency.
- `L_tex`: validates specular-free baking.
- Naive RGB consistency: negative control for physically invalid specular equality.

## Training-stage Ablation
- Stage-wise training vs end-to-end.
- Delayed reflection branch vs reflection from iteration 0.
- Geometry branch freeze/detach vs full gradient flow.
- Texture export fine-tuning vs direct post-process baking.

## Mesh-output Ablation
- mesh from `G_surface` only.
- mesh from `G_surface + G_reflection`.
- mesh from Ref-GS unified render.
- common TSDF extraction vs native method-specific extraction.

Expected support:
`G_surface` only should reduce reflective artifacts and holes.

Refuting result:
all-branch mesh has equal or better geometry metrics.

## Texture-output Ablation
- direct final RGB baking.
- Ref-GS albedo-like output baking.
- SRD-GS diffuse-only baking.
- SRD-GS robust aggregation with specular weights.

Expected support:
robust diffuse-only baking has lowest highlight leakage and best relighting.

Refuting result:
direct RGB baking performs equally under novel light.

## What Each Ablation Supports
Every component must map to a failure:
- branch decoupling -> reflection mistaken as geometry / floating Gaussians.
- geometry loss -> unstable normal/depth / noisy mesh.
- transport consistency -> naive consistency blur.
- texture de-specularization -> baked highlights.
- staged training -> inverse-rendering instability.

## What Each Ablation Could Refute
- Added branch improves only rendering, not mesh/material.
- Branch separation suppresses real reflection.
- Material consistency blurs texture.
- Transport consistency is too noisy.
- Staged training locks wrong geometry.
- Method gains are parameter-count effects rather than factorization effects.
