#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

#ifndef ITEMS_PER_THREAD
#define ITEMS_PER_THREAD 4
#endif

#ifndef UNROLL
#define UNROLL 1
#endif

__global__ void reduction_kernel(const float *input, float *partial, int n) {
    __shared__ float shared[BLOCK_SIZE];

    const int tid = threadIdx.x;
    const int block_offset = blockIdx.x * blockDim.x * ITEMS_PER_THREAD;
    float thread_sum = 0.0f;

    #pragma unroll UNROLL
    for (int item = 0; item < ITEMS_PER_THREAD; ++item) {
        const int idx = block_offset + tid + item * blockDim.x;
        if (idx < n) {
            thread_sum += input[idx];
        }
    }

    shared[tid] = thread_sum;
    __syncthreads();

    for (int stride = blockDim.x / 2; stride > 32; stride >>= 1) {
        if (tid < stride) {
            shared[tid] += shared[tid + stride];
        }
        __syncthreads();
    }

    if (tid < 32) {
        volatile float *warp = shared;
        warp[tid] += warp[tid + 32];
        warp[tid] += warp[tid + 16];
        warp[tid] += warp[tid + 8];
        warp[tid] += warp[tid + 4];
        warp[tid] += warp[tid + 2];
        warp[tid] += warp[tid + 1];
    }

    if (tid == 0) {
        partial[blockIdx.x] = shared[0];
    }
}
