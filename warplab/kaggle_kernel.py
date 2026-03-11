from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .cloud import project_results_cell_snippet, project_run_cell_snippet, validation_cell_snippet
from .kaggle_api import kaggle_credentials


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


def kaggle_kernel_metadata(
    username: str,
    slug: str,
    title: str,
    code_file: str,
    enable_gpu: bool = True,
    enable_internet: bool = True,
    is_private: bool = True,
) -> dict[str, Any]:
    return {
        "id": f"{username}/{slug}",
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": is_private,
        "enable_gpu": enable_gpu,
        "enable_internet": enable_internet,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }


def _copy_repo_snapshot(output_dir: Path, repo_dir_name: str) -> Path:
    root_dir = Path.cwd().resolve()
    staged_repo_dir = output_dir / repo_dir_name

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {".git", ".venv", ".pytest_cache", ".mypy_cache", "__pycache__", ".ipynb_checkpoints"}
        path = Path(directory).resolve()
        try:
            relative = path.relative_to(root_dir)
        except ValueError:
            relative = None

        if relative is None or relative == Path():
            ignored.update({"build", "runs", "reports", "db"})

        return {name for name in names if name in ignored}

    if staged_repo_dir.exists():
        shutil.rmtree(staged_repo_dir)
    shutil.copytree(root_dir, staged_repo_dir, ignore=ignore)
    return staged_repo_dir


def discover_repo_url(root_dir: Path | None = None) -> str | None:
    repo_root = (root_dir or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    url = result.stdout.strip()
    return url or None


def kaggle_validation_notebook(repo_dir: str = "warplab", repo_url: str | None = None) -> dict[str, Any]:
    cell_source = validation_cell_snippet(repo_dir, repo_url=repo_url)
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "overview",
                "metadata": {},
                "source": [
                    "# WarpLab Kaggle Runtime Validation\n",
                    "\n",
                    "This notebook validates whether the Kaggle runtime has the prerequisites needed for WarpLab GPU experiments.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "runtime-check",
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in cell_source.splitlines()],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def kaggle_project_notebook(
    project: str = "projects/saxpy",
    repo_dir: str = "warplab",
    repo_url: str | None = None,
    candidate_count: int = 8,
    profile: bool = True,
) -> dict[str, Any]:
    diagnostics_cell = validation_cell_snippet(repo_dir, repo_url=repo_url)
    run_cell = project_run_cell_snippet(
        project=project,
        repo_dir=repo_dir,
        candidate_count=candidate_count,
        profile=profile,
    )
    results_cell = project_results_cell_snippet()
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "overview",
                "metadata": {},
                "source": [
                    "# WarpLab Project Run\n",
                    "\n",
                    f"This notebook validates the Kaggle runtime and executes `{project}` through the WarpLab CLI.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "runtime-check",
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in diagnostics_cell.splitlines()],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "run-project",
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in run_cell.splitlines()],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "inspect-results",
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in results_cell.splitlines()],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_kaggle_kernel_package(
    output_dir: Path,
    username: str | None,
    title: str = "WarpLab Kaggle Runtime Validation",
    slug: str | None = None,
    repo_dir: str = "warplab",
    enable_gpu: bool = True,
    enable_internet: bool = True,
    is_private: bool = True,
    repo_url: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not username:
        username = kaggle_credentials(output_dir.parent.parent if output_dir.parent.parent.exists() else Path.cwd()).get("username")
    if not username:
        raise ValueError("A Kaggle username is required to build kernel metadata id.")
    slug = slug or _slugify(title)
    notebook_name = f"{slug}.ipynb"
    notebook_path = output_dir / notebook_name
    metadata_path = output_dir / "kernel-metadata.json"

    _copy_repo_snapshot(output_dir, repo_dir)
    repo_url = repo_url or discover_repo_url()

    with open(notebook_path, "w") as f:
        json.dump(kaggle_validation_notebook(repo_dir, repo_url=repo_url), f, indent=2)

    metadata = kaggle_kernel_metadata(
        username=username,
        slug=slug,
        title=title,
        code_file=notebook_name,
        enable_gpu=enable_gpu,
        enable_internet=enable_internet,
        is_private=is_private,
    )
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return output_dir


def write_kaggle_project_package(
    output_dir: Path,
    project: str = "projects/saxpy",
    username: str | None = None,
    title: str = "WarpLab SAXPY Kaggle Run",
    slug: str | None = None,
    repo_dir: str = "warplab",
    enable_gpu: bool = True,
    enable_internet: bool = True,
    is_private: bool = True,
    repo_url: str | None = None,
    candidate_count: int = 8,
    profile: bool = True,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not username:
        username = kaggle_credentials(output_dir.parent.parent if output_dir.parent.parent.exists() else Path.cwd()).get("username")
    if not username:
        raise ValueError("A Kaggle username is required to build kernel metadata id.")
    slug = slug or _slugify(title)
    notebook_name = f"{slug}.ipynb"
    notebook_path = output_dir / notebook_name
    metadata_path = output_dir / "kernel-metadata.json"

    _copy_repo_snapshot(output_dir, repo_dir)
    repo_url = repo_url or discover_repo_url()

    with open(notebook_path, "w") as f:
        json.dump(
            kaggle_project_notebook(
                project=project,
                repo_dir=repo_dir,
                repo_url=repo_url,
                candidate_count=candidate_count,
                profile=profile,
            ),
            f,
            indent=2,
        )

    metadata = kaggle_kernel_metadata(
        username=username,
        slug=slug,
        title=title,
        code_file=notebook_name,
        enable_gpu=enable_gpu,
        enable_internet=enable_internet,
        is_private=is_private,
    )
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return output_dir
