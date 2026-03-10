#include <chrono>
#include <iostream>
#include <string>
#include <vector>

#include <cuda_runtime.h>

#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

#ifndef ITEMS_PER_THREAD
#define ITEMS_PER_THREAD 4
#endif

__global__ void reduction_kernel(const float *input, float *partial, int n);

static bool checkCuda(cudaError_t status, const char *message) {
    if (status != cudaSuccess) {
        std::cerr << message << ": " << cudaGetErrorString(status) << std::endl;
        return false;
    }
    return true;
}

int main(int argc, char **argv) {
    int n = 16777216;
    int warmups = 5;
    int repeats = 40;

    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--size" && i + 1 < argc) n = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--warmups" && i + 1 < argc) warmups = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--repeats" && i + 1 < argc) repeats = std::stoi(argv[++i]);
    }

    const int blocks = (n + BLOCK_SIZE * ITEMS_PER_THREAD - 1) / (BLOCK_SIZE * ITEMS_PER_THREAD);
    std::vector<float> h_input(n, 1.0f);

    float *d_input = nullptr;
    float *d_partial = nullptr;

    if (!checkCuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(d_input)")) return 1;
    if (!checkCuda(cudaMalloc(&d_partial, blocks * sizeof(float)), "cudaMalloc(d_partial)")) return 1;
    if (!checkCuda(cudaMemcpy(d_input, h_input.data(), n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy H2D input")) return 1;

    for (int i = 0; i < warmups; ++i) {
        reduction_kernel<<<blocks, BLOCK_SIZE>>>(d_input, d_partial, n);
        if (!checkCuda(cudaGetLastError(), "kernel launch during warmup")) return 1;
    }
    if (!checkCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize after warmup")) return 1;

    for (int i = 0; i < repeats; ++i) {
        auto start = std::chrono::high_resolution_clock::now();
        reduction_kernel<<<blocks, BLOCK_SIZE>>>(d_input, d_partial, n);
        if (!checkCuda(cudaGetLastError(), "kernel launch")) return 1;
        if (!checkCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize")) return 1;
        auto end = std::chrono::high_resolution_clock::now();

        std::chrono::duration<float, std::milli> duration = end - start;
        std::cout << "{\"latency_ms\": " << duration.count()
                  << ", \"kernel\": \"reduction\", \"size\": " << n << "}" << std::endl;
    }

    cudaFree(d_input);
    cudaFree(d_partial);
    return 0;
}
