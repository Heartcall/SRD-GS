# Task Log

## Completed Steps
| Step | Status | Evidence |
|---|---|---|
| inspect installed skills | done | 本地确认 `nature-academic-search`、`nature-writing`、`verification-before-completion`、`pdf` 等技能；formal tool search 未发现额外工具。 |
| read research pack | done | 已读取 `gs_reflective_reconstruction_research_pack/README.md`、`research_context.md`、`literature_matrix.csv`、`paper_cards/selected_paper_cards.md`、`taxonomy.md`、`core_problem_map.md`、`failure_case_bank.md`、`limitation_and_gap_analysis.md`、`hypothesis_bank.md`、`potential_method_directions.md`、`experiment_design_guide.md`、`dataset_and_metric_guide.md`、`codex_reasoning_instructions.md`。 |
| searched papers | done | 使用 web/arXiv/GitHub/CVF/project pages 核验 3DGS、2DGS、SuGaR、GS-IR、Ref-GS、R3DG、EnvGS、IRGS、Ref-DGS、Ref-NeRF、NeRFactor、NeRO 等。 |
| verified code repositories | partial | Ref-GS、2DGS、SuGaR、GS-IR、Ref-DGS 的 GitHub 页面可访问；Ref-GS 已 clone 到 `external_repos/Ref-GS`。部分新论文代码状态仍 `Needs Verification`。 |
| selected baseline | done | 选定 `Ref-GS: Directional Factorization for 2D Gaussian Splatting`。 |
| reviewed code | done | 静态审阅 `external_repos/Ref-GS/README.md`、`arguments/__init__.py`、`scene/gaussian_model.py`、`gaussian_renderer/__init__.py`、`train*.py`、`utils/loss_utils.py`、`utils/mesh_utils.py`、`scene/*`。 |
| derived limitation | done | limitation: single geometry-bearing Gaussian set stores surface support, material-like attributes, directional features and specular output; no explicit reflection branch exclusion from mesh; no UV/PBR texture export. |
| proposed method | done | `SRD-GS` dual branch + reflection transport + specular-free baking. |
| designed experiments | done | Rendering, reflective-region, mesh, normal, texture/material, relighting, ablation and failure case protocol written. |

## Pack Summary
### Main Research Task
From Literature: 研究包将任务定义为基于 GS 的 high-reflectance / glossy / specular object reconstruction，目标包括 accurate surface geometry、reliable mesh extraction、specular-free texture baking 和 PBR material estimation。

Derived Analysis: 该任务的主线不是提高全图 PSNR，而是把 multi-view images 转换为可用的 3D asset：`Gaussian representation -> geometry -> mesh -> texture/material maps -> relighting/editing`。

### Core Technical Contradictions
- From Literature: reflective/specular surfaces violate diffuse multi-view consistency；同一 surface point 在不同 view 下颜色可变。
- Derived Analysis: photometric loss 可通过错误 normal、floating Gaussians 或 baked texture 解释 specular residual，因此 rendering quality 与 geometry/material quality 可能脱钩。
- Derived Analysis: mesh extraction 要求 view-independent surface support，而 reflection rendering 要求 view-dependent transport；二者如果存入同一 branch，优化目标会冲突。
- Potential Hypothesis: 若把 surface branch 与 reflection branch 的职责硬分离，并只从 surface branch 导出 mesh/material，可降低 reflective-region normal MAE、mesh Chamfer 和 albedo highlight leakage。

### Most Relevant Papers
- From Literature: 3DGS, 2DGS, SuGaR, GOF, Gaussian Surfels: GS surface / mesh route.
- From Literature: Ref-NeRF, NeRFReN, NeRO, NeRFactor: NeRF reflective/inverse rendering route.
- From Literature: GS-IR, R3DG, Ref-GS, EnvGS, Ref-Gaussian, IRGS, SVG-IR, GlossyGS, Ref-DGS: reflective / inverse rendering GS route.
- From Literature: Texture-GS: GS texture mapping route.

### Most Important Failure Cases
- Derived Analysis: specular highlight baked into texture/albedo.
- Derived Analysis: reflection mistaken as geometry bumps.
- Derived Analysis: floating Gaussians in reflective regions.
- Derived Analysis: unstable normal/depth leading to wrong reflection direction.
- Derived Analysis: high PSNR but poor mesh/material outputs.
- Derived Analysis: naive multi-view specular RGB consistency causes blurred or physically wrong highlights.

### Candidate Gaps
- Derived Analysis: rendering quality does not guarantee reflective-region mesh quality.
- Derived Analysis: texture mapping still mixes material and illumination unless specular is separated.
- Derived Analysis: reflective GS papers often optimize NVS/relighting but do not make mesh/material export the training target.
- Derived Analysis: evaluation lacks reflective-region mesh/material metrics.

### Candidate Method Directions
- Potential Hypothesis: surface-reflection dual Gaussian branches.
- Potential Hypothesis: reflection-transport consistency over normal/roughness/reflected-source features rather than specular RGB.
- Potential Hypothesis: specular-free UV/PBR texture baking from surface branch only.
- Potential Hypothesis: staged optimization: geometry-first, reflection branch later, texture/material fine-tuning last.
