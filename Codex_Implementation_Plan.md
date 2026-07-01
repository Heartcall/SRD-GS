# Codex Implementation Plan: SRD-GS from Code to Experiments

你是一个熟练使用 Codex skills 的科研工程 agent。当前任务不是继续写方法构想，而是在 Ref-GS 代码仓库上把 `SRD-GS: Surface-Reflection Decoupled Gaussian Splatting for Specular-Free Mesh Reconstruction and PBR Material Mapping` 从代码实现到实验验证完整落地。

已有科研设计文件在：

```text
reflective_gs_innovation_project/
├── 02_selected_baseline_rationale.md
├── 03_selected_baseline_code_review.md
├── 05_failure_to_gap_reasoning.md
├── 06_proposed_method.md
├── 07_theory_derivation.md
├── 08_full_pipeline.md
├── 09_implementation_plan.md
├── 10_experiment_design.md
├── 11_dataset_and_metric_plan.md
├── 12_ablation_plan.md
├── 14_risk_and_fallback.md
└── 15_final_summary_for_user.md
```

目标代码仓库是：

```text
external_repos/SRD-GS
```

主 baseline 是：

```text
Ref-GS: Directional Factorization for 2D Gaussian Splatting
https://github.com/YoujiaZhang/Ref-GS
```

本地下载的相关数据集存放在：
```text
/data/liuly/dataset/3DGS
```

SRD-GS 的核心假设：

```text
把 view-dependent specular residual 从 geometry-bearing Gaussian 中解耦出来。
G_surface 只负责 surface geometry、depth、normal、diffuse albedo、roughness、mesh extraction 和 PBR material baking。
G_reflection 只负责 view-dependent specular residual / reflection transport，不参与 mesh extraction，也不被 bake 进 diffuse texture。
```

## 总体执行原则

由于 external_repos/SRD-GS 当前就是 Ref-GS 原始代码仓库，所有 SRD-GS 实现必须直接在该仓库中进行；不要再创建 external_repos/Ref-GS，不要重新 clone，不要重新创建 conda 环境。所有命令默认在 conda 环境 ref-gs 中执行。不要一次性大改所有代码，必须按里程碑推进，每个里程碑都要：

1. 先读相关设计文件和当前代码；
2. 明确本轮只改哪些文件；
3. 尽量保持 Ref-GS 原始训练命令兼容；
4. 新增功能必须有 feature flag，不能破坏 baseline；
5. 每轮完成后运行静态检查、最小单元测试或 smoke test；
6. 生成清晰日志；
7. 不编造实验结果；
8. 如果 CUDA / 数据集 / 依赖不可用，写明 `Needs Runtime Verification`；
9. 每轮结束必须输出：

   * changed files；
   * added functions/classes；
   * tests run；
   * known risks；
   * next recommended command。

请优先使用已有 Codex skills，例如 repo-analysis、code-editing、experiment-design、verification-before-completion、grill-me、grill-with-docs、diagnosing-bugs 等。如果 skills 不可用，则用 shell、Python、pytest/unittest、markdown 日志完成。

---

# Modified Milestone 0: 使用现有 SRD-GS 仓库与 ref-gs 环境建立安全开发分支

## 目标

当前 `external_repos/SRD-GS` 存放的是 Ref-GS 原始代码仓库。不要重新 clone Ref-GS。请直接在该仓库中创建 SRD-GS 开发分支、记录 baseline 状态，并确认现有 `ref-gs` conda 环境可用于运行代码。

## 任务

1. 进入现有仓库：

```bash
cd external_repos/SRD-GS
```

2. 激活已有环境：

```bash
conda activate ref-gs
```

