// warp_game_ai.cu - Game AI variant for NPC coordination and real-time decision making

#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include <cooperative_groups.h>
#include "room_types.h"

namespace cg = cooperative_groups;

/**
 * Game AI warp kernel for NPC coordination.
 * Real-time decision making with warp-level behavior coordination.
 */
__global__ void warp_game_ai_kernel(
    const half* __restrict__ npc_states,      // NPC states [num_npcs x state_dim]
    half* __restrict__ npc_actions,           // NPC actions [num_npcs x action_dim]
    const half* __restrict__ game_world,      // Game world state
    const half* __restrict__ behavior_weights, // Behavior tree weights
    int num_npcs, int state_dim, int action_dim,
    float game_time, int* priority_queue) {
    
    // Warp for NPC group coordination
    cg::coalesced_group warp = cg::coalesced_threads();
    int warp_id = (threadIdx.x + blockIdx.x * blockDim.x) / warpSize;
    int lane_id = threadIdx.x % warpSize;
    int npc_id = warp_id * warpSize + lane_id;
    
    if (npc_id >= num_npcs) return;
    
    // Shared memory for NPC group coordination
    extern __shared__ half shared_coordination[];
    half* warp_shared = &shared_coordination[warp_id * 512];  // 512 elements per warp
    
    // Load NPC state
    const half* npc_state = &npc_states[npc_id * state_dim];
    for (int i = lane_id; i < state_dim; i += warpSize) {
        if (i < state_dim) {
            warp_shared[i] = npc_state[i];
        }
    }
    
    warp.sync();
    
    // ============================================
    // REAL-TIME NPC DECISION MAKING
    // ============================================
    
    // 1. Individual NPC decision (parallel within warp)
    half individual_decision[ACTION_DIM];
    make_individual_decision(warp_shared, lane_id, behavior_weights, 
                            individual_decision, action_dim);
    
    // 2. Warp-level NPC group coordination
    if (should_coordinate(warp_shared, lane_id)) {
        // NPCs in same warp can coordinate (e.g., squad tactics)
        half group_decision[ACTION_DIM];
        coordinate_with_group(warp_shared, lane_id, individual_decision, 
                             group_decision, action_dim, warp);
        
        // Blend individual and group decisions
        for (int i = 0; i < action_dim; ++i) {
            individual_decision[i] = __hadd(
                __hmul(individual_decision[i], __float2half(0.7f)),
                __hmul(group_decision[i], __float2half(0.3f))
            );
        }
    }
    
    // 3. Priority-based action selection (real-time constraint)
    int npc_priority = compute_priority(warp_shared, lane_id, game_time);
    
    // Warp-level priority coordination (higher priority NPCs act first)
    int warp_priority_mask = warp.ballot(npc_priority > PRIORITY_THRESHOLD);
    int high_priority_count = __popc(warp_priority_mask);
    
    // Real-time optimization: only high-priority NPCs get complex decisions
    if (npc_priority > PRIORITY_THRESHOLD || high_priority_count < warpSize / 4) {
        // High priority or few high-priority NPCs → full decision
        for (int i = 0; i < action_dim; ++i) {
            npc_actions[npc_id * action_dim + i] = individual_decision[i];
        }
    } else {
        // Low priority → simplified decision for real-time performance
        half simplified = compute_simplified_action(warp_shared, lane_id);
        for (int i = 0; i < action_dim; ++i) {
            npc_actions[npc_id * action_dim + i] = simplified;
        }
    }
    
    // 4. Update priority queue for next frame
    if (lane_id == 0) {
        priority_queue[warp_id] = high_priority_count;
    }
    
    warp.sync();
}

/**
 * Individual NPC decision making.
 */
__device__ void make_individual_decision(
    const half* warp_shared, int lane_id,
    const half* behavior_weights,
    half* decision, int action_dim) {
    
    // Behavior tree-like decision making
    const half* npc_state = &warp_shared[lane_id * 32];  // NPC state in shared memory
    
    // Simple neural decision for demonstration
    for (int act = 0; act < action_dim; ++act) {
        half sum = __float2half(0.0f);
        
        for (int state_idx = 0; state_idx < 32; ++state_idx) {
            half state_val = npc_state[state_idx];
            half weight_val = behavior_weights[state_idx * action_dim + act];
            sum = __hfma(state_val, weight_val, sum);
        }
        
        // Game AI activation (often tanh for bounded actions)
        float fsum = __half2float(sum);
        float activated = tanhf(fsum);
        decision[act] = __float2half(activated);
    }
}

/**
 * Determine if NPC should coordinate with warp group.
 */
__device__ bool should_coordinate(const half* warp_shared, int lane_id) {
    // Check if NPC is part of a coordinated group (squad, team, etc.)
    half coordination_flag = warp_shared[lane_id * 32 + 31];  // Last state element
    return __hgt(coordination_flag, __float2half(0.5f));
}

/**
 * Coordinate decisions with NPCs in same warp.
 */
