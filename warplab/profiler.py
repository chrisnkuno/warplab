import subprocess
import csv
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

class BottleneckInference:
    def __init__(self, metrics: Dict[str, Any]):
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

    def diagnose(self) -> Dict[str, str]:
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

def run_profiler(bin_path: Path, run_cmd: str, kernel_name: str = "") -> Dict[str, Any]:
    ncu_cmd = f"ncu --csv --metrics bus__throughput.pct,sm__throughput.pct,l1tex__t_throughput.pct,lts__t_throughput.pct,dram__throughput.pct {run_cmd}"
    
    try:
        process = subprocess.run(
            ncu_cmd,
            shell=True,
            cwd=bin_path.parent.parent,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {"error": process.stderr}
            
        metrics = {}
        # Parse NCU CSV
        lines = process.stdout.strip().splitlines()
        found_header = False
        header = []
        for line in lines:
            if "Metric Name" in line and "Metric Value" in line:
                found_header = True
                continue
            if found_header:
                parts = line.split(",")
                if len(parts) >= 2:
                    # Very simple parsing, NCU CSV can be complex
                    # Values are often quoted: "sm__throughput.pct","%","75.2"
                    # We just need the name and value
                    name = parts[0].strip('"')
                    val = parts[-1].strip('"')
                    metrics[name] = val
                    
        return metrics
    except Exception as e:
        return {"error": str(e)}
