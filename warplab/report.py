import json
from pathlib import Path
from typing import Any


def _format_ms(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.4f} ms"
    except (TypeError, ValueError):
        return "N/A"

def generate_markdown_report(
    run_id: str, 
    project_name: str, 
    fingerprint: dict[str, Any],
    baseline: dict[str, Any], 
    best: dict[str, Any], 
    bottleneck_diagnosis: dict[str, str],
    reports_dir: Path,
    run_summary_path: Path | None = None,
    run_root: Path | None = None,
    evaluated_count: int | None = None,
    successful_count: int | None = None,
    seed: int | None = None,
    early_stop_reason: str | None = None,
    best_profile_path: Path | None = None,
):
    reports_dir.mkdir(parents=True, exist_ok=True)
    evaluation_summary = ""
    if evaluated_count is not None or successful_count is not None or seed is not None:
        evaluation_summary = "\n## Evaluation Summary\n"
        if evaluated_count is not None:
            evaluation_summary += f"- Evaluated candidates: {evaluated_count}\n"
        if successful_count is not None:
            evaluation_summary += f"- Successful benchmarked candidates: {successful_count}\n"
        if seed is not None:
            evaluation_summary += f"- Search seed: {seed}\n"
        if early_stop_reason:
            evaluation_summary += f"- Early stop: {early_stop_reason}\n"

    artifact_summary = ""
    if run_root or run_summary_path or best_profile_path:
        artifact_summary = "\n## Artifacts\n"
        if run_root:
            artifact_summary += f"- Run root: `{run_root}`\n"
        if run_summary_path:
            artifact_summary += f"- JSON run summary: `{run_summary_path}`\n"
        if best_profile_path:
            artifact_summary += f"- Best-candidate profile: `{best_profile_path}`\n"

    report_content = f"""# WarpLab Report — {project_name}

## Project Metadata
- Project: {project_name}
- Run ID: `{run_id}`
- Timestamp: {fingerprint.get('timestamp')}

## Environment Fingerprint
- GPU: {fingerprint.get('gpu_name')}
- Compute Capability: {fingerprint.get('compute_capability')}
- CUDA Version: {fingerprint.get('cuda_version')}
- OS: {fingerprint.get('os')}

## Baseline Performance
- Median latency: {_format_ms(baseline.get('latency_ms'))}
- CV: {baseline.get('cv', 0) * 100:.2f}%

## Best Candidate
- Config: `{json.dumps(best.get('config', {}))}`
- Median latency: {_format_ms(best.get('latency_ms'))}
- Speedup: **{best.get('speedup', 0):.2f}x**
- Score: {best.get('score', 0):.4f}

## Stability Stats
- CV: {best.get('cv', 0) * 100:.2f}%

## Virtual Mentor Diagnosis
- **Bottleneck suspected**: {bottleneck_diagnosis.get('diagnosis')}
- **Explanation**: {bottleneck_diagnosis.get('explanation')}

## Recommended Next Actions
{bottleneck_diagnosis.get('suggestions')}
- [ ] Apply local refinement around the best configuration.
- [ ] Store results as priors for future runs on {fingerprint.get('gpu_name')}.
{evaluation_summary}
{artifact_summary}
"""
    report_file = reports_dir / f"report_{project_name}_{run_id}.md"
    with open(report_file, "w") as f:
        f.write(report_content)
    return report_file


def write_json_summary(run_id: str, summary: dict[str, Any], reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_file = reports_dir / f"run_summary_{run_id}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    return summary_file
