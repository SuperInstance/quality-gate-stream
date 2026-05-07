/**
 * Fleet Graph Builder and Utilities
 * 
 * Constructs a FleetGraph from nodes and edges, computes derived values.
 * Provides higher-level analysis by combining rigidity + emergence + ZHC.
 */

import type { FleetGraph, FleetNode, FleetEdge, RigidityResult, EmergenceResult, ZhcResult, FullAnalysis } from './types.js';
import { checkLamanRigidity } from './rigidity.js';
import { detectEmergence } from './emergence.js';
import { computeLoopResidual, findCycles } from './zhc.js';

/**
 * Build a FleetGraph from raw nodes and edges.
 * Computes V (vertex count), E (edge count), C (connected components).
 */
export function buildFleetGraph(nodes: FleetNode[], edges: FleetEdge[]): FleetGraph {
  // Count connected components using BFS
  const adjacency = new Map<string, string[]>();
  
  for (const node of nodes) {
    adjacency.set(node.id, []);
  }
  
  for (const edge of edges) {
    adjacency.get(edge.from)?.push(edge.to);
    adjacency.get(edge.to)?.push(edge.from);
  }
  
  // BFS to count connected components
  const visited = new Set<string>();
  let C = 0;
  
  for (const node of nodes) {
    if (!visited.has(node.id)) {
      C++;
      const queue = [node.id];
      
      while (queue.length > 0) {
        const current = queue.shift()!;
        if (visited.has(current)) continue;
        visited.add(current);
        
        for (const neighbor of adjacency.get(current) || []) {
          if (!visited.has(neighbor)) {
            queue.push(neighbor);
          }
        }
      }
    }
  }
  
  return {
    nodes,
    edges,
    V: nodes.length,
    E: edges.length,
    C,
  };
}

/**
 * Get all neighbors of a node in the graph.
 */
export function getNeighbors(graph: FleetGraph, nodeId: string): string[] {
  const neighbors: string[] = [];
  
  for (const edge of graph.edges) {
    if (edge.from === nodeId) neighbors.push(edge.to);
    if (edge.to === nodeId) neighbors.push(edge.from);
  }
  
  return neighbors;
}

/**
 * Quick rigidity + emergence check without ZHC.
 * Use for hot-path checks (heartbeat, health monitoring).
 * 
 * @returns { is_rigid, beta_one, is_self_coordinating }
 */
export function quickCheck(graph: FleetGraph): {
  is_rigid: boolean;
  emergence_detected: boolean;
  beta_one: number;
  threshold: number;
} {
  const rigidity = checkLamanRigidity(graph.V, graph.E);
  const emergence = detectEmergence(graph.V, graph.E, graph.C);
  
  return {
    is_rigid: rigidity.is_rigid,
    emergence_detected: emergence.detected,
    beta_one: rigidity.h1_dimension,
    threshold: emergence.threshold,
  };
}

/**
 * Full analysis: rigidity + emergence + ZHC on detected cycles.
 * Use when you need the captain's complete picture.
 * 
 * @param graph - the fleet graph
 * @param checkCycles - whether to also check ZHC loop residual on detected cycles (default true)
 */
export function analyzeFleetGraph(graph: FleetGraph, checkCycles = true): FullAnalysis {
  const rigidity = checkLamanRigidity(graph.V, graph.E);
  const emergence = detectEmergence(graph.V, graph.E, graph.C);
  
  let zhc: ZhcResult | null = null;
  
  if (checkCycles && graph.edges.length >= 3) {
    // Find a few cycles and compute their loop residuals
    const cycles = findCycles(graph.edges, 3);
    
    if (cycles.length > 0) {
      // Use the first cycle's residual (most representative)
      zhc = computeLoopResidual(cycles[0]);
      
      // Check all cycles for consistency
      for (const cycle of cycles.slice(1)) {
        const residual = computeLoopResidual(cycle);
        // If any cycle has significantly different residual, flag it
        if (Math.abs(residual.loop_residual - (zhc?.loop_residual ?? 0)) > 1e-4) {
          // Cycles are inconsistent — fleet is not flat
          zhc = { loop_residual: 1, consensus_reached: false, cycle_length: 0 };
          break;
        }
      }
    }
  }
  
  const isSelfCoordinating = rigidity.is_rigid && !emergence.detected && (zhc === null || zhc.consensus_reached);
  
  return {
    rigidity,
    emergence,
    zhc,
    is_self_coordinating: isSelfCoordinating,
  };
}

/**
 * Convert an external FleetGraph (from fleet-coordinate Rust crate)
 * to our JS FleetGraph format.
 * 
 * The Rust FleetGraph has: V(), E(), neighbors(id), is_connected_to(other)
 * We normalize to our format here.
 */
export function fromCoordinateGraph(
  V: number,
  E: number,
  neighbors: (id: string) => string[],
  nodeIds: string[]
): FleetGraph {
  const nodes: FleetNode[] = nodeIds.map(id => ({ id }));
  
  // Reconstruct edges from neighbor relationships
  // This is approximate — we don't have the full edge list from the Rust struct
  // For exact conversion, the Rust side should provide edges directly
  const seen = new Set<string>();
  const edges: FleetEdge[] = [];
  
  for (const from of nodeIds) {
    for (const to of neighbors(from)) {
      const key = [from, to].sort().join('-');
      if (!seen.has(key)) {
        seen.add(key);
        edges.push({ from, to, trust: 0.5 });  // trust unknown in this conversion
      }
    }
  }
  
  return {
    nodes,
    edges,
    V,
    E,
    C: 1,  // assume connected for this conversion
  };
}