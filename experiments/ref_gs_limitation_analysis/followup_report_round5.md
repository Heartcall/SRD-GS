# Ref-GS Limitation Pipeline Follow-up Report Round5

## 1. What Changed

- `experiments/ref_gs_limitation_analysis/run_component_sanity.sh`
  - Added real `SANITY_LOG_DIR` isolation.
  - Kept `STRICT=1` and `ROUND_NAME=...` behavior wired into generated summary/log filenames.
  - Passes env check output into the selected sanity log directory.
- `experiments/ref_gs_limitation_analysis/run_timing_probe.sh`
  - Added `TIMING_OUT_DIR`, `TIMING_LOG_DIR`, and `TIMING_SUMMARY_BASENAME`.
  - Default behavior remains compatible: `metrics/timing_probe/timing_summary.json/md`.
- `experiments/ref_gs_limitation_analysis/test_round3_pipeline.py`
  - Unit timing strict test now writes to a temporary metrics/log directory.
  - Component sanity strict test now writes to a temporary sanity log directory.
- `experiments/ref_gs_limitation_analysis/env_check.sh`
  - Added `ENV_CHECK_LOG_DIR` and `ENV_CHECK_LOG_FILE` for test/CI isolation.
- `experiments/ref_gs_limitation_analysis/README.md`
  - Updated strict, round-name, timing-output, and log-isolation notes.
- `utils/mesh_utils.py`
  - Added fallback helpers for missing `utils.render_utils`.
  - Made empty mesh post-processing safe.
- `experiments/ref_gs_limitation_analysis/export_mesh.py`
  - Records raw mesh counts and marks empty TSDF output as `status=NA`.
- Added `experiments/ref_gs_limitation_analysis/mesh_runtime_diagnosis_round5.md`.
- Added round5 timing artifacts:
  - `metrics/timing_probe/timing_summary_round5_dryrun.json/md`
  - `metrics/timing_probe/timing_summary_round5_real_train_nerf_iter2.json/md`
- Added round5 mesh smoke manifest:
  - `meshes/round5_ball_sanity/mesh_manifest.json`

## 2. Audit Consistency Fixes

1. `STRICT=1` is now actually connected in `run_component_sanity.sh`.
   Strict mode exits nonzero when requested training fails, an expected checkpoint
   is missing after training, export exits nonzero, eval exits nonzero, or a
   requested non-dry-run mesh command exits nonzero.
2. `ROUND_NAME` controls:
   - `component_sanity_${ROUND_NAME}_summary.md`
   - `component_sanity_${ROUND_NAME}_train.log`
   - `component_sanity_${ROUND_NAME}_export.log`
   - `component_sanity_${ROUND_NAME}_eval.log`
   - `component_sanity_${ROUND_NAME}_mesh.log`
   - `env_check_${ROUND_NAME}.txt` when called through the sanity runner
3. Timing tests no longer overwrite formal timing artifacts because they set
   temporary `TIMING_OUT_DIR`, `TIMING_LOG_DIR`, and `TIMING_SUMMARY_BASENAME`.
4. Formal round5 timing artifacts are:
   - real attempt: `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round5_real_train_nerf_iter2.json`
   - dry-run: `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round5_dryrun.json`
5. The default `timing_summary.json` is no longer the unit-test
   `definitely_missing_train_script.py` artifact. It currently mirrors the
   round5 real short-run attempt, which failed with exit code 1.
6. `output/ref_gs_limitation_timing/materials_iter2_round4/chkpnt2.pth` exists,
   but old round4 timing numbers were not reused because the formal default
   timing artifact had been overwritten by a test artifact.

## 3. What I Ran

| Command | Exit code | Notes |
| --- | ---: | --- |
| `python -m unittest experiments.ref_gs_limitation_analysis.test_round3_pipeline` before script fixes | 1 | Expected red test: temp timing/sanity outputs were not yet honored. |
| `TIMING_SUMMARY_BASENAME=timing_summary_round5_dryrun bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh --script train-NeRF.py --scene "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" --model output/ref_gs_limitation_timing/materials_iter2_round5 --iterations 2 --dry-run` | 0 | Wrote round5 dry-run timing artifact. |
| `TIMING_SUMMARY_BASENAME=timing_summary_round5_real_train_nerf_iter2 bash experiments/ref_gs_limitation_analysis/run_timing_probe.sh --strict --script train-NeRF.py --scene "/data/liuly/dataset/3DGS/NeRF Synthetic/materials" --model output/ref_gs_limitation_timing/materials_iter2_round5 --iterations 2` | 1 | Restricted-shell attempt failed; later true CUDA attempt also failed with CUBLAS initialization error. |
| `LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH" python - <<'PY' ... import PIL/open3d ... PY` | 0 | Open3D import succeeds when conda libstdc++ is preferred. |
| `LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH" python experiments/ref_gs_limitation_analysis/export_mesh.py --strict ... --out_mesh experiments/ref_gs_limitation_analysis/meshes/round5_ball_sanity/mesh.ply ...` in restricted shell | 1 | Failed before model construction: CUDA unavailable. |
| Same mesh command in true CUDA execution | 1 | Ran through rendering/TSDF; manifest records empty mesh. |

Final verification commands and exit codes are listed at the end of this report
after they are run.

## 4. Timing Artifact Status

Current default artifact:

- path: `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary.json`
- script: `train-NeRF.py`
- model: `output/ref_gs_limitation_timing/materials_iter2_round5`
- dry_run: `false`
- exit_code: `1`
- wall_clock_seconds: `7`
- peak_gpu_memory_mb: `822`
- peak_gpu_memory_reason: empty string, meaning `nvidia-smi` produced a value
- checkpoint_size_bytes: `NA`
- log_path: `experiments/ref_gs_limitation_analysis/sanity_logs/timing_probe_train-NeRF_iter2.log`

