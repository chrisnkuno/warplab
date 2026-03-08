import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Tuple

class CompilationResult:
    def __init__(self, success: bool, stdout: str, stderr: str, command: str):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

def compile_kernel(
    project_root: Path,
    compile_cmd: str,
    output_bin: Path,
    flags: str = ""
) -> CompilationResult:
    # Ensure build directory exists
    output_bin.parent.mkdir(parents=True, exist_ok=True)
    
    # Replace flags in the command if it's templated or just append them
    # For v1, we expect the user to provide a command that we can append flags to
    # or we just run the command with flags as environment variables or extra args.
    # The instruction says: nvcc -O3 -DBLOCK_SIZE=256 ...
    
    full_cmd = f"{compile_cmd} {flags}"
    
    try:
        process = subprocess.run(
            full_cmd,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True
        )
        return CompilationResult(
            success=(process.returncode == 0),
            stdout=process.stdout,
            stderr=process.stderr,
            command=full_cmd
        )
    except Exception as e:
        return CompilationResult(
            success=False,
            stdout="",
            stderr=str(e),
            command=full_cmd
        )
