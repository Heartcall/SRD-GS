# SRD-GS Baseline Snapshot

## Scope

本文件记录 Milestone 0 的静态基线快照。当前阶段只确认 Ref-GS 原始代码仓库、环境、分支和关键文件，不实现 SRD-GS 新模块，不运行训练，也不声明实验效果。

## Repository

- Target repository: `/home/liuly/Surface_Reconstruction/my_work/external_repos/SRD-GS`
- Original codebase: Ref-GS
- Remote: `https://github.com/Heartcall/SRD-GS.git`
- Branch: `srd-gs-dev`
- Commit: `bf843b7d9d74941a400defd55f60aaf36694dd24`
- Initial untracked files: `__pycache__/`, `gaussian_renderer/__pycache__/`, `scene/__pycache__/`

## Environment

- Implementation plan expected env name: `ref-gs`
- Verified available env name: `ref_gs`
- Python: `3.7.12`
- PyTorch: `1.12.1`
- Torch CUDA build: `11.3`
- CUDA available through `conda run -n ref_gs`: `True`
- CUDA device count: `8`

## Key Files Verified

- Training entry: `train.py`
- Additional training entries: `train-NeRF.py`, `train-NeRO.py`, `train-real.py`
- Gaussian model: `scene/gaussian_model.py`
- Renderer: `gaussian_renderer/__init__.py`
- Loss utilities: `utils/loss_utils.py`
- Mesh utilities: `utils/mesh_utils.py`

## Baseline Code Observations

- `scene/gaussian_model.py` is the likely insertion point for SRD-GS Gaussian attributes such as diffuse albedo, roughness, reflection gate, and branch-specific feature tensors.
- `gaussian_renderer/__init__.py` is the likely insertion point for the surface/reflection rendering decomposition and output buffers.
- `train.py` is the likely insertion point for staged training schedules and SRD-GS losses.
- `utils/loss_utils.py` is the likely insertion point for differentiable geometry, material, branch separation, and reflection consistency losses.
- `utils/mesh_utils.py` is the likely insertion point for mesh extraction/export behavior that should use surface branch attributes only.

## Known Static Issues

- `utils/render_utils.py` is not present in the repository, while later runtime/import validation may require it if `utils/mesh_utils.py` imports it. This is a Milestone 1 repair target, not a Milestone 0 implementation change.
- No SRD-GS branch parameters, rendering buffers, losses, training stages, texture baking, or PBR export are implemented yet.
- Baseline training, rendering, mesh extraction, and evaluation have not been run in this milestone.

## Verification Status

- Branch setup: done
- Environment probe: done with `ref_gs`
- Key file existence: done
- Static py_compile: done with `conda run -n ref_gs python -m py_compile scene/gaussian_model.py gaussian_renderer/__init__.py train.py utils/loss_utils.py utils/mesh_utils.py`
- Runtime import validation: Needs Runtime Verification
- Baseline training verification: Needs Runtime Verification
- Mesh extraction verification: Needs Runtime Verification
