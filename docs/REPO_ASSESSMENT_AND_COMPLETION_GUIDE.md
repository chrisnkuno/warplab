# WarpLab Repository Assessment and Completion Guide

## Executive Summary

WarpLab is currently a promising prototype, not a complete system.

The repo already has the right high-level building blocks:

- project config loading
- candidate parameter modeling
- compilation, validation, benchmarking, and profiling wrappers
- simple search strategies
- SQLite-backed memory for priors
- a notebook that tries to orchestrate an optimization run

The main issue is that these pieces do not yet compose into a reliable end-to-end workflow. The notebook and sample CUDA project expose several critical path failures that prevent the "optimize a kernel variant, validate it, benchmark it, store the result, and report it" loop from working correctly.

If the goal is "a serious notebook-first CUDA autotuning tool," the next phase should focus less on adding new ideas and more on making the existing pipeline correct, isolated, reproducible, and testable.

## Current Maturity

Current maturity: early prototype / proof of concept.

What feels solid enough to keep:

- The repo has a coherent product direction.
- The module boundaries are sensible for a v1 package.
- The SQLite memory layer is a reasonable starting point.
- The notebook-first workflow is aligned with research usage.
- The sample `project.yaml` format is simple enough to iterate on.

What makes it incomplete:

- No reliable orchestration layer outside the notebook.
- The candidate compile/validate/benchmark flow is broken.
- The sample project is not currently trustworthy as a reference workload.
- Several features described in the README are only partially implemented.
- There are no automated tests, no CI, and no release readiness checks.

## Critical Findings

These are the highest-priority issues to fix before expanding scope.

### 1. Candidate binaries are not actually isolated per run

Relevant files:

- `warplab/compiler.py`
- `warplab/benchmark.py`
- `warplab/validator.py`
- `projects/saxpy/project.yaml`
- `notebooks/warplab_v1.ipynb`

Problem:

- `compile_kernel()` accepts `output_bin` but never uses it.
- The compile command in `projects/saxpy/project.yaml` hardcodes `build/bench` and `build/validate`.
- The notebook creates candidate paths in `runs/`, but the compiler still writes to `project/build/...`.
- `run_benchmark()` and `run_validator()` derive their working directory from `bin_path.parent.parent`, which is correct for the baseline path inside `projects/saxpy/build`, but wrong for candidate paths inside `runs/`.

Impact:

- candidates are not compiled into their own artifact locations
- parallel evaluation can clobber shared binaries
- candidate validation and benchmarking can execute from the wrong directory
- end-to-end search results are unreliable

### 2. Candidate validation is not validating candidate builds

Relevant files:

- `notebooks/warplab_v1.ipynb`
- `projects/saxpy/project.yaml`
- `warplab/compiler.py`

Problem:

- The notebook compiles only the benchmark binary for each candidate.
- Validation is then run with `config.run["validate"]`, which points to `./build/validate`.
- The candidate-specific validation binary is never compiled or invoked.

Impact:

- the correctness gate does not actually validate the candidate being scored
- invalid configurations can be scored as valid
- the main product claim, "correctness-gated optimization," is not currently true

### 3. The sample validator does not compile as written

Relevant file:

- `projects/saxpy/validate.cu`

Problem:

- `cudaMemcpy(h_y.data(), d_y.data(), ...)` uses `.data()` on a raw device pointer.

Impact:

- the reference project appears broken
- the first real user path is blocked

### 4. Search constraints use `eval()` and fail open

Relevant file:

- `warplab/search.py`

Problem:

- constraints are executed with `eval()`
- if evaluation throws, the code silently continues and treats the candidate as valid

Impact:

- unsafe config evaluation surface
- malformed constraints can quietly disable validation of the search space

### 5. Benchmarking and profiling wrappers do not enforce a rigorous protocol

Relevant files:

- `warplab/benchmark.py`
- `warplab/profiler.py`
- `projects/saxpy/bench.cu`

Problem:

