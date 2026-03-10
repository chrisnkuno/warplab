# Reduction Sample Project

This sample project benchmarks and validates a block-level sum reduction.

It exists to exercise WarpLab on a memory-heavy kernel with meaningful tuning knobs.

Files:

- `kernel.cu`: tunable reduction kernel
- `bench.cu`: machine-readable benchmark executable
- `validate.cu`: correctness executable
- `project.yaml`: WarpLab project specification

Tunable parameters currently exposed:

- `block_size`
- `items_per_thread`
- `unroll`