如果失败，使用：

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ref-gs
```

或者后续命令统一使用：

```bash
conda run -n ref-gs python ...
```

3. 检查当前仓库状态：

```bash
pwd
git status
git rev-parse HEAD
git branch --show-current
git remote -v
```

4. 不要重新 clone 仓库。当前仓库就是目标仓库。

5. 创建或切换开发分支：

```bash
git checkout -b srd-gs-dev
```

如果分支已存在，则执行：

```bash
git checkout srd-gs-dev
```

6. 创建目录：

```bash
mkdir -p docs/srd_gs tests scripts/srd_gs configs/srd_gs
```

7. 生成以下文档：

```text
docs/srd_gs/00_baseline_snapshot.md
docs/srd_gs/implementation_log.md
docs/srd_gs/todo.md
```

8. 在 `00_baseline_snapshot.md` 中记录：

```text
repository path: external_repos/SRD-GS
original codebase: Ref-GS
current git commit
current branch
remote url
conda environment: ref-gs
python version
torch version
cuda availability
key files existence
baseline training entry
renderer file
Gaussian model file
mesh extraction file
known issues
```

9. 使用 `ref-gs` 环境运行静态检查：

```bash
python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py
```

如果 shell 中环境激活不稳定，则用：

```bash
conda run -n ref-gs python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py
```

10. 不要开始实现 SRD-GS branch 参数，不要加新 loss，不要改 renderer。Milestone 0 只做环境、分支、快照和静态检查。

## 交付

```text
docs/srd_gs/00_baseline_snapshot.md
docs/srd_gs/implementation_log.md
docs/srd_gs/todo.md
```

最终汇报：

```text
Milestone: 0
Status:
Repository path:
Conda env:
Current commit:
Current branch:
Tests run:
Passed:
Failed:
Needs Runtime Verification:
Next recommended milestone:
```

---

# Modified Milestone 1: 在 external_repos/SRD-GS 中修复 Ref-GS baseline runtime 与 mesh extraction smoke path

## 目标

当前 `external_repos/SRD-GS` 是 Ref-GS 原始代码仓库，且 `ref-gs` conda 环境可运行代码。本阶段不要重新安装环境，不要重新 clone 仓库。目标是确认 baseline import、renderer、training entry 和 mesh extraction 相关路径可用，并修复最小 runtime 问题。

## 前置条件

```bash
cd external_repos/SRD-GS
conda activate ref-gs
git checkout srd-gs-dev
```

如果 `conda activate ref-gs` 不可用，则使用：

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ref-gs
```

或：

```bash
conda run -n ref-gs python ...
```

## 任务

1. 检查关键文件：

```bash
ls -la
ls -la scene gaussian_renderer utils
test -f scene/gaussian_model.py
test -f gaussian_renderer/__init__.py
test -f train.py
test -f utils/loss_utils.py
test -f utils/mesh_utils.py
```

2. 检查 `utils/mesh_utils.py` 是否仍然依赖缺失的 `utils.render_utils`：

```bash
grep -R "render_utils" -n utils/mesh_utils.py utils || true
```

3. 如果 `utils/render_utils.py` 缺失，但 `utils/mesh_utils.py` 需要它，则新增最小兼容文件：

```text
utils/render_utils.py
```

要求：

* 不改变 Ref-GS 原始 mesh extraction 主逻辑；
* 只补齐 `utils/mesh_utils.py` 实际 import 的函数；
* 如果某些函数无法完整实现，提供安全 fallback，并在 docstring 中标注 `Needs Runtime Verification`；
* 不要为了通过 import 而删除 mesh extraction 逻辑。

4. 创建 import / static tests：

```text
tests/test_mesh_utils_import.py
tests/test_baseline_imports.py
```

测试至少覆盖：

```text
import scene.gaussian_model
import gaussian_renderer
import utils.loss_utils
import utils.mesh_utils
```

5. 创建 Ref-GS renderer contract static test：

```text
tests/test_refgs_render_contract_static.py
```

该测试可以静态读取 `gaussian_renderer/__init__.py`，检查以下关键字符串或返回 key 是否存在：

```text
pbr_rgb
rend_alpha
rend_normal
surf_depth
surf_normal
roughness
spec_light
diff_light
```

如果不能真实运行 CUDA rasterizer，则不要伪造运行结果，只做 static contract test，并标注 `Needs Runtime Verification`。

6. 使用 `ref-gs` 环境运行：

```bash
python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py
python -m unittest tests.test_baseline_imports
python -m unittest tests.test_mesh_utils_import
python -m unittest tests.test_refgs_render_contract_static
```

如果环境激活不稳定，则改用：

```bash
conda run -n ref-gs python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py
conda run -n ref-gs python -m unittest tests.test_baseline_imports
conda run -n ref-gs python -m unittest tests.test_mesh_utils_import
conda run -n ref-gs python -m unittest tests.test_refgs_render_contract_static
```

