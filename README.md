# WarpLab

Self-optimizing workflows for CUDA kernels and GPU workloads.

WarpLab is an open-source, notebook-first CUDA autotuning project. It is designed around one loop:

1. inspect or edit a CUDA kernel
2. compile it
3. validate it
4. benchmark it
5. optimize it
6. visualize the results

The notebook is the lab bench. The Python package is the mechanism underneath it.

## Current Status

WarpLab now includes:

- an executable optimization runner in `warplab.runner`
- a CLI entry point via `python -m warplab` or `warplab`
- explicit artifact paths for baseline and candidate binaries
- correctness-gated candidate evaluation
- SQLite-backed priors and run history
- Markdown report generation
- a notebook template for interactive CUDA experimentation
- a container path for local or remote GPU execution

WarpLab is still early-stage. The main sample projects are `projects/saxpy`, `projects/reduction`, and `projects/stencil`.

## Requirements

- Python 3.11+
- NVIDIA GPU drivers
- CUDA toolkit with `nvcc`
- Nsight Compute (`ncu`) if you want baseline profiling

## Features

- **Notebook-first workflow**: Native to Jupyter for rapid research.
- **Correctness-gated optimization**: Never optimize a broken kernel.
- **Reliable benchmarking**: Median, mean, standard deviation, and CV from explicit warmup/timed runs.
- **Profiler-informed mutation**: Use Nsight Compute metrics to guide search.
- **Prior-guided search**: Learn from previous runs across different GPUs.
- **Markdown experiment reports**: Durable evidence of every optimization run.
- **Open-source accessibility model**: notebook for newcomers, CLI/container for advanced users

## Repository Structure

- `notebooks/`: Notebook wrappers around the package runner.
- `warplab/`: Core Python package for compilation, validation, benchmarking, profiling, search, and reporting.
- `projects/`: CUDA kernel projects in WarpLab project format.
- `runs/`: Temporary build artifacts for candidate kernels.
- `reports/`: Generated Markdown reports.
- `db/`: SQLite database for experiment history.
- `docs/`: Product model, quickstarts, Docker workflow, and repo roadmap.

## Getting Started

1. Sync the environment:

```bash
uv sync --dev
```

2. Run the CLI:

```bash
uv run warplab run projects/saxpy --root-dir .
```

3. Or open `notebooks/warplab_v1.ipynb` in JupyterLab and run the wrapper cells.
4. Review the generated report in `reports/` and the run artifacts in `runs/`.

Notebook workflow:

```bash
uv run jupyter lab
```

For local secrets and hosted notebook helpers:

- copy `.env.example` to `.env` if you want WarpLab to read a Kaggle token from the repo root
- see `docs/KAGGLE_SETUP.md` for the public Kaggle onboarding path

## Open-Source Usage Modes

WarpLab is intended to work in three modes:

### 1. Browser notebook

Use a hosted notebook environment when you want the lowest-friction entry point and the platform provides GPU access.

### 2. Local notebook or CLI

Use `uv run jupyter lab` or `uv run warplab run ...` when you want the same workflow on your own machine.

For a quick runtime check outside notebooks:

```bash
uv run warplab doctor
```

### 3. Containerized local or remote GPU

Use the `Dockerfile` when you want the same repo in a reproducible environment on a local GPU host or remote GPU provider.

## Project Format

Each project directory should contain:

- `project.yaml`
- `kernel.cu`
- one benchmark executable source
- one validator executable source

The current command templates support placeholders such as:

- `{artifact}`
- `{size}`
- `{warmups}`
- `{repeats}`
- `{atol}`
- `{rtol}`
- `{flags}`

## Additional Documentation

- [`docs/README.md`](docs/README.md)
- [`docs/NOTEBOOK_FIRST_ACCESSIBILITY.md`](docs/NOTEBOOK_FIRST_ACCESSIBILITY.md)
- [`docs/NOTEBOOK_QUICKSTART.md`](docs/NOTEBOOK_QUICKSTART.md)
- [`docs/CLOUD_NOTEBOOK_COMPATIBILITY.md`](docs/CLOUD_NOTEBOOK_COMPATIBILITY.md)
- [`docs/KAGGLE_SETUP.md`](docs/KAGGLE_SETUP.md)
- [`docs/KAGGLE_SAXPY_WALKTHROUGH.md`](docs/KAGGLE_SAXPY_WALKTHROUGH.md)
- [`docs/DOCKER_AND_REMOTE_GPU.md`](docs/DOCKER_AND_REMOTE_GPU.md)
- [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md)
- [`docs/OPEN_SOURCE_GAPS_AND_NEXT_STEPS.md`](docs/OPEN_SOURCE_GAPS_AND_NEXT_STEPS.md)
- [`docs/REPO_ASSESSMENT_AND_COMPLETION_GUIDE.md`](docs/REPO_ASSESSMENT_AND_COMPLETION_GUIDE.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
