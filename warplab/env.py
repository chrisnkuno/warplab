import subprocess
import platform
import socket
import os
import sys
from datetime import datetime
from typing import Dict, Any

def get_env_fingerprint() -> Dict[str, Any]:
    fingerprint = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_release": platform.release(),
        "python_version": platform.python_version(),
    }
    
    # Environment detection
    if 'google.colab' in sys.modules:
        fingerprint["environment"] = "Google Colab"
    elif os.path.exists('/kaggle/working'):
        fingerprint["environment"] = "Kaggle"
    else:
        fingerprint["environment"] = "Local/Other"
    
    # GPU info via nvidia-smi if available
    try:
        gpu_info = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,compute_cap,driver_version", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        ).strip().split(", ")
        fingerprint["gpu_name"] = gpu_info[0]
        fingerprint["compute_capability"] = gpu_info[1]
        fingerprint["driver_version"] = gpu_info[2]
    except (subprocess.CalledProcessError, FileNotFoundError):
        fingerprint["gpu_name"] = "Unknown"
        fingerprint["compute_capability"] = "Unknown"
        fingerprint["driver_version"] = "Unknown"

    # CUDA toolkit version
    try:
        cuda_version = subprocess.check_output(
            ["nvcc", "--version"], encoding="utf-8"
        )
        for line in cuda_version.splitlines():
            if "release" in line:
                fingerprint["cuda_version"] = line.split("release")[-1].strip().split(",")[0]
                break
    except (subprocess.CalledProcessError, FileNotFoundError):
        fingerprint["cuda_version"] = "Unknown"

    try:
        fingerprint["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
        fingerprint["git_dirty"] = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                encoding="utf-8",
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        fingerprint["git_commit"] = "Unknown"
        fingerprint["git_dirty"] = False

    return fingerprint