7. 生成文档：

```text
docs/srd_gs/01_baseline_runtime_repair.md
```

文档必须记录：

```text
repository path: external_repos/SRD-GS
conda env: ref-gs
what was checked
what was repaired
whether utils/render_utils.py was added
tests run
tests passed
tests failed
runtime parts needing CUDA verification
known risks before SRD-GS implementation
```

## 严格约束

* 不要修改 SRD-GS branch 参数。
* 不要修改 `GaussianModel` 表示。
* 不要添加 SRD-GS losses。
* 不要改 training stage。
* 不要做 texture baking。
* 不要开始跑完整实验。
* 本阶段只保证 Ref-GS baseline 在当前路径和当前环境下具备可继续开发的基础。

## 交付

```text
utils/render_utils.py                 # only if needed
tests/test_baseline_imports.py
tests/test_mesh_utils_import.py
tests/test_refgs_render_contract_static.py
docs/srd_gs/01_baseline_runtime_repair.md
```

最终汇报：

```text
Milestone: 1
Status:
Repository path: external_repos/SRD-GS
Conda env: ref-gs
Changed files:
New files:
Tests run:
Passed:
Failed:
Needs Runtime Verification:
Key findings:
Risks:
Recommended next milestone:
```

---

# Milestone 2: 实现 SRD-GS 最小 branch 参数，不改变 baseline 默认行为

## 目标

在 `GaussianModel` 中加入 SRD-GS 所需的 branch-aware 参数，但默认关闭 SRD-GS 时，Ref-GS 原始行为必须保持一致。

## 需要阅读

```text
reflective_gs_innovation_project/03_selected_baseline_code_review.md
reflective_gs_innovation_project/06_proposed_method.md
reflective_gs_innovation_project/09_implementation_plan.md
```

## 修改文件

```text
scene/gaussian_model.py
arguments/__init__.py
```

## 任务

1. 在 CLI / config 中新增 feature flags：

```text
--enable_srd_gs
--srd_stage
--srd_reflection_warmup
--srd_detach_specular_geometry
--srd_use_branch_gate
--srd_reflection_dim
--srd_transport_dim
```

2. 在 `GaussianModel` 中添加最小参数：

```text
_surface_albedo
_surface_roughness
_reflection_feature
_specular_weight
_branch_gate
_transport_feature
```

注意：

* `_surface_albedo` 和 `_surface_roughness` 可以先从原 `_albedo` 和 `_roughness` 初始化；
* `_reflection_feature` 和 `_transport_feature` 可以随机小值初始化；
* `_branch_gate` 初始化为偏向 surface branch；
* `_specular_weight` 初始化为低值，避免一开始 reflection branch 吞掉全部残差。

3. 修改 `training_setup()`：

增加 optimizer groups：

```text
surface_albedo
surface_roughness
reflection_feature
specular_weight
branch_gate
transport_feature
```

4. 修改 `save_ply()` / `load_ply()`：

* baseline 旧 checkpoint 必须能加载；
* 新参数如果不存在，使用默认初始化；
* 新 checkpoint 应能保存 SRD-GS 参数；
* 记录 backward compatibility。

5. 新增测试：

```text
tests/test_srd_gaussian_model_static.py
```

测试内容：

* 新参数名存在；
* optimizer groups 名称存在；
* enable_srd_gs=False 时不强制使用新分支；
* save/load 有 backward-compatible fallback。

## 交付

* 修改后的 `scene/gaussian_model.py`
* 修改后的 `arguments/__init__.py`
* `tests/test_srd_gaussian_model_static.py`
* `docs/srd_gs/02_branch_params.md`

---

# Milestone 3: 修改 renderer，返回 SRD-GS 分离 buffer

## 目标

扩展 `gaussian_renderer/__init__.py::render()`，在 `enable_srd_gs=True` 时返回 surface/reflection 分离 buffer；在默认情况下保持 Ref-GS 原行为。

## 修改文件

```text
gaussian_renderer/__init__.py
```

## 需要实现的输出 key

在 SRD-GS 模式下，`render()` 至少返回：

```text
pbr_rgb
surface_rgb
diffuse_rgb
specular_rgb
surf_depth
surf_normal
rend_normal
rend_alpha
roughness_map
reflection_dir
branch_gate_map
specular_weight_map
transport_feature_map
reflection_residual
```

