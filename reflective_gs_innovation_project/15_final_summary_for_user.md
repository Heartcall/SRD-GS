# Final Summary for User

## 选定的主 baseline
本次选定的主 baseline 是 `Ref-GS: Directional Factorization for 2D Gaussian Splatting`。

- 论文/项目来源：`https://arxiv.org/abs/2412.00905`，`https://ref-gs.github.io/`，`https://github.com/YoujiaZhang/Ref-GS`。
- 代码状态：已成功 clone 到 `external_repos/Ref-GS`，commit 为 `bf843b7 Update README.md`。
- 选择理由：它直接面向 reflective / glossy 2DGS，有公开代码，已有 reflection direction、roughness-aware spherical Mip-grid、deferred rendering 和 2DGS mesh extraction 路线，适合作为新方法的工程基线。

## 该 baseline 的核心局限性
Derived Analysis: Ref-GS 的公开代码中，几何支撑、albedo、roughness、directional feature 和 specular rendering 都依附在同一组 Gaussian 上。`gaussian_renderer.render()` 使用同一组 `means3D / opacity / scales / rotations` 生成 albedo、roughness/feature、alpha、normal、depth，并进一步预测 `spec_light`，最后用 `pbr_rgb = spec_light + diff_light` 做图像重建。

这意味着：即使 Ref-GS 改善了 reflective rendering，view-dependent specular residual 仍可能通过 photometric loss 间接影响 geometry-bearing Gaussians。对于论文目标中的 mesh reconstruction 和 texture/material mapping，这个局限很关键，因为它可能导致：

- reflection 被解释成几何凹凸；
- reflective region 出现 floating Gaussians；
- normal/depth 不稳定；
- mesh extraction 有洞或噪声；
- albedo/texture 中 baked highlight；
- PSNR 提升但 mesh/material 质量不提升。

## 提出的新方法
方法名：`SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping`。

核心做法：

1. `G_surface`: 只负责 surface geometry、depth、normal、diffuse albedo、roughness、mesh extraction 和 material map baking。
2. `G_reflection`: 只负责 view-dependent specular residual / reflection transport，不参与 mesh extraction，也不被 bake 进 diffuse texture。
3. 用 reflection direction `r = 2(n dot v)n - v` 延续 Ref-GS 的方向建模优势。
4. 不做 naive specular RGB consistency；只对 normal、albedo、roughness、transport feature 等稳定变量做 consistency。
5. 从 `G_surface` 导出 mesh，再进行 residual-aware specular-free UV/PBR texture baking。

## 方法为什么有独特视角
它不是简单“加一个 loss”，而是改变 Ref-GS 的表示职责：

- surface branch 是可导出资产的来源；
- reflection branch 是 view-dependent appearance 的来源；
- mesh/material 评价是主目标，而不是渲染 PSNR 的附属结果。

与 Ref-DGS 相比，SRD-GS 的重点不是仅做 dual reflection rendering，而是把 dual representation 绑定到 surface-only mesh extraction、specular-free texture baking 和 reflective-region asset metrics。

## 核心 pipeline
1. 读取 posed multi-view images、camera、optional masks。
2. 初始化 Ref-GS / 2DGS surface Gaussians。
3. Stage A: geometry-first surface branch training。
4. Stage B: 引入 reflection branch，学习 specular residual / transport。
5. Stage B/C: 加入 branch separation、material consistency、reflection transport consistency。
6. 从 `G_surface` only 提取 mesh。
7. 对 mesh 做 UV unwrap 和 specular-free PBR material baking。
8. 用 rendering、reflective region、mesh、normal、texture/material、relighting 指标评估。

## 理论依据
从图像形成看：

```math
I(x,v) = D(x) + S(x,v)
```

`D(x)` 在固定光照近似下主要是 view-independent，适合进入 albedo/material/mesh branch；`S(x,v)` 是 view-dependent，不应该被强行当作 surface texture 或 geometry。对同一 surface point，通常有：

```math
S(x,v_1) \neq S(x,v_2)
```

因此，不应直接约束不同视角 specular RGB 相等。更合理的是约束 `normal / roughness / albedo / reflection transport feature` 等相对稳定变量。

## 实验方案
主比较：
- Ref-GS selected baseline；
- 2DGS；
- SuGaR / GOF；
- GS-IR / R3DG；
- Texture-GS；
- Ref-DGS if runnable；
- SRD-GS。

核心指标：
- Rendering: PSNR / SSIM / LPIPS。
- Reflective region: Refl-PSNR / Refl-LPIPS。
- Geometry: Chamfer / F-score / normal MAE / depth error。
- Mesh: holes、noise、component count、reflective-region mesh quality。
- Texture/material: albedo highlight leakage、roughness error if GT、material consistency、relighting PSNR/LPIPS if GT。

关键消融：
- without reflection branch；
- without branch separation；
- without normal-depth consistency；
- naive specular RGB consistency vs transport consistency；
- surface-only mesh vs all-branch mesh；
- direct RGB baking vs specular-free baking；
- staged training vs end-to-end training。

## 预期贡献
Potential Hypothesis:
1. 一个面向 reflective asset reconstruction 的 surface-reflection decoupled GS 表示。
2. 一个避免错误 specular RGB consistency 的 reflection transport consistency。
3. 一个从 GS 到 specular-free mesh/PBR material maps 的导出 pipeline。
4. 一套 reflective-region mesh/material evaluation protocol。

这些贡献都需要实验验证，不能在未运行实验前声称已经优于现有方法。

## 风险
- reflection branch 可能吸收 geometry error。
- surface branch 可能仍然 baked highlight。
- geometry loss 可能牺牲 rendering PSNR。
- material GT 缺失会限制材料定量评价。
- Ref-GS 当前 `utils/mesh_utils.py` 依赖缺失的 `utils.render_utils`，mesh extraction runtime 需要修复和验证。
- Ref-DGS / IRGS / Ref-Gaussian 等新工作可能与部分思想重叠，需要在论文中明确区别。

## 下一步建议
1. 先做 Ref-GS 代码修复和 surface-only mesh extraction smoke test。
2. 在一个 Shiny Blender / Glossy Synthetic scene 上做最小 SRD-GS branch prototype。
3. 优先验证 normal MAE、mesh Chamfer/F-score、highlight leakage，而不是先跑全量 PSNR。
4. 写一个小型 synthetic glossy Blender diagnostic scene，确保有 GT mesh/material/relighting。
5. 只有当 mesh/material 指标成立后，再扩展到完整论文实验表。
