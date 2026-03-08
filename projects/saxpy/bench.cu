#include <iostream>
#include <vector>
#include <cuda_runtime.h>
#include <chrono>

#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

__global__ void saxpy_kernel(int n, float a, float *x, float *y);

int main(int argc, char **argv) {
    int n = 10000000;
    int repeats = 50;
    
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--size" && i + 1 < argc) n = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--repeats" && i + 1 < argc) repeats = std::stoi(argv[++i]);
    }

    float *d_x, *d_y;
    cudaMalloc(&d_x, n * sizeof(float));
    cudaMalloc(&d_y, n * sizeof(float));
    
    float a = 2.0f;
    
    // Warmup
    for (int i = 0; i < 5; ++i) {
        saxpy_kernel<<<(n + BLOCK_SIZE - 1) / BLOCK_SIZE, BLOCK_SIZE>>>(n, a, d_x, d_y);
    }
    cudaDeviceSynchronize();

    for (int i = 0; i < repeats; ++i) {
        auto start = std::chrono::high_resolution_clock::now();
        saxpy_kernel<<<(n + BLOCK_SIZE - 1) / BLOCK_SIZE, BLOCK_SIZE>>>(n, a, d_x, d_y);
        cudaDeviceSynchronize();
        auto end = std::chrono::high_resolution_clock::now();
        
        std::chrono::duration<float, std::milli> duration = end - start;
        std::cout << "{\"latency_ms\": " << duration.count() << ", \"kernel\": \"saxpy\", \"size\": " << n << "}" << std::endl;
    }

    cudaFree(d_x);
    cudaFree(d_y);
    return 0;
}