## 具体逻辑

1. 复用 Ref-GS 现有 rasterization 路线。
2. `G_surface` 输出：

   * `surface_rgb`
   * `diffuse_rgb`
   * `surf_depth`
   * `surf_normal`
   * `roughness_map`
3. 计算 reflection direction：

```text
r = 2(n dot v)n - v
```

4. 复用 Ref-GS 的 `SphMipEncoding` 和 `light_mlp`。
5. 通过 `branch_gate_map` 和 `specular_weight_map` 控制 `specular_rgb`。
6. 组合：

```text
pbr_rgb = diffuse_rgb + branch_gate_map * specular_rgb
```

7. 实现一个可选 detach：

```text
if srd_detach_specular_geometry:
    normals_for_specular = normals.detach()
    reflection_dir = reflection_dir.detach()
```

用于防止 specular gradient 在 warm-up 阶段污染 geometry。

8. 新增 renderer contract test：

```text
tests/test_srd_render_contract_static.py
```

## 约束

* 不要破坏原来的 `render()` 调用。
* 如果已有训练代码依赖旧 key，要保持兼容。
* 若 CUDA 不可运行，至少保证 py_compile 和静态 key contract test 通过。

## 交付

* 修改后的 `gaussian_renderer/__init__.py`
* `tests/test_srd_render_contract_static.py`
* `docs/srd_gs/03_renderer_buffers.md`

---

# Milestone 4: 实现 SRD-GS loss 与 staged training

## 目标

在训练脚本中实现 SRD-GS 的三阶段训练与基础 loss。

## 修改文件

```text
utils/loss_utils.py
train.py
train-NeRF.py
train-NeRO.py
train-real.py
```

优先实现 `train.py`，其他训练入口先保持兼容或只做轻量适配。

## 新增 loss

在 `utils/loss_utils.py` 中新增：

```text
branch_separation_loss
material_consistency_loss
transport_consistency_loss
highlight_leakage_loss
specular_sparsity_loss
```

最小版本允许：

* `transport_consistency_loss` 先实现为同视角或近邻 view 的 feature smoothness / stable-variable consistency；
* 复杂 visibility-aware correspondence 可以放到 Milestone 7；
* 但必须保留接口，方便后续升级。

每个 loss 函数必须有 docstring，说明：

```text
input tensors
output tensor
differentiability
application level
stage
risk
```

## 训练阶段

实现：

```text
Stage A: geometry warm-up
  enable reflection branch = false or very weak
  strong L_geo
  train surface albedo / roughness / geometry

Stage B: reflection residual learning
  enable reflection branch
  optionally detach specular geometry
  add L_sep, L_ref, L_mat

Stage C: material / texture fine-tuning
  freeze or weak-update geometry
  focus material consistency and texture export buffers
```

新增日志字段：

```text
loss_photo
loss_geo
loss_sep
loss_ref
loss_mat
loss_tex
specular_energy
branch_gate_mean
surface_alpha_mean
```

## 新增测试

```text
tests/test_srd_losses.py
tests/test_srd_stage_schedule.py
```

测试：

* loss 输入输出 shape；
* scalar loss 可 backward；
* stage schedule 是否按 iteration 切换；
* enable_srd_gs=False 时 baseline loss path 不变。

## 交付

* 修改后的 `utils/loss_utils.py`
* 修改后的 `train.py`
* 其他 train 文件的兼容修改
* `tests/test_srd_losses.py`
* `tests/test_srd_stage_schedule.py`
* `docs/srd_gs/04_training_losses.md`

---

# Milestone 5: 实现 surface-only mesh extraction

## 目标

实现 SRD-GS 的核心导出规则：mesh 只从 `G_surface` 提取，不允许 `G_reflection` 参与 mesh opacity / depth / normal。

## 修改文件

```text
utils/mesh_utils.py
```

## 新增脚本

```text
extract_surface_mesh.py
```

## 任务

1. 在 `GaussianExtractor` 中新增参数：

```text
surface_only=True
```

2. 新增或适配 renderer 调用：

```text
render_surface()
```

如果不单独新增函数，则在 `render()` 中通过 `surface_only=True` 返回：

```text
surface_rgb
surface_alpha
surface_depth
surface_normal
```

