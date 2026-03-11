# Kaggle SAXPY Walkthrough

This is the first fully validated browser-runtime path for WarpLab.

As of March 11, 2026, Kaggle was verified to provide:

- `Tesla P100-PCIE-16GB`
- `nvcc` at `/usr/local/cuda/bin/nvcc`
- `ncu` at `/usr/local/cuda/bin/ncu`
- `nvidia-smi` at `/opt/bin/nvidia-smi`

## Goal

Run the full WarpLab loop for `projects/saxpy` from a Kaggle notebook:

1. bootstrap the repo
2. validate runtime diagnostics
3. compile and validate the sample project
4. benchmark and search candidates
5. inspect the generated summary, report, and plots

## Build The Kaggle Package

From the repo root:

```bash
uv run warplab kaggle-project-package \
  --project projects/saxpy \
  --output-dir build/kaggle-saxpy \
  --title "WarpLab SAXPY Kaggle Run" \
  --slug warplab-saxpy-kaggle-run \
  --candidate-count 8
```

This creates a Kaggle notebook package with:

- runtime diagnostics
- a `saxpy` optimization run
- result inspection and plotting cells

## Push The Notebook

```bash
set -a && . ./.env && set +a && UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels push -p build/kaggle-saxpy
```

## Check Status

```bash
set -a && . ./.env && set +a && UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels status ckagabe/warplab-saxpy-kaggle-run
```

## Download Output

```bash
set -a && . ./.env && set +a && UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels output ckagabe/warplab-saxpy-kaggle-run -p build/kaggle-saxpy-output
```

## What To Look For

Successful output should include:

- runtime diagnostics JSON
- a CLI result JSON with `run_id`, `baseline_latency_ms`, and `best_candidate`
- a generated Markdown report path
- a run summary path under `reports/`
- a DataFrame and scatter plot of successful candidates

## Notes

- `--candidate-count 8` is a reasonable first Kaggle run. Increase it once the base path is stable.
- Keep profiling enabled if `ncu` is present. Use `--no-profile` only when startup time matters more than diagnostics.
- Kaggle logs can repeat package-install output because the hosted execution stack mirrors notebook cell streams into multiple output channels.
