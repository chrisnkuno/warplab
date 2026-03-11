from __future__ import annotations

import json
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


def notebook_bootstrap_snippet(repo_url: str = "<your-warplab-fork-or-repo-url>", repo_dir: str = "warplab") -> str:
    return "\n".join(
        [
            f"!git clone {repo_url} {repo_dir}",
            f"%cd {repo_dir}",
            "%pip install uv",
            "!uv sync --dev",
        ]
    )


def validation_cell_snippet(repo_dir: str = "warplab", repo_url: str | None = None) -> str:
    lines = [
        "import json, subprocess, sys",
        "from pathlib import Path",
        "",
        f"ROOT_DIR = Path('{repo_dir}').resolve()",
    ]
    if repo_url:
        lines.extend(
            [
                "if not ROOT_DIR.exists():",
                f"    subprocess.run(['git', 'clone', '--depth', '1', '{repo_url}', '{repo_dir}'], check=True)",
                f"    ROOT_DIR = Path('{repo_dir}').resolve()",
            ]
        )
    else:
        lines.extend(
            [
                "if not ROOT_DIR.exists():",
                "    raise FileNotFoundError(f'Repo directory not found: {ROOT_DIR}')",
            ]
        )
    lines.extend(
        [
            "",
            "subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)",
            "subprocess.run(['uv', 'sync', '--dev'], cwd=ROOT_DIR, check=True)",
            "if str(ROOT_DIR) not in sys.path:",
            "    sys.path.insert(0, str(ROOT_DIR))",
            "",
            "from warplab.cloud import collect_runtime_diagnostics, runtime_warnings",
            "",
            "diagnostics = collect_runtime_diagnostics()",
            "warnings = runtime_warnings(diagnostics)",
            "print(json.dumps(diagnostics, indent=2))",
            "if warnings:",
            "    print('\\nWarnings:')",
            "    for warning in warnings:",
            "        print('-', warning)",
        ]
    )
    return "\n".join(lines)


def format_runtime_report(diagnostics: dict[str, object]) -> str:
    warnings = runtime_warnings(diagnostics)
    payload = {"diagnostics": diagnostics, "warnings": warnings}
    return json.dumps(payload, indent=2)


def runtime_warnings(diagnostics: dict[str, object]) -> list[str]:
    warnings = []
    if not diagnostics.get("has_gpu_visibility"):
        warnings.append("No GPU visibility detected via nvidia-smi.")
    if not diagnostics.get("has_nvcc"):
        warnings.append("CUDA compiler `nvcc` is not available in this runtime.")
    if not diagnostics.get("has_ncu"):
        warnings.append("Nsight Compute `ncu` is not available; profiling will be limited.")
    return warnings