3. mesh extraction 只使用：

```text
surface_alpha
surface_depth
surface_normal
```

4. 保存诊断图：

```text
surface_depth.png
surface_normal.png
surface_alpha.png
specular_rgb.png
branch_gate_map.png
```

5. 支持三种 extraction 对照：

```text
Ref-GS unified render mesh
SRD-GS surface-only mesh
SRD-GS all-branch mesh negative ablation
```

6. 新增测试：

```text
tests/test_surface_only_mesh_contract.py
```

## 交付

* 修改后的 `utils/mesh_utils.py`
* `extract_surface_mesh.py`
* `tests/test_surface_only_mesh_contract.py`
* `docs/srd_gs/05_surface_only_mesh.md`

---

# Milestone 6: 实现 specular-free texture / material baking 最小版本

## 目标

实现从 surface branch 导出 specular-free material maps 的最小可运行版本。

## 新增文件

```text
utils/texture_baking.py
export_pbr_textures.py
```

## 最小输出

```text
albedo.png
roughness.png
normal.png
specular_weight.png
highlight_leakage_mask.png
baking_report.json
```

## 任务

1. 第一版可以先不做复杂 UV atlas。如果 UV unwrap 成本太高，先实现 image-space / mesh-vertex color baking：

   * vertex albedo；
   * vertex roughness；
   * vertex normal；
   * specular leakage score。
2. 如果环境有 `xatlas` / `trimesh` / `open3d` 支持，再实现 UV texture baking。
3. 聚合权重至少包括：

```text
visibility confidence
alpha confidence
view angle weight
specular residual downweight
branch_gate downweight
reprojection confidence if available
```

4. 不允许直接用 final `pbr_rgb` 作为 albedo。
5. 需要实现 direct RGB baking baseline，用于对照。
6. 新增测试：

```text
tests/test_texture_baking_weights.py
```

测试内容：

* 高 specular residual 的观测权重应更低；
* diffuse-only baking 不使用 final RGB；
* 输出文件路径和 report schema 正确。

## 交付

* `utils/texture_baking.py`
* `export_pbr_textures.py`
* `tests/test_texture_baking_weights.py`
* `docs/srd_gs/06_texture_baking.md`

---

# Milestone 7: 实现 reflective asset evaluation 脚本

## 目标

将 SRD-GS 的论文 claim 转换成可计算指标。不要只算 PSNR。

## 新增文件

```text
eval_reflective_assets.py
utils/metric_utils.py
scripts/srd_gs/run_eval_one_scene.sh
```

## 指标

必须支持：

```text
Rendering:
  PSNR
  SSIM
  LPIPS if available

Reflective region:
  Refl-PSNR
  Refl-SSIM
  Refl-LPIPS if available

Geometry:
  Chamfer Distance if GT mesh/point cloud exists
  F-score if GT exists
  normal MAE if GT normal or mesh-derived normal exists
  depth error if GT exists

Mesh diagnostics:
  connected components
  hole / boundary proxy if feasible
  floating Gaussian count near surface if feasible

Texture / material:
  highlight leakage score
  albedo error if GT exists
  roughness error if GT exists
  material consistency across views

Runtime:
  training time
  peak memory if available
  render FPS
```

## 输出

每个 scene 输出：

```text
metrics.json
metrics.csv
qualitative_panels/
failure_case_panels/
```

## 约束

* 没有 GT 的指标不要伪造，写 `null` 和 `not_available_reason`。
* 每个 metric 都要说明是否支持主假设。
* reflective masks 如果是自动估计，必须保存 mask 可视化。

## 交付

* `eval_reflective_assets.py`
* `utils/metric_utils.py`
* `scripts/srd_gs/run_eval_one_scene.sh`
* `docs/srd_gs/07_evaluation_metrics.md`

---

# Milestone 8: 实现 ablation 配置系统

## 目标

让 SRD-GS 的关键消融可以一键运行。

## 新增目录

```text
configs/srd_gs/
scripts/srd_gs/
```

## 配置

至少创建：

