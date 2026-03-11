# Cloud Notebook Compatibility

This document tracks the browser-notebook story honestly.

## Current Status

WarpLab is designed for cloud notebooks, but cloud notebook availability is controlled by the platform.

What the repo now provides:

- a notebook-first workflow
- runtime diagnostics via `warplab.cloud`
- a notebook structure that matches the intended CUDA experimentation loop
- docs for cloud notebook usage

## Compatibility Matrix

| Environment | Status | Notes |
| --- | --- | --- |
| Local Jupyter + `uv` | Verified in repo workflow | Primary maintained path |
| Local CLI + `uv` | Verified in repo workflow | `uv run warplab ...` |
| Docker + GPU host | Scaffolded | Dockerfile and docs provided |
| Google Colab | Documented, not verified in CI | GPU/toolchain depends on runtime |
| Kaggle Notebooks | Verified manually on March 11, 2026 | Tesla P100 runtime exposed `nvcc`, `ncu`, and `nvidia-smi` |

## Copy-Paste Bootstrap

Use this as a starting point in a hosted notebook after cloning or mounting the repo:

```python
from warplab.cloud import notebook_bootstrap_snippet
print(notebook_bootstrap_snippet())
```

Equivalent commands:

```bash
!git clone <your-warplab-fork-or-repo-url>
%cd warplab
%pip install uv
!uv sync --dev
```

## Single Validation Cell

Use this when you want one notebook cell that both syncs the repo and prints runtime diagnostics:

```python
from warplab.cloud import validation_cell_snippet
print(validation_cell_snippet("warplab"))
```

## Runtime Checks

Use:

```python
from warplab.cloud import collect_runtime_diagnostics, runtime_warnings

diagnostics = collect_runtime_diagnostics()
warnings = runtime_warnings(diagnostics)
diagnostics, warnings
```

This helps answer:

- am I actually on a GPU-visible runtime?
- is `nvcc` available?
- is `ncu` available?

## Outside Colab And Kaggle

The same runtime-check path can be used in:

- local JupyterLab
- VS Code notebooks
- JupyterHub
- Docker-hosted Jupyter
- remote SSH or port-forwarded Jupyter sessions
- local shell via `uv run warplab doctor`

## Verified Kaggle Runtime

The Kaggle validation notebook was run successfully on March 11, 2026 with:

- GPU: `Tesla P100-PCIE-16GB`
- compute capability: `6.0`
- CUDA: `12.5`
- `nvcc`: available
- `ncu`: available
- `nvidia-smi`: available

The follow-up step is a full sample-project run, documented in:

- `docs/KAGGLE_SAXPY_WALKTHROUGH.md`

## What Still Needs Human Validation

- a real Colab run from a clean session
- repeated Kaggle runs for more than one sample project
- confirmation that the full optimization loop is stable across notebook restarts
- a short list of known workarounds when `nvcc` is not present
