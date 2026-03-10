# Stencil Sample Project

This sample project benchmarks and validates a 1D three-point stencil.

It exists to exercise WarpLab on a bandwidth-sensitive kernel with a shared-memory toggle.

Files:

- `kernel.cu`: tunable stencil kernel
- `bench.cu`: machine-readable benchmark executable
- `validate.cu`: correctness executable
- `project.yaml`: WarpLab project specification

Tunable parameters currently exposed:

- `block_size`
- `unroll`
- `use_shared`