__device__ void coordinate_with_group(
    const half* warp_shared, int lane_id,
    const half* individual_decision,
    half* group_decision, int action_dim,
    cg::coalesced_group warp) {
    
    // Warp-level coordination (e.g., squad tactics)
    
    // 1. Share individual decisions
    half shared_decisions[warpSize * ACTION_DIM];
    for (int i = 0; i < action_dim; ++i) {
        shared_decisions[lane_id * action_dim + i] = individual_decision[i];
    }
    
    // 2. Warp leader computes group strategy
    if (lane_id == 0) {
        // Simple average strategy for demonstration
        for (int act = 0; act < action_dim; ++act) {
            half sum = __float2half(0.0f);
            for (int npc = 0; npc < warpSize; ++npc) {
                sum = __hadd(sum, shared_decisions[npc * action_dim + act]);
            }
            group_decision[act] = __hdiv(sum, __int2half_rn(warpSize));
        }
        
        // Share group decision
        for (int npc = 1; npc < warpSize; ++npc) {
            for (int act = 0; act < action_dim; ++act) {
                shared_decisions[npc * action_dim + act] = group_decision[act];
            }
        }
    }
    
    warp.sync();
    
    // 3. All NPCs get group decision
    for (int i = 0; i < action_dim; ++i) {
        group_decision[i] = shared_decisions[lane_id * action_dim + i];
    }
}

/**
 * Compute NPC priority for real-time scheduling.
 */
__device__ int compute_priority(const half* warp_shared, int lane_id, float game_time) {
    // Priority based on:
    // 1. Distance to player
    // 2. Health
    // 3. Threat level
    // 4. Recent activity
    
    half distance_to_player = warp_shared[lane_id * 32 + 0];
    half health = warp_shared[lane_id * 32 + 1];
    half threat_level = warp_shared[lane_id * 32 + 2];
    
    // Higher priority for close, low-health, high-threat NPCs
    float priority = 100.0f;
    priority -= __half2float(distance_to_player) * 10.0f;  // Closer = higher priority
    priority += (1.0f - __half2float(health)) * 50.0f;     // Lower health = higher priority
    priority += __half2float(threat_level) * 30.0f;        // Higher threat = higher priority
    
    // Time-based priority decay
    priority *= (1.0f - fmod(game_time, 1.0f) * 0.1f);
    
    return (int)priority;
}

/**
 * Simplified action for low-priority NPCs (real-time optimization).
 */
__device__ half compute_simplified_action(const half* warp_shared, int lane_id) {
    // Very simple decision for real-time performance
    half last_action = warp_shared[lane_id * 32 + 30];  // Last action
    half randomness = __float2half((lane_id % 10) * 0.1f);  // Some variety
    
    // 70% chance to repeat last action, 30% random
    if ((lane_id + (int)(__half2float(randomness) * 100)) % 10 < 7) {
        return last_action;
    } else {
        return randomness;
    }
}

/**
 * Initialize game AI warp for real-time NPC coordination.
 */
RoomError warp_game_ai_init(const RoomConfig* config, cudaStream_t stream = 0) {
    // Game AI needs real-time performance
    if (config->context_size < 32) {
        return ROOM_ERROR_INVALID_CONFIG;  // Need enough state for NPCs
    }
    
    // Set CUDA for real-time (lower latency)
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, 0);
    
    // Real-time optimization: prefer lower latency over throughput
    cudaSetDeviceFlags(cudaDeviceScheduleSpin);  // Spin wait for lower latency
    
    return ROOM_SUCCESS;
}

/**
 * Launch game AI warp kernel.
 */
void launch_warp_game_ai(
    const half* npc_states, half* npc_actions,
    const half* game_world, const half* behavior_weights,
    int num_npcs, int state_dim, int action_dim,
    float game_time, int* priority_queue, cudaStream_t stream = 0) {
    
    // Game AI: many NPCs, real-time constraints
    int threads_per_block = 256;
    int blocks_per_grid = (num_npcs + threads_per_block - 1) / threads_per_block;
    
    // Shared memory for NPC coordination
    size_t shared_mem_size = (threads_per_block / warpSize) * 512 * sizeof(half);
    
    warp_game_ai_kernel<<<blocks_per_block, threads_per_block, shared_mem_size, stream>>>(
        npc_states, npc_actions, game_world, behavior_weights,
        num_npcs, state_dim, action_dim, game_time, priority_queue);
}

/**
 * Real-time scheduling: update NPC priorities based on game events.
 */
RoomError warp_update_priorities(int* priorities, int num_npcs,
                                const float* game_events, int num_events) {
    // Update NPC priorities based on game events
    // Real-time optimization: batch updates
    
    for (int i = 0; i < num_npcs; ++i) {
        // Base priority
        int priority = priorities[i];
        
        // Apply event influences
        for (int e = 0; e < num_events; ++e) {
            // Simple influence: events affect nearby NPCs
            float event_influence = game_events[e * 3 + 2];  // Event strength
            // (In real implementation, would compute distance, etc.)
            
            if (event_influence > 0.5f) {
                priority += (int)(event_influence * 100.0f);
            }
        }
        
        // Clamp priority
        priorities[i] = min(priority, 1000);
    }
    
    return ROOM_SUCCESS;
}

/**
 * Dynamic NPC grouping based on spatial proximity.
 */
RoomError warp_group_npcs(const float* npc_positions, int num_npcs,
                         float group_radius, int* group_assignments) {
    // Simple spatial grouping for warp assignment
    // Real implementation would use spatial hashing or similar
    
    int current_group = 0;
    int npcs_in_group = 0;
    const int GROUP_SIZE = 32;  // Warp size
    
    for (int i = 0; i < num_npcs; ++i) {
        group_assignments[i] = current_group;
        npcs_in_group++;
        
        if (npcs_in_group >= GROUP_SIZE) {
            current_group++;
            npcs_in_group = 0;
        }
    }
    
    return ROOM_SUCCESS;
}
