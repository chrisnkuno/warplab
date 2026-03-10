from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .env import get_env_fingerprint


def detect_notebook_environment() -> str:
    if "google.colab" in sys.modules:
        return "colab"
    if Path("/kaggle/working").exists():
        return "kaggle"
    return "local"


def collect_runtime_diagnostics() -> dict[str, object]:
    environment = detect_notebook_environment()
    fingerprint = get_env_fingerprint()
    tools = {
        "nvcc": shutil.which("nvcc"),
        "ncu": shutil.which("ncu"),
        "nvidia_smi": shutil.which("nvidia-smi"),
    }
    return {
        "environment": environment,
        "has_gpu_visibility": bool(tools["nvidia_smi"]),
        "has_nvcc": bool(tools["nvcc"]),
        "has_ncu": bool(tools["ncu"]),
        "tools": tools,
        "fingerprint": fingerprint,
    }


def notebook_bootstrap_snippet() -> str:
    return "\n".join(
        [
            "!git clone <your-warplab-fork-or-repo-url>",
            "%cd warplab",
            "%pip install uv",
            "!uv sync --dev",
        ]
    )


def runtime_warnings(diagnostics: dict[str, object]) -> list[str]:
    warnings = []
    if not diagnostics.get("has_gpu_visibility"):
        warnings.append("No GPU visibility detected via nvidia-smi.")
    if not diagnostics.get("has_nvcc"):
        warnings.append("CUDA compiler `nvcc` is not available in this runtime.")
    if not diagnostics.get("has_ncu"):
        warnings.append("Nsight Compute `ncu` is not available; profiling will be limited.")
    return warnings
