# Contributing

## Goal

WarpLab is an open-source CUDA experimentation framework.

Contributions should improve one or more of these areas:

- notebook-first usability
- correctness of compile/validate/benchmark workflows
- search quality
- result reproducibility
- documentation

## Local Development

Use `uv` for the Python environment.

```bash
uv sync --dev
```

Common commands:

```bash
uv run pytest -q
uv run warplab --help
uv run jupyter lab
```

## Repo Expectations

Before opening a change, make sure:

- the Python environment syncs with `uv`
- tests pass
- notebook-facing workflows still make sense
- docs are updated when behavior changes

## What Needs Documentation

If your change affects the user workflow, update at least one of:

- `README.md`
- `docs/README.md`
- `docs/NOTEBOOK_QUICKSTART.md`
- `docs/DOCKER_AND_REMOTE_GPU.md`
- `docs/REPO_ASSESSMENT_AND_COMPLETION_GUIDE.md`

## Preferred Contribution Areas

- new sample CUDA projects
- stronger profiling and benchmark methodology
- better result visualization
- safer and smarter search strategies
- cloud-notebook onboarding improvements
- container and remote-GPU workflow improvements

## Open-Source Product Principle

The repo should remain understandable to someone who lands on it from a notebook link.

That means:

- the notebook story must stay coherent
- the CLI story must stay reproducible
- docs should explain both clearly
