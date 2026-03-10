from pathlib import Path
from typing import Any

import csv
import io

from .execution import render_command, run_command

class BottleneckInference:
    def __init__(self, metrics: dict[str, Any]):
        self.metrics = metrics
        
    def classify(self) -> str:
        # Rule-based classifier for v1
        # Metrics we look for:
        # dram__throughput.pct, sm__throughput.pct, l1tex__t_throughput.pct
        
        try:
            dram = float(self.metrics.get("dram__throughput.pct", 0))
            sm = float(self.metrics.get("sm__throughput.pct", 0))
            l1tex = float(self.metrics.get("l1tex__t_throughput.pct", 0))
            
            if dram > 70:
                return "Memory-bound (DRAM)"
            if l1tex > 70:
                return "Memory-bound (L1/TEX)"
            if sm > 70:
                return "Compute-bound (SM)"
            if sm < 30 and dram < 30:
                return "Latency-bound or Low-Occupancy"
                
            return "Balanced or Unknown"
        except (ValueError, TypeError):
            return "Inconclusive"

    def diagnose(self) -> dict[str, str]:
        bottleneck = self.classify()
        if bottleneck == "Memory-bound (DRAM)":
            return {
                "diagnosis": bottleneck,
                "explanation": "Your kernel spends over 70% of its time waiting for data from main memory. It's starved for data.",
                "suggestions": "1. Ensure memory accesses are coalesced. 2. Load frequently used data into Shared Memory (__shared__)."
            }
        elif bottleneck == "Memory-bound (L1/TEX)":
            return {
                "diagnosis": bottleneck,
                "explanation": "The kernel is hitting the L1 cache or Texture cache heavily.",
                "suggestions": "1. Consider changing access patterns to be more cache-friendly. 2. If using read-only data, ensure it's loaded efficiently."
            }
        elif bottleneck == "Compute-bound (SM)":
            return {
                "diagnosis": bottleneck,
                "explanation": "Your GPU's compute units (Streaming Multiprocessors) are saturated. The kernel is doing a lot of math.",
                "suggestions": "1. Profile instruction mix (e.g., FMA operations). 2. Minimize divergent branches. 3. Consider loop unrolling."
            }
        elif bottleneck == "Latency-bound or Low-Occupancy":
            return {
                "diagnosis": bottleneck,
                "explanation": "Neither memory nor compute is saturated. The GPU might not have enough work per block, or is waiting on long-latency instructions.",
                "suggestions": "1. Increase block size or grid size to improve occupancy. 2. Check for register pressure limiting active warps."
            }
        else:
            return {
                "diagnosis": bottleneck,
                "explanation": "The profiler metrics do not strongly suggest a single primary bottleneck.",
                "suggestions": "Check nsys/ncu directly for more detailed timeline or metric analysis."
            }

def run_profiler(
    bin_path: Path,
    run_cmd: str,
    kernel_name: str = "",
    cwd: Path | None = None,
    timeout_s: int | None = 300,
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {"artifact": str(bin_path)}
    if extra_context:
        context.update(extra_context)

    rendered_run_cmd = render_command(run_cmd, **context)
    ncu_cmd = (
        "ncu --csv --metrics "
        "bus__throughput.pct,sm__throughput.pct,l1tex__t_throughput.pct,"
        "lts__t_throughput.pct,dram__throughput.pct "
        f"{rendered_run_cmd}"
    )
    execution = run_command(ncu_cmd, cwd=cwd or bin_path.parent, timeout_s=timeout_s)
    if not execution.success:
        return {"error": execution.stderr, "command": execution.command}

    reader = csv.DictReader(io.StringIO(execution.stdout))
    metrics: dict[str, Any] = {}
    for row in reader:
        metric_name = row.get("Metric Name") or row.get("Metric Name Base")
        if not metric_name:
            continue

        row_kernel_name = row.get("Kernel Name") or row.get("Kernel Name Base") or ""
        if kernel_name and row_kernel_name and kernel_name not in row_kernel_name:
            continue

        metric_value = row.get("Metric Value")
        if metric_value is not None:
            metrics[metric_name] = metric_value

    if not metrics:
        return {
            "error": "No profiler metrics parsed from Nsight Compute output",
            "command": execution.command,
            "stdout": execution.stdout,
        }

    return metrics
