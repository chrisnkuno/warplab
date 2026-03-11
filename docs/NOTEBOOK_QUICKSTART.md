# Notebook Quickstart

## Recommended Flow

Use the notebook when you want the full CUDA experimentation loop in one place:

1. environment setup
2. kernel inspection or editing
3. compile step
4. correctness validation
5. benchmark run
6. optimization loop
7. result visualization

The canonical notebook for that flow is:

- `notebooks/warplab_v1.ipynb`

## Local Jupyter Workflow

From the repo root:

```bash
uv sync --dev
uv run jupyter lab
```

Then open:

- `notebooks/warplab_v1.ipynb`

## Colab Or Kaggle Workflow

The browser-notebook path is best treated as a lightweight clone-and-run flow.

Recommended steps:

1. clone or upload the repo into the notebook workspace
2. install Python dependencies
3. use `warplab.cloud` runtime diagnostics to confirm that the runtime actually exposes a GPU and CUDA compiler access
4. open `notebooks/warplab_v1.ipynb`
5. run the environment setup and experiment cells

Notes:

- GPU availability depends on the notebook platform and the current runtime you receive.
- CUDA compiler access may differ between platforms and over time.
- treat the notebook as the frontend and the `warplab` package as the backend logic

## Verified Kaggle Path

Kaggle is now validated as a real WarpLab runtime for diagnostics and browser-based CUDA access.

Verified runtime facts from March 11, 2026:

- GPU: `Tesla P100-PCIE-16GB`
- `nvcc`: available
- `ncu`: available
- `nvidia-smi`: available

For a packaged `saxpy` run notebook, use:

```bash
uv run warplab kaggle-project-package \
  --project projects/saxpy \
  --output-dir build/kaggle-saxpy \
  --title "WarpLab SAXPY Kaggle Run" \
  --slug warplab-saxpy-kaggle-run \
  --candidate-count 8
```

Then push it with the Kaggle CLI. See:

- `docs/KAGGLE_SAXPY_WALKTHROUGH.md`

## What The Notebook Covers

The notebook is intentionally organized around the research loop:

- environment setup
- kernel source inspection
- baseline compilation
- baseline validation
- baseline benchmarking
- full optimization run
- performance visualization

## Editing Kernels

The sample project lives under:

- `projects/saxpy/`

The notebook shows the kernel source so users can inspect the implementation quickly. More advanced editing is usually easiest from the file browser or editor connected to the notebook environment.

## When To Leave The Notebook

Use the CLI or Python API when:

- you want repeatable automation
- you want to integrate WarpLab into a larger workflow
- you want to run experiments outside Jupyter

Equivalent CLI pattern:

```bash
uv run warplab projects/saxpy --root-dir .
```