- `warmup_runs` and `timed_runs` are accepted but ignored in Python
- the benchmark protocol is delegated entirely to the binary contract
- benchmark inputs are not initialized in `bench.cu`
- profiler CSV parsing is very fragile
- profiler kernel filtering is not implemented even though a `kernel_name` parameter exists

Impact:

- measurement quality is not controlled centrally
- results are difficult to trust or compare across runs

### 6. Persistence exists, but lifecycle management is incomplete

Relevant file:

- `warplab/memory.py`

Problem:

- runs are inserted with status `running` and never finalized
- schema fields such as `git_commit`, `profiles`, and `artifacts` are defined but not used by the workflow
- there are no indexes, migrations, or query helpers for run inspection

Impact:

- history is incomplete
- reproducibility is weaker than the product description suggests

### 7. The README overstates what the repo currently delivers

Relevant file:

- `README.md`

Problem:

- the README describes a reproducible, profiler-informed optimization system
- the current implementation is closer to a partial notebook prototype

Impact:

- expectation mismatch for contributors and users
- first-run confusion

## What To Improve

### Improve correctness first

The first milestone should be "one sample project runs correctly from baseline through best-candidate report." Until that exists, new features will compound on unstable foundations.

Improve:

- artifact path handling
- command templating
- compile/validate/benchmark parity
- candidate isolation under parallel execution
- benchmark protocol consistency
- explicit failure handling and diagnostics

### Improve architecture

The notebook should become a thin client over a real orchestration layer.

Improve:

- move the optimization loop out of the notebook into a package-level runner
- define typed execution results for compile, validate, benchmark, and profile stages
- separate project specification from execution state
- stop relying on implicit working-directory behavior

### Improve trustworthiness

WarpLab will only be useful if users can trust the output.

Improve:

- run provenance
- environment capture
- deterministic candidate IDs
- explicit artifact storage
- reproducible benchmark inputs
- command logging
- error classification

### Improve developer experience

At the moment, a new contributor has to infer too much.

Improve:

- dependency setup
- local development workflow
- test strategy
- coding standards
- project spec documentation
- sample project authoring guide

## What To Add

### Add a real runner

Add a package API and CLI around the optimization loop.

Suggested entry points:

- `warplab.runner.run_project(...)`
- `python -m warplab run projects/saxpy`

This runner should:

- load the project config
- fingerprint the environment
- build the baseline
- validate the baseline
- benchmark the baseline
- profile the baseline
- generate candidate configs
- compile and validate each candidate in isolated directories
- benchmark valid candidates
- update memory
- write a report

### Add typed project and command models

The current `ProjectConfig` model is too loose for long-term stability.

Add:

- dedicated models for build commands, run commands, input schema, budget, validation tolerances, and objective
- explicit placeholders for output paths and runtime parameters
- validation of required fields
- a version field in `project.yaml`

### Add command templating that understands outputs

Right now commands are raw strings. That is too fragile.

Add a templating system where commands can refer to:

- `{project_root}`
- `{build_dir}`
- `{artifact}`
- `{size}`
- `{repeats}`
- `{flags}`

This should remove all implicit path coupling.

### Add a trustworthy sample suite

Right now only `projects/saxpy` is tracked, and it is not fully healthy.

Add:

- a fixed SAXPY sample that actually compiles and runs
- at least one reduction sample
- at least one stencil sample
- a "minimal project template" contributors can copy

### Add testing

You need both non-GPU and GPU-aware testing layers.

Add:

- pure-Python tests for config parsing, search, scoring, report generation, and DB behavior
- command construction tests
- notebook smoke test coverage if you keep the notebook as a first-class entry point
- optional GPU integration tests gated by environment

### Add CI and quality gates

Add:

- formatting
- linting
- type checking
- unit tests
- docs checks

### Add observability

Add:

- structured logging
- per-candidate logs
- captured stdout/stderr artifacts
- timing breakdowns by stage
- a summary table of failures by reason

## Recommended Order Of Work

### Phase 1: Make the prototype honest

Goal:

- one working sample project
- one reliable end-to-end run
- one accurate report

Tasks:

