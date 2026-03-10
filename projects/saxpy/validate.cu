#include <iostream>
#include <vector>
#include <cuda_runtime.h>
#include <cmath>
#include <string>

#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

__global__ void saxpy_kernel(int n, float a, float *x, float *y);

static bool checkCuda(cudaError_t status, const char *message) {
    if (status != cudaSuccess) {
        std::cerr << message << ": " << cudaGetErrorString(status) << std::endl;
        return false;
    }
    return true;
}

int main(int argc, char **argv) {
    int n = 1000000; // Smaller size for validation
    float atol = 1e-6f;
    float rtol = 1e-5f;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--size" && i + 1 < argc) n = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--atol" && i + 1 < argc) atol = std::stof(argv[++i]);
        if (std::string(argv[i]) == "--rtol" && i + 1 < argc) rtol = std::stof(argv[++i]);
    }

    std::vector<float> h_x(n, 1.0f);
    std::vector<float> h_y(n, 2.0f);
    float a = 2.0f;

    float *d_x, *d_y;
    if (!checkCuda(cudaMalloc(&d_x, n * sizeof(float)), "cudaMalloc(d_x)")) return 1;
    if (!checkCuda(cudaMalloc(&d_y, n * sizeof(float)), "cudaMalloc(d_y)")) return 1;
    if (!checkCuda(cudaMemcpy(d_x, h_x.data(), n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy H2D x")) return 1;
    if (!checkCuda(cudaMemcpy(d_y, h_y.data(), n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy H2D y")) return 1;

    saxpy_kernel<<<(n + BLOCK_SIZE - 1) / BLOCK_SIZE, BLOCK_SIZE>>>(n, a, d_x, d_y);
    if (!checkCuda(cudaGetLastError(), "kernel launch")) return 1;
    if (!checkCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize")) return 1;
    if (!checkCuda(cudaMemcpy(h_y.data(), d_y, n * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy D2H y")) return 1;

    bool valid = true;
    float max_abs_diff = 0.0f;
    for (int i = 0; i < n; ++i) {
        float expected = 2.0f * 1.0f + 2.0f;
        float diff = std::abs(h_y[i] - expected);
        if (diff > atol + rtol * std::abs(expected)) valid = false;
        if (diff > max_abs_diff) max_abs_diff = diff;
    }

    std::cout << "{\"valid\": " << (valid ? "true" : "false") << ", \"max_abs_diff\": " << max_abs_diff << "}" << std::endl;

    cudaFree(d_x);
    cudaFree(d_y);
    return 0;
}
