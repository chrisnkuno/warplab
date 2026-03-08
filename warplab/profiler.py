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
