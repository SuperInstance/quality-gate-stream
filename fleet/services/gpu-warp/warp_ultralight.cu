// warp_ultralight.cu - Ultra-lightweight warp variant for IoT and sensors
// Optimized for microcontrollers, low power, intermittent connectivity

#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include "room_types.h"

/**
 * Ultra-lightweight warp kernel for IoT devices.
 * Optimized for microcontrollers with GPU, low-power AI chips.
 * 
 * Features:
 * - Minimal memory footprint (<0.01 MB/warp)
 * - Energy-aware computation
 * - Sleep modes between inferences
 * - Intermittent connectivity support
 */
__global__ void warp_ultralight_kernel(
    const half* __restrict__ sensor_readings,
    half* __restrict__ sensor_outputs,
    const half* __restrict__ model_weights,
    int num_sensors, int reading_dim, int output_dim,
    int* sleep_flags, float battery_level) {
    
    // IoT optimization: very small warp for microcontrollers
    const int IOT_WARP_SIZE = 16;  // Half-size warp for IoT
    const int MAX_READINGS = 32;   // IoT devices have limited sensors
    
    int warp_id = (threadIdx.x + blockIdx.x * blockDim.x) / IOT_WARP_SIZE;
    int lane_id = threadIdx.x % IOT_WARP_SIZE;
    int sensor_id = warp_id * IOT_WARP_SIZE + lane_id;
    
    if (sensor_id >= num_sensors) {
        // IoT optimization: early exit to save power
        if (lane_id == 0 && sleep_flags) {
            sleep_flags[warp_id] = 1;  // Signal warp can sleep
        }
        return;
    }
    
    // IoT optimization: check battery level
    if (battery_level < 0.1f) {  // Critical battery
        // Minimal computation only
        for (int i = 0; i < output_dim; ++i) {
            sensor_outputs[sensor_id * output_dim + i] = __float2half(0.0f);
        }
        return;
    }
    
    // IoT optimization: registers only, no shared memory
    half sensor_reading[MAX_READINGS];
    
    // Load sensor readings (IoT devices have few sensors)
    const half* readings = &sensor_readings[sensor_id * reading_dim];
    for (int i = 0; i < min(MAX_READINGS, reading_dim); ++i) {
        sensor_reading[i] = readings[i];
    }
    
    // IoT-optimized computation: minimal, power-efficient
    for (int out_idx = 0; out_idx < output_dim; ++out_idx) {
        half sum = __float2half(0.0f);
        
        // Ultra-lightweight: process only essential readings
        int readings_to_process = (battery_level > 0.5f) ? reading_dim : reading_dim / 2;
        readings_to_process = min(readings_to_process, 16);  // IoT limit
        
        for (int in_idx = 0; in_idx < readings_to_process; ++in_idx) {
            half reading_val = sensor_reading[in_idx];
            half weight_val = model_weights[in_idx * output_dim + out_idx];
            
            // IoT optimization: approximate multiply-add
            sum = __hadd(sum, __hmul(reading_val, weight_val));
        }
        
        // IoT activation: simple threshold
        sensor_outputs[sensor_id * output_dim + out_idx] = 
            __hgt(sum, __float2half(0.0f)) ? __float2half(1.0f) : __float2half(0.0f);
    }
    
    // IoT optimization: signal completion for power management
    if (lane_id == IOT_WARP_SIZE - 1 && sleep_flags) {
        sleep_flags[warp_id] = 1;  // This warp can go to sleep
    }
}

/**
 * IoT power management: put warp in deep sleep.
 */
__device__ void iot_warp_sleep(int warp_id, int sleep_time_us) {
    // IoT optimization: minimal power state
    // Note: Actual implementation would use CUDA events or device sleep
    // For microcontrollers, might use actual sleep instructions
    
    // Signal sleep to host
    // (Implementation depends on IoT device capabilities)
}

/**
 * Initialize ultra-lightweight warp for IoT.
 */
RoomError warp_ultralight_init(const RoomConfig* config, cudaStream_t stream = 0) {
    // IoT-specific validation
    if (config->input_dim > 64) {
        return ROOM_ERROR_INVALID_CONFIG;  // IoT devices limited
    }
    
    if (config->output_dim > 16) {
        return ROOM_ERROR_INVALID_CONFIG;  // IoT devices limited
    }
    
    if (config->max_rooms > 256) {
        return ROOM_ERROR_INVALID_CONFIG;  // IoT devices limited
    }
    
    // Configure for ultra-low power
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, 0);
    
    // IoT optimization: lowest power mode
    // Note: Actual power management depends on device
    
    return ROOM_SUCCESS;
}

/**
 * Launch ultra-lightweight warp for IoT.
 */
void launch_warp_ultralight(
    const half* sensor_readings, half* sensor_outputs, const half* model_weights,
    int num_sensors, int reading_dim, int output_dim,
    int* sleep_flags, float battery_level, cudaStream_t stream = 0) {
    
    // IoT optimization: small blocks for microcontrollers
    int threads_per_block = 64;  // Small for IoT
    int blocks_per_grid = (num_sensors * 16 + threads_per_block - 1) / threads_per_block;
    blocks_per_grid = min(blocks_per_grid, 4);  // Limit for IoT
    
    warp_ultralight_kernel<<<blocks_per_grid, threads_per_block, 0, stream>>>(
        sensor_readings, sensor_outputs, model_weights,
        num_sensors, reading_dim, output_dim,
        sleep_flags, battery_level);
}

/**
 * IoT energy-aware scheduling.
 * Determines if computation should proceed based on battery.
 */
bool iot_should_compute(float battery_level, int computation_complexity) {
    // IoT optimization: skip computation if battery too low
    if (battery_level < 0.05f) {
        return false;  // Critical battery
    }
    
    // Adjust based on computation complexity
    float battery_threshold = 0.1f + computation_complexity * 0.05f;
    
    return battery_level > battery_threshold;
}

/**
 * IoT data compression for transmission.
 */
RoomError iot_compress_results(const half* results, int num_results,
                              half* compressed, int* compressed_size) {
    // IoT optimization: simple compression for transmission
    
    // Simple run-length encoding for binary outputs
    int idx = 0;
    int count = 0;
    half current = results[0];
    
    for (int i = 0; i < num_results; ++i) {
        if (results[i] == current && count < 255) {
            count++;
        } else {
            compressed[idx++] = current;
            compressed[idx++] = __int2half_rn(count);
            current = results[i];
            count = 1;
        }
    }
    
    // Store last run
    compressed[idx++] = current;
    compressed[idx++] = __int2half_rn(count);
    
    *compressed_size = idx;
    
    return ROOM_SUCCESS;
}

/**
 * IoT intermittent connectivity: buffer results when offline.
 */
RoomError iot_buffer_results(const half* results, int num_results,
                            half* buffer, int buffer_size, int* buffer_used) {
    // IoT optimization: store results when offline
    
    if (*buffer_used + num_results > buffer_size) {
        return ROOM_ERROR_CONTEXT_FULL;
    }
    
    for (int i = 0; i < num_results; ++i) {
        buffer[*buffer_used + i] = results[i];
    }
    
    *buffer_used += num_results;
    
    return ROOM_SUCCESS;
}
