# WarpLab

Self-optimizing workflows for CUDA kernels and GPU workloads.

WarpLab is an open-source notebook-first system that profiles, mutates, validates, benchmarks, and ranks CUDA kernel variants to discover faster configurations with reproducible evidence.

## Features

- **Notebook-first workflow**: Native to Jupyter for rapid research.
- **Correctness-gated optimization**: Never optimize a broken kernel.
- **Reliable benchmarking**: Robust statistics (median, CV) with warmups.
- **Profiler-informed mutation**: Use Nsight Compute metrics to guide search.
- **Prior-guided search**: Learn from previous runs across different GPUs.
- **Markdown experiment reports**: Durable evidence of every optimization run.

## Repository Structure

- `notebooks/`: WarpLab v1 driver notebooks.
- `warplab/`: Core Python package for compilation, benchmarking, and profiling.
- `projects/`: Templated CUDA kernel projects (e.g., SAXPY, Reduction).
- `runs/`: Temporary build artifacts for candidate kernels.
- `reports/`: Generated Markdown reports.
- `db/`: SQLite database for experiment history.

## Getting Started

1. Install dependencies: `pip install -e .`
2. Open `notebooks/warplab_v1.ipynb` in JupyterLab.
3. Configure your CUDA project in `projects/`.
4. Run the optimization loop.
