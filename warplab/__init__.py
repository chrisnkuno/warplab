"""WarpLab package."""

__all__ = ["run_project"]


def __getattr__(name: str):
    if name == "run_project":
        from .runner import run_project

        return run_project
    raise AttributeError(f"module 'warplab' has no attribute {name!r}")
