#include <cmath>
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
    int n = 1 << 20;
    float atol = 1e-4f;
    float rtol = 1e-4f;

    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--size" && i + 1 < argc) n = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--atol" && i + 1 < argc) atol = std::stof(argv[++i]);
        if (std::string(argv[i]) == "--rtol" && i + 1 < argc) rtol = std::stof(argv[++i]);
    }

    const int blocks = (n + BLOCK_SIZE * ITEMS_PER_THREAD - 1) / (BLOCK_SIZE * ITEMS_PER_THREAD);

    std::vector<float> h_input(n);
    for (int i = 0; i < n; ++i) {
        h_input[i] = 1.0f + static_cast<float>(i % 13) * 0.125f;
    }
    std::vector<float> h_partial(blocks, 0.0f);

    float *d_input = nullptr;
    float *d_partial = nullptr;
    if (!checkCuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(d_input)")) return 1;
    if (!checkCuda(cudaMalloc(&d_partial, blocks * sizeof(float)), "cudaMalloc(d_partial)")) return 1;
    if (!checkCuda(cudaMemcpy(d_input, h_input.data(), n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy H2D input")) return 1;

    reduction_kernel<<<blocks, BLOCK_SIZE>>>(d_input, d_partial, n);
    if (!checkCuda(cudaGetLastError(), "kernel launch")) return 1;
    if (!checkCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize")) return 1;
    if (!checkCuda(cudaMemcpy(h_partial.data(), d_partial, blocks * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy D2H partial")) return 1;

    double gpu_sum = 0.0;
    for (int i = 0; i < blocks; ++i) {
        gpu_sum += static_cast<double>(h_partial[i]);
    }

    double cpu_sum = 0.0;
    for (int i = 0; i < n; ++i) {
        cpu_sum += static_cast<double>(h_input[i]);
    }

    const double diff = std::fabs(gpu_sum - cpu_sum);
    const double tolerance = static_cast<double>(atol) + static_cast<double>(rtol) * std::fabs(cpu_sum);
    const bool valid = diff <= tolerance;

    std::cout << "{\"valid\": " << (valid ? "true" : "false")
              << ", \"gpu_sum\": " << gpu_sum
              << ", \"cpu_sum\": " << cpu_sum
              << ", \"abs_diff\": " << diff
              << "}" << std::endl;

    cudaFree(d_input);
    cudaFree(d_partial);
    return 0;
}
