import subprocess
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

class BenchmarkResult:
    def __init__(self, median_ms: float, mean_ms: float, std_ms: float, cv: float, raw_data: List[float]):
        self.median_ms = median_ms
        self.mean_ms = mean_ms
        self.std_ms = std_ms
        self.cv = cv
        self.raw_data = raw_data

def run_benchmark(
    bin_path: Path,
    run_cmd: str,
    warmup_runs: int = 5,
    timed_runs: int = 20
) -> BenchmarkResult:
    latencies = []
    
    # We assume the benchmark binary prints JSON lines with "latency_ms"
    # and we run it once, it handles the loop, or we run it in a loop.
    # Instruction says: benchmark binary should print machine-readable JSON lines.
    # Protocol: 3-10 warmups, 10-30 timed runs.
    
    # Let's assume the benchmark binary takes --repeats and we parse all lines.
    try:
        process = subprocess.run(
            run_cmd,
            shell=True,
            cwd=bin_path.parent.parent,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            raise RuntimeError(f"Benchmark failed: {process.stderr}")
            
        for line in process.stdout.strip().splitlines():
            try:
                data = json.loads(line)
                if "latency_ms" in data:
                    latencies.append(data["latency_ms"])
            except json.JSONDecodeError:
                continue
        
        if not latencies:
            raise RuntimeError("No latencies collected from benchmark")
            
        # Stats
        median = float(np.median(latencies))
        mean = float(np.mean(latencies))
        std = float(np.std(latencies))
        cv = std / mean if mean != 0 else 0
        
        return BenchmarkResult(median, mean, std, cv, latencies)
        
    except Exception as e:
        raise RuntimeError(f"Error running benchmark: {str(e)}")
