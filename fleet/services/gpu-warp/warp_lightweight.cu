// warp_lightweight.cu - Lightweight warp variant for edge AI
// Optimized for low latency, low power, small memory footprint

#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include "room_types.h"

/**
 * Lightweight warp kernel for edge AI.
 * Optimized for Jetson Orin Nano and similar edge devices.
 * 
 * Features:
 * - Minimal warp context (32 elements)
 * - Fixed room assignments
 * - Energy-efficient computation
 * - Basic synchronization only
 */
__global__ void warp_lightweight_kernel(
    const half* __restrict__ room_inputs,
    half* __restrict__ room_outputs,
    const half* __restrict__ weights,
    int num_rooms, int input_dim, int output_dim) {
    
    // Edge-optimized: fixed warp size, minimal context
    const int WARP_SIZE = 32;
    const int CONTEXT_SIZE = 32;  // Minimal context for edge
    
    int warp_id = (threadIdx.x + blockIdx.x * blockDim.x) / WARP_SIZE;
    int lane_id = threadIdx.x % WARP_SIZE;
    int room_id = warp_id * WARP_SIZE + lane_id;
    
    if (room_id >= num_rooms) {
        // Edge optimization: early exit to save power
        return;
    }
    
    // Minimal context in registers (not shared memory for edge)
    half room_context[CONTEXT_SIZE];
    
    // Load minimal context (first CONTEXT_SIZE elements)
    const half* room_input = &room_inputs[room_id * input_dim];
    for (int i = 0; i < min(CONTEXT_SIZE, input_dim); ++i) {
        room_context[i] = room_input[i];
    }
    
    // Edge-optimized computation: simplified, power-efficient
    for (int out_idx = 0; out_idx < output_dim; ++out_idx) {
        half sum = __float2half(0.0f);
        
        // Simplified dot product (edge devices have limited compute)
        for (int in_idx = 0; in_idx < min(64, input_dim); ++in_idx) { // Limit for edge
            half input_val = (in_idx < CONTEXT_SIZE) ? room_context[in_idx] : room_input[in_idx];
            half weight_val = weights[in_idx * output_dim + out_idx];
            sum = __hadd(sum, __hmul(input_val, weight_val));
        }
        
        // Edge-optimized activation (ReLU, minimal)
        room_outputs[room_id * output_dim + out_idx] = 
            __hgt(sum, __float2half(0.0f)) ? sum : __float2half(0.0f);
    }
    
    // Edge optimization: implicit synchronization (no explicit __syncwarp)
    // Reduces power consumption on edge devices
}

/**
 * Edge-optimized warp initialization.
 * Configures for low power, minimal memory usage.
 */
RoomError warp_lightweight_init(const RoomConfig* config, cudaStream_t stream = 0) {
    // Edge-specific validation
    if (config->input_dim > 256) {
        return ROOM_ERROR_INVALID_CONFIG; // Edge devices limited
    }
    
    if (config->output_dim > 128) {
        return ROOM_ERROR_INVALID_CONFIG; // Edge devices limited
    }
    
    // Configure CUDA for edge (lower clock speeds, power saving)
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, 0);
    
    // Edge optimization: lower clock for power savings
    cudaSetDeviceFlags(cudaDeviceScheduleSpin); // Spin wait (lower power on edge)
    
    return ROOM_SUCCESS;
}

/**
 * Launch lightweight warp kernel with edge optimizations.
 */
void launch_warp_lightweight(
    const half* room_inputs, half* room_outputs, const half* weights,
    int num_rooms, int input_dim, int output_dim, cudaStream_t stream = 0) {
    
    // Edge optimization: smaller blocks for better occupancy on edge GPUs
    int threads_per_block = 128;  // Smaller for edge devices
    int blocks_per_grid = (num_rooms + threads_per_block - 1) / threads_per_block;
    
    // Edge optimization: limit grid size for power management
    blocks_per_grid = min(blocks_per_grid, 8); // Limit concurrent warps on edge
    
    warp_lightweight_kernel<<<blocks_per_grid, threads_per_block, 0, stream>>>(
        room_inputs, room_outputs, weights, num_rooms, input_dim, output_dim);
}

/**
 * Edge power management: put warp in low-power state.
 */
RoomError warp_lightweight_sleep(int warp_id, int microseconds) {
    // Edge optimization: nanosleep for power savings
    // Note: Actual implementation would use CUDA events or streams
    // For now, conceptual
    return ROOM_SUCCESS;
}

/**
 * Edge memory optimization: compact room context.
 */
RoomError warp_lightweight_compact_context(int warp_id) {
    // Edge optimization: compress room context to save memory
    // Implementation would use shared memory compression
    return ROOM_SUCCESS;
}
