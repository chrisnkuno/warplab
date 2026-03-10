# Docker And Remote GPU Workflow

## Why This Exists

WarpLab should support a dual model:

- browser notebook for accessible experimentation
- containerized local or remote GPU execution for advanced users

That lets beginners use notebooks while experienced users keep the same repo and workflow on real machines.

## Files

- `Dockerfile`
- `.dockerignore`

## Build

From the repo root:

```bash
docker build -t warplab .
```

## Run Jupyter With GPU Access

On a machine with the NVIDIA container toolkit configured:

```bash
docker run --rm -it --gpus all -p 8888:8888 warplab
```

This starts JupyterLab inside the container using the repo's `uv` environment.

## Run The CLI Instead

```bash
docker run --rm -it --gpus all warplab uv run warplab projects/saxpy --root-dir /workspace
```

## Remote GPU Hosts

This same container approach maps cleanly onto remote GPU providers:

- build the image
- send it to a registry or remote build target
- launch the container on a GPU host
- expose Jupyter or run the CLI remotely

## Important Limits

The container path gives you reproducible user-space dependencies.

It does not remove the need for:

- an actual NVIDIA GPU on the host
- correct NVIDIA driver compatibility on the host
- container runtime GPU support

## Suggested Open-Source Model

For broad adoption, treat the repo as three layers:

1. notebook template for first use
2. Python package for reproducible execution
3. container for advanced or remote GPU users

That makes the project accessible without forcing every user into the same setup model.
