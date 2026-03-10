# SAXPY Sample Project

This is the reference WarpLab sample project.

It exists to prove the full loop:

1. compile a CUDA kernel
2. validate correctness
3. benchmark runtime
4. search over tunable parameters
5. generate a report

Files:

- `kernel.cu`: tunable kernel implementation
- `bench.cu`: machine-readable benchmark executable
- `validate.cu`: correctness executable
- `project.yaml`: WarpLab project specification

Tunable parameters currently exposed:

- `block_size`
- `unroll`
- `vector_width`

Use this project first when testing new WarpLab features.
