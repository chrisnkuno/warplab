from pathlib import Path

from .execution import CommandResult, render_command, run_command

def compile_kernel(
    project_root: Path,
    compile_cmd: str,
    output_bin: Path,
    flags: str = "",
    timeout_s: int | None = 300,
    extra_context: dict | None = None,
) -> CommandResult:
    output_bin.parent.mkdir(parents=True, exist_ok=True)

    context = {
        "artifact": str(output_bin),
        "build_dir": str(output_bin.parent),
        "flags": flags,
        "project_root": str(project_root),
    }
    if extra_context:
        context.update(extra_context)

    full_cmd = render_command(compile_cmd, **context)
    return run_command(full_cmd, cwd=project_root, timeout_s=timeout_s)
