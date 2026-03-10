#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

#ifndef UNROLL
#define UNROLL 1
#endif

#ifndef USE_SHARED
#define USE_SHARED 0
#endif

__global__ void stencil_kernel(const float *input, float *output, int n) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;

#if USE_SHARED
    __shared__ float tile[BLOCK_SIZE + 2];
    const int local = threadIdx.x + 1;

    if (i < n) {
        tile[local] = input[i];
        if (threadIdx.x == 0) {
            tile[0] = input[i > 0 ? i - 1 : i];
        }
        if (threadIdx.x == blockDim.x - 1 || i == n - 1) {
            const int right = i + 1 < n ? i + 1 : i;
            tile[local + 1] = input[right];
        }
    }
    __syncthreads();
#endif

    if (i >= n) {
        return;
    }

    if (i == 0 || i == n - 1) {
        output[i] = input[i];
        return;
    }

    #pragma unroll UNROLL
    for (int iter = 0; iter < 1; ++iter) {
#if USE_SHARED
        output[i] = 0.25f * tile[local - 1] + 0.5f * tile[local] + 0.25f * tile[local + 1];
#else
        output[i] = 0.25f * input[i - 1] + 0.5f * input[i] + 0.25f * input[i + 1];
#endif
    }
}
