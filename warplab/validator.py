import json
from pathlib import Path
from typing import Any

from .execution import CommandResult, render_command, run_command

class ValidationResult:
    def __init__(
        self,
        success: bool,
        valid: bool,
        data: dict[str, Any],
        raw_output: str,
        execution: CommandResult,
    ):
        self.success = success
        self.valid = valid
        self.data = data
        self.raw_output = raw_output
        self.execution = execution

def run_validator(
    bin_path: Path,
    run_cmd: str,
    cwd: Path | None = None,
    timeout_s: int | None = 120,
    extra_context: dict[str, Any] | None = None,
) -> ValidationResult:
    context = {"artifact": str(bin_path)}
    if extra_context:
        context.update(extra_context)

    command = render_command(run_cmd, **context)
    execution = run_command(command, cwd=cwd or bin_path.parent, timeout_s=timeout_s)
    if not execution.success:
        return ValidationResult(False, False, {}, execution.stderr, execution)

    lines = execution.stdout.strip().splitlines()
    if not lines:
        return ValidationResult(True, False, {}, "No output", execution)

    try:
        data = json.loads(lines[-1])
        return ValidationResult(True, bool(data.get("valid", False)), data, execution.stdout, execution)
    except json.JSONDecodeError:
        return ValidationResult(True, False, {}, f"Failed to parse JSON: {lines[-1]}", execution)
