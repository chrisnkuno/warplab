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


def project_run_cell_snippet(
    project: str = "projects/saxpy",
    repo_dir: str = "warplab",
    candidate_count: int = 8,
    profile: bool = True,
) -> str:
    args = [
        "uv",
        "run",
        "warplab",
        "str(PROJECT_PATH)",
        "--root-dir",
        "str(ROOT_DIR)",
        "--candidate-count",
        str(candidate_count),
    ]
    if not profile:
        args.append("--no-profile")

    rendered_args = ", ".join(
        [f"'{item}'" if not item.startswith("str(") else item for item in args]
    )
    return "\n".join(
        [
            "import json, subprocess",
            "from pathlib import Path",
            "",
            f"ROOT_DIR = Path('{repo_dir}').resolve()",
            f"PROJECT_PATH = ROOT_DIR / '{project}'",
            "if not PROJECT_PATH.exists():",
            "    raise FileNotFoundError(f'Project path not found: {PROJECT_PATH}')",
            "",
            "command = [" + rendered_args + "]",
            "try:",
            "    result = subprocess.run(command, cwd=ROOT_DIR, check=True, capture_output=True, text=True)",
            "except subprocess.CalledProcessError as exc:",
            "    if exc.stdout:",
            "        print('WarpLab stdout:')",
            "        print(exc.stdout)",
            "    if exc.stderr:",
            "        print('WarpLab stderr:')",
            "        print(exc.stderr)",
            "    raise",
            "print(result.stdout)",
            "summary = json.loads(result.stdout)",
            "summary_path = Path(summary['run_summary_path'])",
            "report_path = summary.get('report_path')",
            "print(json.dumps({",
            "    'run_id': summary['run_id'],",
            "    'project_name': summary['project_name'],",
            "    'baseline_latency_ms': summary['baseline_latency_ms'],",
            "    'best_candidate': summary.get('best_candidate', {}),",
            "    'run_summary_path': str(summary_path),",
            "    'report_path': report_path,",
            "}, indent=2))",
        ]
    )


def project_results_cell_snippet() -> str:
    return "\n".join(
        [
            "import json",
            "from pathlib import Path",
            "",
            "import pandas as pd",
            "import plotly.express as px",
            "from IPython.display import Markdown, display",
            "",
            "summary_payload = json.loads(summary_path.read_text())",
            "rows = []",
            "for item in summary_payload['results']:",
            "    if not item.get('benchmark_success'):",
            "        continue",
            "    rows.append({",
            "        'candidate_id': item['id'],",
            "        'latency_ms': item['latency_ms'],",
            "        'speedup': item['speedup'],",
            "        'cv': item['cv'],",
            "        'block_size': item['config']['params'].get('block_size'),",
            "        'unroll': item['config']['params'].get('unroll'),",
            "        'vector_width': item['config']['params'].get('vector_width'),",
            "    })",
            "",
            "df = pd.DataFrame(rows).sort_values('speedup', ascending=False)",
            "display(df)",
            "if not df.empty:",
            "    fig = px.scatter(",
            "        df,",
            "        x='latency_ms',",
            "        y='speedup',",
            "        color='vector_width',",
            "        hover_data=['candidate_id', 'block_size', 'unroll', 'cv'],",
            "        title='WarpLab SAXPY Candidates: Latency vs Speedup',",
            "    )",
            "    fig.show()",
            "if summary.get('report_path'):",
            "    report_text = Path(summary['report_path']).read_text()",
            "    display(Markdown('## Generated Report'))",
            "    display(Markdown(report_text))",
        ]
    )


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
