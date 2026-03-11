from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark
from .compiler import compile_kernel
from .config import load_project_config
from .env import get_env_fingerprint
from .memory import Memory
from .models import CandidateConfig
from .profiler import BottleneckInference, run_profiler
from .report import generate_markdown_report, write_json_summary
from .scoring import score_candidate
from .search import (
    generate_local_refinements,
    generate_prior_guided_candidates,
    generate_profile_guided_candidates,
    generate_random_candidates,
    set_search_seed,
)
from .utils import generate_id, get_kernel_signature
from .validator import run_validator


def _candidate_dirs(run_root: Path, candidate_id: str) -> tuple[Path, Path]:
    candidate_root = run_root / "candidates" / candidate_id
    return candidate_root / "bench", candidate_root / "validate"


def _profile_artifact_path(run_root: Path, label: str) -> Path:
    return run_root / "profiles" / f"{label}.json"


def _write_json_file(path: Path, payload: dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def run_project(
    project_path: Path,
    root_dir: Path,
    candidate_count: int | None = None,
    profile_baseline: bool = True,
) -> dict[str, Any]:
    project_path = project_path.resolve()
    root_dir = root_dir.resolve()
    config = load_project_config(project_path)

    runs_dir = root_dir / "runs"
    reports_dir = root_dir / "reports"
    db_path = root_dir / "db" / "warplab.sqlite"
    runs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    fingerprint = get_env_fingerprint()
    memory = Memory(db_path)
    run_id = generate_id()
    run_root = runs_dir / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    memory.insert_run(run_id, config.name, fingerprint, config.objective)
    search_seed = config.budget.get("seed")
    set_search_seed(search_seed)

    baseline_bench = run_root / "baseline" / "bench"
    baseline_validate = run_root / "baseline" / "validate"

    compile_context = dict(config.input)
    validation_context = {**config.input, **config.validation}
    benchmark_context = dict(config.input)

    try:
        baseline_bench_compile = compile_kernel(
            project_path,
            config.build["compile_kernel"],
            baseline_bench,
            extra_context=compile_context,
        )
        baseline_validate_compile = compile_kernel(
            project_path,
            config.build["compile_validate"],
            baseline_validate,
            extra_context=compile_context,
        )
        if not baseline_bench_compile.success or not baseline_validate_compile.success:
            raise RuntimeError(
                "Baseline compilation failed:\n"
                f"bench stderr:\n{baseline_bench_compile.stderr}\n"
                f"validate stderr:\n{baseline_validate_compile.stderr}"
            )

        baseline_validation = run_validator(
            baseline_validate,
            config.run["validate"],
            cwd=project_path,
            extra_context=validation_context,
        )
        if not baseline_validation.valid:
            raise RuntimeError(f"Baseline validation failed: {baseline_validation.raw_output}")

        baseline_benchmark = run_benchmark(
            baseline_bench,
            config.run["benchmark"],
            warmup_runs=config.budget["warmup_runs"],
            timed_runs=config.budget["timed_runs"],
            cwd=project_path,
            extra_context=benchmark_context,
        )
        baseline_latency = baseline_benchmark.median_ms

        baseline_profile: dict[str, Any] = {}
        baseline_profile_path = None
        baseline_diagnosis = {
            "diagnosis": "Not profiled",
            "explanation": "Profiling was disabled for this run.",
            "suggestions": "Enable profiling to get bottleneck-aware guidance.",
        }
        if profile_baseline:
            baseline_profile = run_profiler(
                baseline_bench,
                config.run["benchmark"],
                cwd=project_path,
                extra_context={**benchmark_context, "warmups": 1, "repeats": 1},
            )
            if "error" not in baseline_profile:
                baseline_diagnosis = BottleneckInference(baseline_profile).diagnose()
                baseline_profile_path = _profile_artifact_path(run_root, "baseline")
                _write_json_file(baseline_profile_path, baseline_profile)

        kernel_signature = get_kernel_signature(
            config.name,
            project_path / "kernel.cu",
            str(config.input["size"]),
        )
        priors = memory.get_priors(kernel_signature, fingerprint["gpu_name"])

        max_candidates = candidate_count or min(config.budget["max_experiments"], 30)
        refinement_budget = min(config.budget.get("refinement_budget", max(1, max_candidates // 4)), max_candidates)
        initial_budget = max(1, max_candidates - refinement_budget)
        if priors:
            candidates = generate_prior_guided_candidates(config, priors, initial_budget)
        elif baseline_profile and "error" not in baseline_profile:
            candidates = generate_profile_guided_candidates(config, baseline_profile, initial_budget)
        else:
            candidates = generate_random_candidates(config, initial_budget)

        results = []
        best_score = float("-inf")
        no_improvement_count = 0
        patience = config.budget.get("patience")
        early_stop_reason = None

        def evaluate_candidate(candidate: Any, index: int) -> dict[str, Any]:
            candidate_id = f"{run_id}_{index}"
            candidate_bench, candidate_validate = _candidate_dirs(run_root, candidate_id)
            flags = candidate.to_compile_flags()

            bench_compile = compile_kernel(
                project_path,
                config.build["compile_kernel"],
                candidate_bench,
                flags=flags,
                extra_context=compile_context,
            )
            validate_compile = compile_kernel(
                project_path,
                config.build["compile_validate"],
                candidate_validate,
                flags=flags,
                extra_context=compile_context,
            )

            metrics: dict[str, Any] = {
                "compile_success": bench_compile.success and validate_compile.success,
                "validate_success": False,
                "benchmark_success": False,
                "stage_details": {
                    "compile_bench": {
                        "command": bench_compile.command,
                        "duration_s": bench_compile.duration_s,
                        "success": bench_compile.success,
                    },
                    "compile_validate": {
                        "command": validate_compile.command,
                        "duration_s": validate_compile.duration_s,
                        "success": validate_compile.success,
                    },
                },
            }

            if metrics["compile_success"]:
                validation = run_validator(
                    candidate_validate,
                    config.run["validate"],
                    cwd=project_path,
                    extra_context=validation_context,
                )
                metrics["validate_success"] = validation.valid
                metrics["stage_details"]["validate"] = {
                    "command": validation.execution.command,
                    "duration_s": validation.execution.duration_s,
                    "success": validation.success,
                }
                if not validation.valid:
                    metrics["error"] = validation.raw_output

                if validation.valid:
                    try:
                        benchmark = run_benchmark(
                            candidate_bench,
                            config.run["benchmark"],
                            warmup_runs=config.budget["warmup_runs"],
                            timed_runs=config.budget["timed_runs"],
                            cwd=project_path,
                            extra_context=benchmark_context,
                        )
                        metrics["benchmark_success"] = True
                        metrics["latency_ms"] = benchmark.median_ms
                        metrics["std_ms"] = benchmark.std_ms
                        metrics["cv"] = benchmark.cv
                        metrics["speedup"] = baseline_latency / benchmark.median_ms
                        metrics["score"] = score_candidate(metrics["speedup"], benchmark.cv, True, True)
                        metrics["stage_details"]["benchmark"] = {
                            "command": benchmark.execution.command,
                            "duration_s": benchmark.execution.duration_s,
                            "success": True,
                        }
                    except Exception as exc:
                        metrics["error"] = str(exc)
            else:
                metrics["error"] = "\n".join(
                    part for part in [bench_compile.stderr, validate_compile.stderr] if part
                )

            memory.insert_candidate(candidate_id, run_id, candidate.model_dump_json(), metrics)
            memory.insert_artifact(candidate_id, "bench_binary", str(candidate_bench))
            memory.insert_artifact(candidate_id, "validate_binary", str(candidate_validate))

            return {
                **metrics,
                "id": candidate_id,
                "config": candidate.model_dump(),
                "flags": flags,
            }

        for index, candidate in enumerate(candidates):
            result = evaluate_candidate(candidate, index)
            results.append(result)
            if result.get("benchmark_success") and result.get("score", float("-inf")) > best_score:
                best_score = result["score"]
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            if patience and no_improvement_count >= patience:
                early_stop_reason = f"No improvement for {patience} consecutive candidates."
                break

        if len(results) < max_candidates:
            top_results = [
                CandidateConfig(params=result["config"]["params"])
                for result in sorted(
                    [result for result in results if result.get("benchmark_success")],
                    key=lambda item: item.get("score", float("-inf")),
                    reverse=True,
                )[: config.budget.get("refinement_top_k", 3)]
            ]
            remaining = max_candidates - len(results)
            refinements = generate_local_refinements(top_results, config, min(remaining, refinement_budget))
            start_index = len(results)
            for offset, refinement in enumerate(refinements):
                result = evaluate_candidate(refinement, start_index + offset)
                results.append(result)
                if result.get("benchmark_success") and result.get("score", float("-inf")) > best_score:
                    best_score = result["score"]
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                if patience and no_improvement_count >= patience:
                    early_stop_reason = f"No improvement for {patience} consecutive candidates."
                    break

        successful_results = [result for result in results if result.get("benchmark_success")]
        successful_results.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
        best_candidate = successful_results[0] if successful_results else None

        best_profile = {}
        best_profile_path = None
        if best_candidate:
            memory.update_priors(
                kernel_signature,
                fingerprint["gpu_name"],
                json.dumps(best_candidate["config"]),
                best_candidate["score"],
            )
            if profile_baseline:
                best_candidate_bench = run_root / "candidates" / best_candidate["id"] / "bench"
                best_profile = run_profiler(
                    best_candidate_bench,
                    config.run["benchmark"],
                    cwd=project_path,
                    extra_context={**benchmark_context, "warmups": 1, "repeats": 1},
                )
                if "error" not in best_profile:
                    best_profile_path = _profile_artifact_path(run_root, best_candidate["id"])
                    _write_json_file(best_profile_path, best_profile)
                    memory.insert_profile(
                        best_candidate["id"],
                        json.dumps(best_profile),
                        BottleneckInference(best_profile).classify(),
                    )

        summary_payload = {
            "run_id": run_id,
            "project_name": config.name,
            "fingerprint": fingerprint,
            "baseline": {
                "latency_ms": baseline_latency,
                "cv": baseline_benchmark.cv,
                "compile_bench_command": baseline_bench_compile.command,
                "compile_validate_command": baseline_validate_compile.command,
                "validate_command": baseline_validation.execution.command,
                "benchmark_command": baseline_benchmark.execution.command,
                "baseline_profile_path": str(baseline_profile_path) if baseline_profile_path else None,
            },
            "best_candidate": best_candidate,
            "best_profile_path": str(best_profile_path) if best_profile_path else None,
            "baseline_diagnosis": baseline_diagnosis,
            "results": results,
            "run_root": str(run_root),
            "search_seed": search_seed,
            "early_stop_reason": early_stop_reason,
        }
        run_summary_path = write_json_summary(run_id, summary_payload, reports_dir)
        report_path = None
        if best_candidate:
            baseline_metrics = {"latency_ms": baseline_latency, "cv": baseline_benchmark.cv}
            report_path = generate_markdown_report(
                run_id,
                config.name,
                fingerprint,
                baseline_metrics,
                best_candidate,
                baseline_diagnosis,
                reports_dir,
                run_summary_path=run_summary_path,
                run_root=run_root,
                evaluated_count=len(results),
                successful_count=len(successful_results),
                seed=search_seed,
                early_stop_reason=early_stop_reason,
                best_profile_path=best_profile_path,
            )
            memory.insert_artifact(best_candidate["id"], "report", str(report_path))
            memory.insert_artifact(best_candidate["id"], "run_summary", str(run_summary_path))

        memory.finalize_run(run_id, "completed")
        return {
            "run_id": run_id,
            "project_name": config.name,
            "baseline_latency_ms": baseline_latency,
            "best_candidate": best_candidate,
            "report_path": str(report_path) if report_path else None,
            "run_summary_path": str(run_summary_path),
            "results": results,
            "baseline_profile": baseline_profile,
            "baseline_diagnosis": baseline_diagnosis,
            "best_profile": best_profile,
            "early_stop_reason": early_stop_reason,
        }
    except Exception:
        memory.finalize_run(run_id, "failed")
        raise