Round5 real short-run summary:

- `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round5_real_train_nerf_iter2.json`
- exit_code: `1`
- failure: `RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED when calling cublasCreate(handle)`
- checkpoint was not produced, so `checkpoint_size_bytes=NA`

Round5 dry-run summary:

- `experiments/ref_gs_limitation_analysis/metrics/timing_probe/timing_summary_round5_dryrun.json`
- exit_code: `0`
- dry_run: `true`
- peak_gpu_memory_mb: `NA`
- peak_gpu_memory_reason: `dry_run`

Pollution check:

- `metrics/timing_probe/timing_summary.json` is not
  `definitely_missing_train_script.py`.
- Round5 does not reproduce the round4 claimed successful timing short-run.
  Therefore L5 should be treated as audit-hardened but not newly closed by a
  successful round5 real run.

## 5. Component Sanity Strict Status

- `STRICT=1` with `SANITY_SCRIPT=definitely_missing_train_script.py` returns
  nonzero in the unit test.
- `ROUND_NAME=unit_strict` writes unit-specific filenames.
- With `SANITY_LOG_DIR` set, unit logs and `env_check_unit_strict.txt` are
  written under the temporary test directory, not the formal
  `experiments/ref_gs_limitation_analysis/sanity_logs` directory.
- Default non-strict behavior remains safe-fail: failures are logged and the
  script exits 0 unless `STRICT=1`.

## 6. Mesh Runtime Diagnosis

See `experiments/ref_gs_limitation_analysis/mesh_runtime_diagnosis_round5.md`.

Summary:

- Round4 GLIBCXX/libLerc failure is real and reproducible without an explicit
  conda library path.
- The conda environment has a `libstdc++.so.6` containing `GLIBCXX_3.4.29`.
- `LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"` lets Open3D import.
- After that fix, `utils.mesh_utils` exposed a missing `utils.render_utils`
  dependency, now covered by a local fallback.
- True CUDA mesh smoke then reached TSDF but produced an empty mesh:
  - manifest: `experiments/ref_gs_limitation_analysis/meshes/round5_ball_sanity/mesh_manifest.json`
  - status: `NA`
  - reason: `TSDF produced an empty mesh`
  - `num_vertices=0`
  - `num_triangles=0`
  - `mesh_exists=false`
  - `points_exists=true`

## 7. Updated Validation Status

| Limitation | Round4 status | Round5 status | Remaining gap |
| ---------- | ------------- | ------------- | ------------- |
| L1 PBR/component evaluation | Minimal true loop complete on 2-iteration ball checkpoint; `pbr_rgb_vs_render_gap.status=ok`; `ref_w/out_w` missing for synthetic ref render. | Left intact. Round4 manifest still exports `gt/pbr_rgb/render/diffuse/specular/spec/albedo/roughness/normal/depth/alpha/features`; gap remains ok. | Only 2-iteration smoke, not quality evidence. Full scene training/eval still needed. |
| L2 geometry sensitivity | Real mesh export attempted but blocked by GLIBCXX/libLerc. | GLIBCXX path diagnosed and bypassed with conda `LD_LIBRARY_PATH`; mesh import and TSDF reached. Real 1-view smoke still failed because TSDF produced an empty mesh. | Need trained checkpoint and more views; keep `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`; then run geometry metrics against accepted GT/eval points. |
| L3 real-scene env sensitivity | Env sphere checks existed from prior rounds. | Not rerun in round5. | Needs real-scene sweep; no new evidence this round. |
| L4 Sph-Mip/factorization ablation | Notes only; no implementation. | Unchanged. | no-Sph-Mip and no-factorization still require implementation. |
| L5 non-reflective overhead | Round4 report claimed successful 2-iteration timing, but default timing artifact was polluted by unit test. | Test pollution fixed. Default and round5-named timing artifacts are clean but the real short-run failed with CUBLAS initialization; dry-run succeeded. | Need rerun short timing in a stable CUDA environment before claiming a successful overhead smoke. |

## 8. Caveats

1. L1 is still a 2-iteration smoke result and does not represent model quality.
2. Full training was not run.
3. L2 is no longer blocked at the original GLIBCXX import point under
   `LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`, but it is still not
   closed because the round5 smoke mesh is empty.
4. L5 has clean, auditable artifacts, but the round5 real short-run did not
   succeed and did not produce a checkpoint.
5. no-Sph-Mip and no-factorization ablations are still not implemented.
6. External baselines are still not aligned.
7. The round5 timing GPU memory value comes from `nvidia-smi` polling during the
   failed run; it is runtime telemetry, not a successful-training peak.

## 9. Final Verification

| Command | Exit code | Result |
| --- | ---: | --- |
| `python -m unittest experiments.ref_gs_limitation_analysis.test_round3_pipeline` | 0 | 5 tests passed. |
| `python -m py_compile experiments/ref_gs_limitation_analysis/export_pbr_views.py experiments/ref_gs_limitation_analysis/evaluate_pbr.py experiments/ref_gs_limitation_analysis/evaluate_geometry.py experiments/ref_gs_limitation_analysis/export_mesh.py` | 0 | Syntax check passed. |
| `bash -n experiments/ref_gs_limitation_analysis/run_timing_probe.sh experiments/ref_gs_limitation_analysis/run_component_sanity.sh experiments/ref_gs_limitation_analysis/env_check.sh` | 0 | Shell syntax check passed. |
| `git diff --check` | 0 | No whitespace errors. |
| formal timing artifact pollution check | 0 | `timing_summary.json` reports `script=train-NeRF.py`, `exit_code=1`, `model=output/ref_gs_limitation_timing/materials_iter2_round5`; it is not the unit-test missing-script artifact. |