- fix `projects/saxpy/validate.cu`
- stop hardcoding build outputs in `project.yaml`
- make `compile_kernel()` actually honor `output_bin`
- make validation and benchmarking execute against the candidate artifact that was just built
- remove any dependence on inferred `cwd` from artifact shape
- make candidate evaluation sequential until artifact isolation is proven correct
- update README language so it matches the real state

Exit criteria:

- baseline compile/validate/benchmark/profile all succeed
- at least one candidate is compiled, validated, benchmarked, and stored correctly
- the report reflects the real best candidate

### Phase 2: Build a real core runner

Goal:

- notebook becomes a frontend, not the system

Tasks:

- implement a runner module
- move orchestration logic out of the notebook
- expose a CLI command
- define typed result objects for each pipeline stage
- centralize error handling

Exit criteria:

- the same run can be launched from Python or CLI
- notebook cells call runner functions instead of owning business logic

### Phase 3: Make results trustworthy

Goal:

- reproducible and debuggable experiments

Tasks:

- capture git commit and dirty state
- store profiler output and command logs as artifacts
- add run finalization states
- add per-run and per-candidate directories
- define benchmark protocol centrally
- add support for timeouts and retries

Exit criteria:

- every run has enough provenance to debug or reproduce it later

### Phase 4: Expand search quality

Goal:

- smarter optimization, still with controlled behavior

Tasks:

- replace `eval()`-based constraint evaluation
- add deduplication of candidates
- add local refinement around top performers
- add seeded randomness
- add search strategy selection
- add budget-aware stopping rules

Exit criteria:

- search behavior is deterministic when seeded
- invalid search-space constraints fail fast

### Phase 5: Productize the repo

Goal:

- contributor-ready open-source project

Tasks:

- add tests and CI
- add examples and docs
- add contribution guide
- add issue templates and roadmap
- split optional notebook dependencies from core runtime dependencies

Exit criteria:

- a new contributor can install, run, test, and extend WarpLab without guessing

## Detailed Completion Checklist

Use this as the main "make it complete" checklist.

### A. Core Execution Pipeline

- Define a canonical artifact directory layout.
- Ensure baseline and candidate builds use the same command abstraction.
- Make compile commands output to an explicit requested path.
- Make validate commands consume an explicit requested binary path.
- Make benchmark commands consume an explicit requested binary path.
- Make profiler commands consume an explicit requested binary path.
- Remove path assumptions based on `bin_path.parent.parent`.
- Add timeouts to compile, validate, benchmark, and profile subprocesses.
- Capture subprocess return code, stdout, stderr, duration, and command for every stage.
- Add a failure enum or status model for compile, validate, benchmark, and profile outcomes.

### B. Project Specification

- Version `project.yaml`.
- Define a schema for build and run commands.
- Document the command placeholders.
- Validate search-space types.
- Validate that all constrained parameter names exist.
- Validate that all runtime placeholders in commands are satisfiable.
- Validate objective names and direction values.
- Add a schema upgrade path if the project format changes later.

### C. CUDA Sample Projects

- Fix SAXPY validation compile issues.
- Initialize benchmark inputs intentionally.
- Add error checking around CUDA API calls.
- Add kernel launch error checks.
- Ensure sample projects prove that tunable parameters actually matter.
- Either implement `use_shared` or remove it from the SAXPY search space.
- Add reduction and stencil examples only after the template contract is stable.

### D. Search

- Replace `eval()` with a safe expression evaluator or a structured constraint DSL.
- Deduplicate generated candidates.
- Enforce valid priors against the current search space.
- Add configurable seeds for reproducibility.
- Add perturbation-based local search around strong candidates.
- Add stopping logic for no-improvement windows.
- Add strategy metadata to stored runs.

### E. Benchmarking and Profiling

- Centralize warmup and timed-run semantics.
- Decide whether the Python layer or the benchmark binary owns repetition.
- Normalize benchmark output format and document it.
- Store raw latency distributions.
- Support outlier policy explicitly.
- Parse Nsight Compute output robustly.
- Support kernel filtering when multiple kernels are present.
- Record profiler command version and metric set used.

### F. Memory / Database

