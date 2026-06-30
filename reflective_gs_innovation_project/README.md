# Reflective GS Innovation Project

## Project Goal
本项目面向 Gaussian Splatting based reflective object surface mesh reconstruction and texture / material mapping。目标不是写泛化综述，而是完成一条可实现的研究工程链路：

`verified literature -> public-code baseline selection -> code-level limitation -> failure phenomenon -> root cause -> technical contradiction -> proposed hypothesis -> method design -> theory formulation -> implementation path -> falsifiable experiments -> paper story`

## Selected Baseline
`Ref-GS: Directional Factorization for 2D Gaussian Splatting`

- From Literature: arXiv `https://arxiv.org/abs/2412.00905` 将 Ref-GS 描述为面向 reflective 2DGS 的 directional light factorization 方法，使用 deferred surface directional encoding、spherical Mip-grid 和 geometry-lighting factorization。
- From Literature: GitHub `https://github.com/YoujiaZhang/Ref-GS` 标注 `[CVPR 2025]`，公开代码，README 说明主要测试 Shiny Blender Synthetic / Real、Glossy Synthetic、NeRF Synthetic，并说明 mesh extraction adopts 2DGS method。
- From Code Inspection: 本地克隆 `external_repos/Ref-GS` commit `bf843b7 Update README.md`，关键代码位于 `scene/gaussian_model.py`、`gaussian_renderer/__init__.py`、`train.py`、`utils/mesh_utils.py`。

## Proposed Method Name
`SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping`

## Key Research Gap
Derived Analysis: Ref-GS 改善 reflective NVS 和 geometry-aware rendering，但其代码仍使用同一组 geometry-bearing Gaussians 同时承载 surface support、albedo/roughness、directional feature 和 specular rendering residual。该结构没有显式禁止 view-dependent specular residual 影响 mesh extraction，也没有标准 UV/PBR material export。核心 gap 是：`reflective rendering improvement` 尚未充分转化为 `specular-free mesh + texture/material asset`。

## Directory Structure
- `00_task_log.md`: 任务日志与 pack 摘要。
- `01_literature_search_matrix.csv`: 核验后的文献矩阵。
- `02_selected_baseline_rationale.md`: baseline 选择理由。
- `03_selected_baseline_code_review.md`: Ref-GS 代码审阅。
- `04_existing_methods_and_limitations.md`: 技术路线与局限。
- `05_failure_to_gap_reasoning.md`: failure -> gap 推理。
- `06_proposed_method.md`: 新方法设计。
- `07_theory_derivation.md`: 理论推导与 loss。
- `08_full_pipeline.md`: 全流程与 Mermaid 图。
- `09_implementation_plan.md`: Ref-GS 上的实现计划。
- `10_experiment_design.md`: 可证伪实验设计。
- `11_dataset_and_metric_plan.md`: 数据集与指标方案。
- `12_ablation_plan.md`: 消融实验。
- `13_paper_story.md`: 论文叙事。
- `14_risk_and_fallback.md`: 风险与 fallback。
- `15_final_summary_for_user.md`: 中文自包含总结。

## Recommended Reading Order
建议按 `00 -> 02 -> 03 -> 05 -> 06 -> 07 -> 08 -> 09 -> 10 -> 15` 阅读；如需查文献细节，再读 `01` 和 `04`。

## Verification Status
- done: research pack 已读取。
- done: selected baseline public code 已通过 GitHub 和本地 clone 验证。
- done: Ref-GS 关键代码静态检查完成。
- partial: 部分 2025/2026 arXiv 论文 venue/code 状态仍需手动二次核验，已标注 `Needs Verification`。
- Needs Verification: 未运行任何训练、mesh extraction、PDF 全文抽取或实验复现。
