# Timing Probe Summary

- script: `train-NeRF.py`
- scene: `/data/liuly/dataset/3DGS/NeRF Synthetic/materials`
- model: `output/ref_gs_limitation_timing/materials_iter10`
- iterations: `10`
- dry_run: `True`
- exit_code: `0`
- wall_clock_seconds: `0`
- peak_gpu_memory_mb: `NA`
- checkpoint_size_bytes: `NA`
- log_path: `experiments/ref_gs_limitation_analysis/sanity_logs/timing_probe_train-NeRF_iter10.log`

## Command

```bash
python train-NeRF.py -s /data/liuly/dataset/3DGS/NeRF Synthetic/materials --eval --iterations 10 --save_iterations 10 --checkpoint_iterations 10 --test_iterations 10 --model_path output/ref_gs_limitation_timing/materials_iter10
```