- Add run finalization methods.
- Store baseline metrics explicitly.
- Store profiler results through the `profiles` table.
- Store generated reports and raw logs through the `artifacts` table.
- Add indexes for common run and prior lookups.
- Capture git commit and dirty state.
- Add migration support before the schema evolves further.
- Add read APIs for run history and leaderboard-style views.

### G. Interfaces

- Keep the notebook as a guided UX layer.
- Add a CLI for repeatable runs.
- Add a Python API for integration into other workflows.
- Define a stable report format.
- Add a machine-readable run summary, for example JSON alongside Markdown.

### H. Packaging and Repository Hygiene

- Add optional dependency groups such as `dev`, `notebook`, and maybe `gpu`.
- Add a lockfile strategy or documented environment strategy.
- Add formatting and lint config.
- Add type-checker config.
- Clean up confusing empty directories under `warplab/` if they are not intentional.
- Add a `tests/` tree.
- Add a `docs/` index once documentation grows.

### I. Documentation

- Rewrite README to reflect current scope accurately.
- Add installation prerequisites for CUDA, `nvcc`, `ncu`, drivers, and Python.
- Add a quickstart for running the SAXPY sample.
- Add a project authoring guide for new CUDA workloads.
- Add an architecture overview.
- Add a benchmarking methodology document.
- Add a troubleshooting guide.
- Add a contributor guide.
- Add a roadmap with MVP and post-MVP milestones.

### J. Release Readiness

- Define what "v0.1 usable" means.
- Define what "v1 complete" means.
- Add acceptance tests for the canonical sample projects.
- Verify behavior on at least one local Linux GPU setup.
- Verify behavior in notebook environments only after the local workflow is stable.
- Tag versions only after schema, runner, and docs are coherent.

## Definition Of A Complete MVP

WarpLab should not be considered complete until all of the following are true:

- A user can install dependencies from documented instructions.
- A user can run one command or one notebook flow and complete an end-to-end optimization run.
- Baseline and candidate artifacts are isolated and reproducible.
- Candidate correctness is validated against the actual candidate binary.
- Benchmark results are stable enough to compare candidates meaningfully.
- Run history and priors are stored with enough provenance to be useful later.
- Reports are generated automatically and reflect the true run outcome.
- A minimal automated test suite protects the core non-GPU logic.
- The README and examples match the actual product behavior.

## Suggested Documentation Set To Create

These are the docs I would add next.

- `README.md`: concise project overview, install, quickstart, current status
- `docs/architecture.md`: modules, data flow, run lifecycle
- `docs/project-spec.md`: `project.yaml` schema and command placeholders
- `docs/benchmarking.md`: methodology, repeats, CV, pitfalls
- `docs/sample-projects.md`: how SAXPY, reduction, and stencil examples are structured
- `docs/troubleshooting.md`: CUDA path issues, Nsight issues, notebook path issues, compile failures
- `CONTRIBUTING.md`: setup, tests, code standards, PR expectations
- `docs/roadmap.md`: MVP, v0.2, v1 goals

## Immediate Next 10 Tasks

If you want the shortest path to a credible repo, do these first:

1. Fix `projects/saxpy/validate.cu`.
2. Redesign command templating so outputs are explicit.
3. Make `compile_kernel()` honor `output_bin`.
4. Make validate and benchmark target the actual candidate artifact.
5. Remove candidate parallelism until artifact isolation is correct.
6. Move the notebook orchestration loop into a runner module.
7. Replace `eval()`-based constraints with a safe mechanism.
8. Add unit tests for config loading, search, DB operations, and report generation.
9. Rewrite the README to match the current state and prerequisites.
10. Add a CLI entry point for one reproducible sample run.

## Bottom Line

WarpLab has a good concept and a reasonable module layout, but it is not yet complete enough to trust for real optimization work.

The best way to finish it is:

- fix the execution pipeline first
- make the sample project real
- extract orchestration into a proper runner
- add tests and documentation only after the workflow is truthful

That sequence will turn the repo from "interesting scaffold" into "usable autotuning MVP."