```text
configs/srd_gs/refgs_baseline.yaml
configs/srd_gs/full_srd_gs.yaml
configs/srd_gs/no_reflection_branch.yaml
configs/srd_gs/no_branch_separation.yaml
configs/srd_gs/no_geo_loss.yaml
configs/srd_gs/no_transport_consistency.yaml
configs/srd_gs/naive_specular_rgb_consistency.yaml
configs/srd_gs/no_texture_despecularization.yaml
configs/srd_gs/no_staged_training.yaml
configs/srd_gs/all_branch_mesh.yaml
```

## 脚本

```text
scripts/srd_gs/run_one_scene.sh
scripts/srd_gs/run_ablation_one_scene.sh
scripts/srd_gs/collect_results.py
scripts/srd_gs/make_tables.py
scripts/srd_gs/make_failure_panels.py
```

## 每个 ablation 必须记录

```text
Hypothesis
What it removes
Expected supporting result
Refuting result
Metrics to inspect first
```

## 交付

* config files
* scripts
* `docs/srd_gs/08_ablation_system.md`

---

# Milestone 9: 跑最小实验闭环

## 目标

先不要全量跑所有数据集。先跑一个最小闭环，证明代码可训练、可导出、可评估。

## 推荐顺序

1. 选 1 个小 scene。
2. 跑 Ref-GS baseline。
3. 跑 SRD-GS minimal。
4. 导出：

   * render；
   * separated buffers；
   * surface-only mesh；
   * direct RGB texture baseline；
   * SRD-GS specular-free texture。
5. 跑 eval。
6. 生成对比报告。

## 输出目录

```text
outputs/srd_gs_smoke/<scene>/
├── refgs_baseline/
├── srd_gs_full/
├── eval/
├── panels/
└── smoke_report.md
```

## smoke_report.md 必须包含

```text
scene name
training command
iterations
GPU
runtime
whether training completed
whether mesh extraction completed
whether texture export completed
metrics table
failure images
what worked
what failed
next fix
```

## 成功标准

不是要求指标一定好，而是要求：

```text
training does not crash
renderer returns separated buffers
surface-only mesh path runs or fails with clear reason
texture export path runs or fails with clear reason
eval script produces metrics.json
```

## 交付

* 最小实验输出目录
* `docs/srd_gs/09_smoke_experiment_report.md`

---

# Milestone 10: 扩展到论文级实验

## 目标

在 smoke test 成功后，扩展到多 scene、多 ablation、多 baseline。

## 实验矩阵

优先：

```text
Ref-GS baseline
SRD-GS full
no reflection branch
no branch separation
no geometry-aware loss
naive specular RGB consistency
surface-only mesh vs all-branch mesh
direct RGB baking vs specular-free baking
```

数据集优先：

```text
Shiny Blender / Ref-NeRF scene
Glossy Synthetic / NeRO scene
one real glossy scene if available
one synthetic diagnostic scene with GT mesh/material
```

## 输出

```text
outputs/srd_gs_experiments/
├── raw_logs/
├── metrics/
├── tables/
├── figures/
├── failure_cases/
└── experiment_summary.md
```

## experiment_summary.md 必须回答

1. SRD-GS 是否降低 reflective-region normal MAE？
2. SRD-GS 是否降低 reflective-region mesh Chamfer / 提高 F-score？
3. SRD-GS 是否降低 albedo highlight leakage？
4. SRD-GS 是否保持接近 Ref-GS 的 PSNR/SSIM/LPIPS？
5. 哪个消融最关键？
6. 有没有反驳主假设的结果？
7. 下一步该改代码还是改论文 claim？

## 交付

* `experiment_summary.md`
* `tables/*.csv`
* `figures/*.png`
* `failure_cases/*.png`
* updated `docs/srd_gs/final_implementation_summary.md`

---

# 最终要求

完成每个 Milestone 后，不要自动进入下一阶段，先汇报：

```text
Milestone:
Status:
Changed files:
New files:
Tests run:
Passed:
Failed:
Needs Runtime Verification:
Key findings:
Risks:
Recommended next milestone:
```

严禁：

1. 未跑实验就声称 SRD-GS 优于 Ref-GS；
2. 为了让指标好看而修改实验结果；
3. 删除 Ref-GS 原始功能；
4. 把 final RGB 直接当 albedo texture；
5. 让 reflection branch 参与默认 mesh extraction；
6. 对 specular RGB 做 naive consistency 并把它当主方法；
7. 忽略 failed tests；
8. 忽略 `Needs Verification` 项。
