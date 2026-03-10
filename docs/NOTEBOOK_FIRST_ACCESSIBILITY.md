# Notebook-First Accessibility Model

## The Core Idea

WarpLab should feel like a research instrument, not a build system.

The main user experience is:

1. open a notebook
2. edit or inspect a CUDA kernel
3. compile it
4. validate it
5. benchmark it
6. run an optimization loop
7. visualize the results

That loop is the product.

## Why The Repo Is Structured This Way

CUDA experimentation needs three things:

- interactive compilation
- fast benchmarking
- visual feedback

Notebooks are the best general-purpose interface for that workflow because they combine execution, narrative context, and results in one place.

WarpLab therefore uses:

- notebooks as the primary experimentation surface
- a Python orchestration layer for repeatable execution
- project directories to hold kernel code and benchmark/validation entry points
- optional containerization for advanced users and remote GPU hosts

## Supported Usage Modes

### 1. Notebook-first

The default interface is `notebooks/warplab_v1.ipynb`.

This is the best entry point for:

- first-time contributors
- research demos
- performance exploration
- teaching and sharing experiments

### 2. Local CLI / Python API

The same workflow is exposed through:

- `warplab.runner.run_project(...)`
- `python -m warplab`
- `warplab ...`

This is the repeatable automation layer behind the notebook.

### 3. Local Or Remote GPU Container

Advanced users should be able to run the same repo in a container and expose Jupyter from that environment.

That model gives you:

- reproducible user-space dependencies
- easier onboarding on Linux GPU machines
- a path to remote GPU hosts

## What "Fully Implemented" Means For This Idea

The notebook-first idea is only fully implemented when all of the following are true:

- a notebook can set up the environment with minimal friction
- the notebook can compile, validate, benchmark, and optimize a sample CUDA project
- the notebook produces visual output, not only logs
- the same logic is available through a normal Python API and CLI
- local users and container users run the same project format
- docs explain the cloud notebook path and the local/container path clearly

## What Exists In This Repo Now

- a notebook wrapper for the runner
- a CLI and Python runner
- a sample SAXPY project
- explicit candidate artifact handling
- validation/benchmark/report plumbing
- documentation for the repo roadmap and accessibility model

## What Still Depends On The Host Machine

WarpLab does not vendor the CUDA toolkit.

The host environment still needs:

- an NVIDIA GPU when running real kernels locally
- CUDA toolchain access such as `nvcc`
- Nsight Compute if profiling is desired

In browser notebook environments, the availability of GPU hardware and CUDA tools depends on the platform and its current quotas or runtime image.

## Design Principle

The notebook is the lab bench.

The Python package is the mechanism under the bench.

The container is the transport case for the whole instrument.
