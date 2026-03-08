import json
import os
from pathlib import Path
from typing import List, Dict, Any

def generate_markdown_report(
    run_id: str, 
    project_name: str, 
    fingerprint: Dict[str, Any],
    baseline: Dict[str, Any], 
    best: Dict[str, Any], 
    bottleneck_diagnosis: Dict[str, str],
    reports_dir: Path
):
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
- Median latency: {baseline.get('latency_ms', 'N/A'):.4f} ms
- CV: {baseline.get('cv', 0) * 100:.2f}%

## Best Candidate
- Config: `{json.dumps(best.get('config', {}))}`
- Median latency: {best.get('latency_ms', 'N/A'):.4f} ms
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
"""
    report_file = reports_dir / f"report_{project_name}_{run_id}.md"
    with open(report_file, "w") as f:
        f.write(report_content)
    return report_file
