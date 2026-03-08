from pathlib import Path
from .env import get_env_fingerprint
import uuid

def generate_id() -> str:
    return str(uuid.uuid4())[:8]

def get_kernel_signature(project_name: str, kernel_path: Path, size_bucket: str) -> str:
    # Stable signature for priors
    # For v1: project:size
    return f"{project_name}:{size_bucket}"
