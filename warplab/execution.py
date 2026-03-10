from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    success: bool
    command: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False


def render_command(template: str, **context: Any) -> str:
    try:
        return template.format(**context).strip()
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(f"Missing command template variable: {missing}") from exc


def run_command(command: str, cwd: Path, timeout_s: int | None = None) -> CommandResult:
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration_s = time.perf_counter() - started
        return CommandResult(
            success=(process.returncode == 0),
            command=command,
            cwd=str(cwd),
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            duration_s=duration_s,
        )
    except subprocess.TimeoutExpired as exc:
        duration_s = time.perf_counter() - started
        return CommandResult(
            success=False,
            command=command,
            cwd=str(cwd),
            returncode=-1,
            stdout=exc.stdout or "",
            stderr=exc.stderr or f"Command timed out after {timeout_s}s",
            duration_s=duration_s,
            timed_out=True,
        )
    except Exception as exc:
        duration_s = time.perf_counter() - started
        return CommandResult(
            success=False,
            command=command,
            cwd=str(cwd),
            returncode=-1,
            stdout="",
            stderr=str(exc),
            duration_s=duration_s,
        )
