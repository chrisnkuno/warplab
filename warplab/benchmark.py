import json
from pathlib import Path
from typing import Any

import numpy as np

from .execution import CommandResult, render_command, run_command

class BenchmarkResult:
    def __init__(
        self,
        median_ms: float,
        mean_ms: float,
        std_ms: float,
        cv: float,
        raw_data: list[float],
        execution: CommandResult,
    ):
        self.median_ms = median_ms
        self.mean_ms = mean_ms
        self.std_ms = std_ms
        self.cv = cv
        self.raw_data = raw_data
        self.execution = execution

def run_benchmark(
    bin_path: Path,
    run_cmd: str,
    warmup_runs: int = 5,
    timed_runs: int = 20,
    cwd: Path | None = None,
    timeout_s: int | None = 300,
    extra_context: dict[str, Any] | None = None,
) -> BenchmarkResult:
    latencies = []

    context = {
        "artifact": str(bin_path),
        "warmups": warmup_runs,
        "repeats": timed_runs,
    }
    if extra_context:
        context.update(extra_context)

    command = render_command(run_cmd, **context)
    execution = run_command(command, cwd=cwd or bin_path.parent, timeout_s=timeout_s)
    if not execution.success:
        raise RuntimeError(f"Benchmark failed: {execution.stderr}")

    for line in execution.stdout.strip().splitlines():
        try:
            data = json.loads(line)
            if "latency_ms" in data:
                latencies.append(float(data["latency_ms"]))
        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    if len(latencies) < timed_runs:
        raise RuntimeError(
            f"Expected at least {timed_runs} timed latencies, received {len(latencies)}"
        )

    median = float(np.median(latencies))
    mean = float(np.mean(latencies))
    std = float(np.std(latencies))
    cv = std / mean if mean != 0 else 0.0

    return BenchmarkResult(median, mean, std, cv, latencies, execution)
