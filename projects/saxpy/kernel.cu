#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

#ifndef UNROLL
#define UNROLL 1
#endif

#ifndef VECTOR_WIDTH
#define VECTOR_WIDTH 1
#endif

__global__ void saxpy_kernel(int n, float a, float *x, float *y) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Simple unoptimized implementation for v1
    // WarpLab will discover optimizations
    
    if (i < n) {
        #pragma unroll UNROLL
        for (int k = 0; k < VECTOR_WIDTH; ++k) {
            int idx = i * VECTOR_WIDTH + k;
            if (idx < n) {
                y[idx] = a * x[idx] + y[idx];
            }
        }
    }
}
