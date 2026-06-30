# SRD-GS Milestone 9 Smoke Experiment Report

## Scope

本文件记录 Milestone 9。当前阶段完成一个最小工程闭环：在 Shiny Blender Synthetic `ball` 上分别运行 Ref-GS baseline 和 SRD-GS minimal，导出 mesh、texture/material proxy，并运行 blocked-safe eval。该闭环只验证代码路径可运行，不构成渲染、几何或材质质量结论。

## Scene and Runtime

- Scene: `ball`
- Dataset: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball`
- Iterations: `20`
- Max mesh/export views: `8`
- Output root: `outputs/srd_gs_smoke`
- Environment: `conda run -n ref_gs`
- CUDA check: `torch.cuda.is_available=True`, 8 devices, GPU 0 `NVIDIA RTX A5000`

## Output Directory

```text
outputs/srd_gs_smoke/
├── models/ball/refgs_baseline/
├── models/ball/full_srd_gs/
├── results/ball/refgs_baseline/
├── results/ball/full_srd_gs/
└── ball/
    ├── eval/
    └── smoke_report.md
```

## Completed Steps

| Step | Status |
| --- | --- |
| Ref-GS baseline training | completed |
| SRD-GS minimal training | completed |
| Ref-GS unified mesh extraction | completed |
| SRD-GS surface-only mesh extraction | completed |
| Direct RGB texture baseline export | completed |
| SRD-GS specular-free texture export | completed |
| Eval `metrics.json` generation | completed |
| Metrics summary CSV/Markdown | completed |

## Key Artifacts

- Smoke report: `outputs/srd_gs_smoke/ball/smoke_report.md`
- Metrics CSV: `outputs/srd_gs_smoke/ball/eval/metrics_summary.csv`
- Metrics Markdown: `outputs/srd_gs_smoke/ball/eval/metrics_summary.md`
- Ref-GS mesh: `outputs/srd_gs_smoke/results/ball/refgs_baseline/mesh_unified.ply`
- SRD-GS mesh: `outputs/srd_gs_smoke/results/ball/full_srd_gs/mesh_surface.ply`
- Ref-GS texture report: `outputs/srd_gs_smoke/results/ball/refgs_baseline/pbr_textures_direct_rgb/baking_report.json`
- SRD-GS texture report: `outputs/srd_gs_smoke/results/ball/full_srd_gs/pbr_textures_specular_free/baking_report.json`

## Runtime Bugs Fixed During Milestone 9

1. `gaussian_renderer/__init__.py`
   - Added `_slice_feature_or_default()`.
   - Prevented unsupported SRD extra channels from entering current rasterizer `language_feature_precomp`.
   - Current limitation: branch/specular/transport maps use fallback behavior until rasterizer ABI supports extra channels.

2. `extract_surface_mesh.py`
   - Added `--max_views` to make smoke mesh extraction bounded.

3. `utils/render_utils.py`
   - Fixed single-channel PNG export by squeezing `H x W x 1` arrays.

4. `utils/metric_utils.py`
   - Fixed highlight leakage PNG scale normalization.

5. `scripts/srd_gs/collect_results.py`
   - Fixed parsing for `scene/variant/eval/metrics.json`.

## Metrics Interpretation

- Rendering metrics are `null` because this smoke did not provide saved predicted/GT RGB render pairs to `eval_reflective_assets.py`.
- Geometry metrics are `null` because accepted GT geometry loading is not yet integrated into the eval CLI.
- Highlight leakage is available as an export-path diagnostic.
- No scientific improvement claim is made from this smoke.

## Known Limitations

- Training is only 20 iterations.
- SRD extra branch maps currently rely on renderer fallback due rasterizer feature-channel ABI limitations.
- `metrics.json` is generated, but most claim-bearing metrics are intentionally `null` without GT inputs.
- Panel image composition is not implemented.
- LPIPS is not integrated.

## Next Recommended Milestone

Milestone 10 should not start as a full paper-scale run until these are addressed:

- Add render/GT export for eval.
- Add accepted GT geometry loading for Shiny Blender Synthetic.
- Decide whether to implement multi-channel rasterizer support or a separate branch-map rasterizer.
- Run a longer single-scene SRD smoke before expanding to multiple scenes.
