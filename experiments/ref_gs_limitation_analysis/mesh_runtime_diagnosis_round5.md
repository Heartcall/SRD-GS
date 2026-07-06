# Mesh Runtime Diagnosis Round5

## Failure From Round4

`experiments/ref_gs_limitation_analysis/meshes/round4_ball_sanity/mesh_manifest.json`
recorded a real, non-dry-run mesh export attempt with:

- `checkpoint_exists=true`
- `status=NA`
- reason:
  `/lib/x86_64-linux-gnu/libstdc++.so.6: version GLIBCXX_3.4.29 not found (required by /home/liuly/anaconda3/envs/ref_gs/lib/python3.7/site-packages/PIL/../../.././libLerc.so.4)`

## Python And Import Checks

Command:

```bash
python - <<'PY'
import sys
print(sys.executable)
try:
    import PIL
    print("PIL", PIL.__file__)
except Exception as e:
    print("PIL import failed:", e)
try:
    import open3d
    print("open3d", open3d.__file__)
except Exception as e:
    print("open3d import failed:", e)
PY
```

Result without an explicit conda library path:

- Python executable: `/home/liuly/anaconda3/envs/ref_gs/bin/python`
- PIL import: ok, `/home/liuly/anaconda3/envs/ref_gs/lib/python3.7/site-packages/PIL/__init__.py`
- Open3D import: failed with the same `GLIBCXX_3.4.29` / `libLerc.so.4` error

## Conda libstdc++ Check

Command:

```bash
python - <<'PY'
import os
prefix = os.environ.get("CONDA_PREFIX")
print("CONDA_PREFIX", prefix)
if prefix:
    print(os.path.join(prefix, "lib", "libstdc++.so.6"))
PY
strings "$CONDA_PREFIX/lib/libstdc++.so.6" | grep GLIBCXX_3.4.29 || true
```

Result:

- `CONDA_PREFIX=/home/liuly/anaconda3/envs/ref_gs`
- conda libstdc++ path: `/home/liuly/anaconda3/envs/ref_gs/lib/libstdc++.so.6`
- `GLIBCXX_3.4.29` is present in the conda `libstdc++.so.6`

## LD_LIBRARY_PATH Attempt

Command:

```bash
LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH" python - <<'PY'
import sys, os
print("executable", sys.executable)
print("CONDA_PREFIX", os.environ.get("CONDA_PREFIX"))
import PIL
print("PIL ok", PIL.__file__)
import open3d
print("open3d ok", open3d.__file__)
PY
```

Result:

- PIL import: ok
- Open3D import: ok, `/home/liuly/anaconda3/envs/ref_gs/lib/python3.7/site-packages/open3d/__init__.py`

Interpretation: the round4 `GLIBCXX_3.4.29` failure is reproducibly avoided by
preferring the conda environment library directory for the mesh command. No
system library was modified.

## Mesh Smoke After Runtime Fix

Command:

```bash
LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH" \
python experiments/ref_gs_limitation_analysis/export_mesh.py --strict \
  --source_path "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball" \
  --model_path "output/ref_gs_limitation_sanity/ball_iter2" \
  --checkpoint "output/ref_gs_limitation_sanity/ball_iter2/chkpnt2.pth" \
  --split test \
  --max_views 1 \
  --depth_ratio 1.0 \
  --voxel_size 0.004 \
  --sdf_trunc 0.02 \
  --render_func ref \
  --out_mesh experiments/ref_gs_limitation_analysis/meshes/round5_ball_sanity/mesh.ply \
  --out_points experiments/ref_gs_limitation_analysis/meshes/round5_ball_sanity/points.ply
```

Results:

- restricted shell attempt: failed before model construction with `CUDA is not available; Ref-GS model construction uses .cuda().`
- true CUDA attempt: ran through camera loading, rendering, TSDF integration, and point export
- mesh manifest: `experiments/ref_gs_limitation_analysis/meshes/round5_ball_sanity/mesh_manifest.json`
- status: `NA`
- reason: `TSDF produced an empty mesh`
- `num_vertices=0`
- `num_triangles=0`
- `mesh_exists=false`
- `points_exists=true`

## Code-Side Audit Fixes

- `utils/mesh_utils.py` now has a fallback for the missing `utils.render_utils`
  helpers so mesh import does not fail before reaching TSDF.
- `post_process_mesh` now handles empty meshes without hiding the real failure
  behind an index error.
- `export_mesh.py` records raw and post-processed vertex/triangle counts and
  marks empty TSDF output as `status=NA`.

## Next Step

For L2, run the same mesh command with:

```bash
LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
```

on a trained checkpoint and more than one view. The round5 2-iteration,
1-view smoke proves the runtime can reach TSDF under the conda library path, but
it does not close geometry evaluation because the mesh is empty.
