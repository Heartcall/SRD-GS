# Full Pipeline

## Step 1: Input and Preprocessing
Input:
- posed multi-view images;
- camera intrinsics/extrinsics;
- optional alpha masks;
- optional reflective/specular masks;
- optional GT mesh/material/normal for evaluation.

Operation:
- load data through Ref-GS `Scene` and camera utilities;
- estimate reflective masks from provided masks, photometric variation, or residual after warm-up.

Output:
- training cameras, rays, masks and split metadata.

Reason:
- reflective-region metrics and losses require a stable surface/visibility protocol.

Difference from baseline:
- baseline only loads images/masks; proposed pipeline also creates reflective/specular confidence maps.

Code modules to modify:
- `scene/dataset_readers.py`;
- `utils/camera_utils.py`;
- new `utils/specular_mask.py`.

## Step 2: Baseline Initialization
Input:
- Ref-GS checkpoint or random/SfM initialization.

Operation:
- initialize `G_surface` from Ref-GS Gaussian set;
- initialize albedo/roughness/material fields from Ref-GS fields;
- initialize reflection branch disabled or low weight.

Output:
- surface branch ready for geometry warm-up.

Reason:
- reuse Ref-GS directional and 2DGS infrastructure.

Difference from baseline:
- baseline has one `GaussianModel`; proposed model has branch-aware attributes and stage flags.

Code modules to modify:
- `scene/gaussian_model.py::GaussianModel.__init__`;
- `GaussianModel.create_from_pcd`;
- `GaussianModel.training_setup`.

## Step 3: Surface / Reflection Modeling
Input:
- `G_surface`, camera rays and optional masks.

Operation:
- render surface diffuse/material buffers;
- compute reflection direction;
- query reflection branch only after geometry warm-up.

Output:
- `surface_rgb`, `diffuse_rgb`, `specular_rgb`, `pbr_rgb`, `surf_depth`, `surf_normal`, `roughness_map`, `reflection_dir`, `transport_feature_map`.

Reason:
- separate what can be baked into material maps from what must remain view-dependent.

Difference from baseline:
- baseline returns final `pbr_rgb`; proposed renderer returns separated branch buffers.

Code modules to modify:
- `gaussian_renderer/__init__.py::render`;
- `render_nerf`;
- `render_real`.

## Step 4: Geometry-aware Optimization
Input:
- surface outputs, target image, alpha/depth/normal masks.

Operation:
- optimize photometric and geometry losses;
- apply normal-depth consistency only to `G_surface`;
- reduce specular gradients to geometry during warm-up.

Output:
- stable surface branch for mesh extraction.

Reason:
- mesh quality depends on stable depth/normal support.

Difference from baseline:
- baseline normal loss and photometric loss both act on one branch.

Code modules to modify:
- `train.py`;
- `train-NeRF.py`;
- `train-NeRO.py`;
- `train-real.py`;
- `utils/loss_utils.py`.

## Step 5: Reflection / Material Optimization
Input:
- stable `G_surface`, enabled `G_reflection`, multi-view correspondences.

Operation:
- optimize reflection residual;
- enforce material consistency on albedo/roughness;
- enforce transport consistency only on valid reflected-source features or stable variables;
- apply branch separation and residual sparsity.

Output:
- view-dependent reflection branch and cleaner surface material fields.

Reason:
- reflections should render well without altering mesh-bearing support.

Difference from baseline:
- baseline has no explicit branch separation or transport consistency.

Code modules to modify:
- new `utils/reflection_transport.py`;
- new losses in `utils/loss_utils.py`;
- training scripts.

## Step 6: Mesh Extraction
Input:
- `G_surface` and surface-only render buffers.

Operation:
- run surface-only TSDF / Poisson / 2DGS mesh extraction;
- exclude `G_reflection` alpha and features from geometry.

Output:
- mesh, normals, mesh confidence, diagnostic visualizations.

Reason:
- prevent specular branch from producing mesh geometry.

Difference from baseline:
- baseline mesh extraction uses render outputs from the unified model.

Code modules to modify:
- `utils/mesh_utils.py::GaussianExtractor`;
- new `extract_surface_mesh.py`.

## Step 7: Texture / Material Baking
Input:
- surface mesh, UVs, `G_surface` diffuse/material maps, residual/specular weights.

Operation:
- unwrap mesh;
- project texels into views;
- robustly aggregate diffuse albedo/roughness/normal;
- downweight high specular residual and high view variance.

Output:
- `albedo.png`, `roughness.png`, `normal.png`, optional `metallic.png`, `specular_weight.png`, `highlight_leakage_mask.png`.

Reason:
- texture baking must avoid final RGB highlights.

Difference from baseline:
- baseline has no UV/PBR export path.

Code modules to modify:
- new `utils/texture_baking.py`;
- new `export_pbr_textures.py`.

## Step 8: Evaluation
Input:
- baseline and proposed renderings, meshes, materials, masks, optional GT.

Operation:
- compute global NVS, reflective-region NVS, geometry, mesh, texture/material, relighting and runtime metrics.

Output:
- CSV tables, qualitative panels, ablation plots.

Reason:
- claims must be falsifiable and asset-level.

Difference from baseline:
- baseline code has no unified reflective asset evaluation.

Code modules to modify:
- new `eval_reflective_assets.py`;
- new `scripts/make_failure_panels.py`.

## Mermaid Diagram
```mermaid
flowchart TD
  A[Posed multi-view images + cameras] --> B[Ref-GS / 2DGS initialization]
  B --> C[G_surface: geometry, normal, diffuse albedo, roughness]
  B --> D[G_reflection: residual transport, specular feature, gate]
  C --> E[Surface-only render buffers: alpha depth normal diffuse]
  C --> F[Reflection direction r = 2(n dot v)n - v]
  F --> D
  D --> G[Specular residual render]
  E --> H[Final image composition D + gate*S]
  H --> I[Photometric loss]
  E --> J[Geometry and normal-depth losses]
  D --> K[Branch separation + transport consistency]
  C --> L[Surface-only mesh extraction]
  L --> M[UV unwrap]
  C --> N[Specular-free material baking]
  M --> N
  N --> O[PBR maps: albedo roughness normal optional specular]
  L --> P[Mesh metrics]
  O --> Q[Texture/material/relighting metrics]
```
