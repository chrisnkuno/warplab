#include <cmath>
#include <iostream>
#include <string>
#include <vector>

#include <cuda_runtime.h>

#ifndef BLOCK_SIZE
#define BLOCK_SIZE 256
#endif

__global__ void stencil_kernel(const float *input, float *output, int n);

static bool checkCuda(cudaError_t status, const char *message) {
    if (status != cudaSuccess) {
        std::cerr << message << ": " << cudaGetErrorString(status) << std::endl;
        return false;
    }
    return true;
}

int main(int argc, char **argv) {
    int n = 1 << 20;
    float atol = 1e-5f;
    float rtol = 1e-5f;

    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--size" && i + 1 < argc) n = std::stoi(argv[++i]);
        if (std::string(argv[i]) == "--atol" && i + 1 < argc) atol = std::stof(argv[++i]);
        if (std::string(argv[i]) == "--rtol" && i + 1 < argc) rtol = std::stof(argv[++i]);
    }

    std::vector<float> h_input(n);
    std::vector<float> h_output(n, 0.0f);
    std::vector<float> h_expected(n, 0.0f);
    for (int i = 0; i < n; ++i) {
        h_input[i] = static_cast<float>(i % 251) * 0.01f;
    }

    h_expected[0] = h_input[0];
    h_expected[n - 1] = h_input[n - 1];
    for (int i = 1; i < n - 1; ++i) {
        h_expected[i] = 0.25f * h_input[i - 1] + 0.5f * h_input[i] + 0.25f * h_input[i + 1];
    }

    float *d_input = nullptr;
    float *d_output = nullptr;
    if (!checkCuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(d_input)")) return 1;
    if (!checkCuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(d_output)")) return 1;
    if (!checkCuda(cudaMemcpy(d_input, h_input.data(), n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy H2D input")) return 1;

    const int blocks = (n + BLOCK_SIZE - 1) / BLOCK_SIZE;
    stencil_kernel<<<blocks, BLOCK_SIZE>>>(d_input, d_output, n);
    if (!checkCuda(cudaGetLastError(), "kernel launch")) return 1;
    if (!checkCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize")) return 1;
    if (!checkCuda(cudaMemcpy(h_output.data(), d_output, n * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy D2H output")) return 1;

    float max_abs_diff = 0.0f;
    bool valid = true;
    for (int i = 0; i < n; ++i) {
        const float diff = std::fabs(h_output[i] - h_expected[i]);
        const float tolerance = atol + rtol * std::fabs(h_expected[i]);
        if (diff > tolerance) {
            valid = false;
        }
        if (diff > max_abs_diff) {
            max_abs_diff = diff;
        }
    }

    std::cout << "{\"valid\": " << (valid ? "true" : "false")
              << ", \"max_abs_diff\": " << max_abs_diff
              << "}" << std::endl;

    cudaFree(d_input);
    cudaFree(d_output);
    return 0;
}
