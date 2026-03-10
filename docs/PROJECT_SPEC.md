# WarpLab Project Specification

Each WarpLab project is a directory that defines:

- the kernel source
- how to compile benchmark and validation binaries
- how to run them
- what parameters can be searched

## Required Files

A minimal project should contain:

- `project.yaml`
- `kernel.cu`
- one benchmark executable source file
- one validation executable source file

## `project.yaml`

Example shape:

```yaml
version: 1
name: saxpy
description: "SAXPY benchmark for WarpLab"

build:
  compile_kernel: >
    nvcc -O3 -lineinfo -o {artifact} bench.cu kernel.cu {flags}
  compile_validate: >
    nvcc -O3 -lineinfo -o {artifact} validate.cu kernel.cu {flags}

run:
  benchmark: "{artifact} --size {size} --warmups {warmups} --repeats {repeats}"
  validate: "{artifact} --size {size} --atol {atol} --rtol {rtol}"

input:
  size: 10000000
  repeats: 50

objective:
  metric: latency_ms
  direction: minimize

search_space:
  block_size: [64, 128, 256, 512]
  unroll: [1, 2, 4, 8]

constraints:
  - "block_size % 32 == 0"

validation:
  atol: 1e-6
  rtol: 1e-5

budget:
  max_experiments: 100
  warmup_runs: 5
  timed_runs: 20
  seed: 123
  patience: 10
  refinement_budget: 10
  refinement_top_k: 3
```

## Top-Level Fields

- `version`: project spec version
- `name`: short project name
- `description`: human-readable description
- `build`: compile command templates
- `run`: runtime command templates
- `input`: runtime inputs exposed to commands
- `objective`: metric name and optimization direction
- `search_space`: tunable parameters and candidate values
- `constraints`: safe arithmetic/logical expressions over search parameters
- `validation`: validator tolerances
- `budget`: search/benchmark budget controls

## Supported Command Placeholders

Build commands can use:

- `{artifact}`
- `{build_dir}`
- `{flags}`
- `{project_root}`

Run commands can use:

- `{artifact}`
- `{size}`
- `{warmups}`
- `{repeats}`
- `{atol}`
- `{rtol}`

Any values provided in `input`, `validation`, or runtime context can also be referenced.

## Benchmark Output Contract

The benchmark executable should print one JSON line per timed run, for example:

```json
{"latency_ms": 0.1234}
```

WarpLab parses these lines and computes:

- median latency
- mean latency
- standard deviation
- coefficient of variation

## Validator Output Contract

The validator executable should print a final JSON line, for example:

```json
{"valid": true, "max_abs_diff": 0.0}
```

WarpLab uses `valid` as the correctness gate.

## Search Budget Fields

These budget fields are currently supported:

- `max_experiments`
- `warmup_runs`
- `timed_runs`
- `seed`
- `patience`
- `refinement_budget`
- `refinement_top_k`

## Recommended Authoring Rules

- keep benchmark and validator separate
- make benchmark output machine-readable
- make validator output machine-readable
- expose only parameters that materially affect behavior
- keep constraints simple and explicit
- include a short `README.md` in each sample project
