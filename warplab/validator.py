import subprocess
import json
from pathlib import Path
from typing import Dict, Any

class ValidationResult:
    def __init__(self, success: bool, valid: bool, data: Dict[str, Any], raw_output: str):
        self.success = success
        self.valid = valid
        self.data = data
        self.raw_output = raw_output

def run_validator(bin_path: Path, run_cmd: str) -> ValidationResult:
    try:
        process = subprocess.run(
            run_cmd,
            shell=True,
            cwd=bin_path.parent.parent, # Assuming build/ is inside project root
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return ValidationResult(False, False, {}, process.stderr)
            
        # Parse last line as JSON
        lines = process.stdout.strip().splitlines()
        if not lines:
            return ValidationResult(True, False, {}, "No output")
            
        try:
            data = json.loads(lines[-1])
            return ValidationResult(True, data.get("valid", False), data, process.stdout)
        except json.JSONDecodeError:
            return ValidationResult(True, False, {}, f"Failed to parse JSON: {lines[-1]}")
            
    except Exception as e:
        return ValidationResult(False, False, {}, str(e))
