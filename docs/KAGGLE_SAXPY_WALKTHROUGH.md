# Kaggle SAXPY Walkthrough

This is the first packaged WarpLab sample-project workflow for Kaggle.

As of March 11, 2026, Kaggle was verified to provide:

- `Tesla P100-PCIE-16GB`
- `nvcc` at `/usr/local/cuda/bin/nvcc`
- `ncu` at `/usr/local/cuda/bin/ncu`
- `nvidia-smi` at `/opt/bin/nvidia-smi`

That verification covers the runtime and CUDA toolchain.
The full `saxpy` optimization path should still be treated as beta until repeated end-to-end runs are stable.

## Goal

Run the full WarpLab loop for `projects/saxpy` from a Kaggle notebook:

1. bootstrap the repo
2. validate runtime diagnostics
3. compile and validate the sample project
4. benchmark and search candidates
5. inspect the generated summary, report, and plots

Before running this walkthrough, complete:

- `docs/KAGGLE_SETUP.md`

## Build The Kaggle Package

From the repo root:

Smoke-test first:

```bash
uv run warplab kaggle-project-package \
  --project projects/saxpy \
  --output-dir build/kaggle-saxpy \
  --title "WarpLab SAXPY Kaggle Run" \
  --slug warplab-saxpy-kaggle-run \
  --candidate-count 2 \
  --no-profile
```

Then increase the search budget once the base path is stable.

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
UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels status <your-kaggle-username>/warplab-saxpy-kaggle-run
```

## Download Output

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run kaggle kernels output <your-kaggle-username>/warplab-saxpy-kaggle-run -p build/kaggle-saxpy-output
```

## What To Look For

Successful output should include:

- runtime diagnostics JSON
- a CLI result JSON with `run_id`, `baseline_latency_ms`, and `best_candidate`
- a generated Markdown report path
- a run summary path under `reports/`
- a DataFrame and scatter plot of successful candidates

## Notes

- start with `--candidate-count 2 --no-profile` for the first smoke test
- increase the candidate count only after the smoke test succeeds
- Keep profiling enabled if `ncu` is present. Use `--no-profile` only when startup time matters more than diagnostics.
- Kaggle logs can repeat package-install output because the hosted execution stack mirrors notebook cell streams into multiple output channels.
