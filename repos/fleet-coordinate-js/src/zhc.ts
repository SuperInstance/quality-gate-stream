/**
 * Zero Holonomy Consensus — Loop Residual Computation
 * 
 * Hol(γ) = product of trust transformations around a cycle.
 * For a flat connection, Hol(γ) = I (identity), loop residual = 0.
 * 
 * The full ZHC consensus requires message passing and voting rounds
 * (lives in the Rust `holonomy-consensus` crate). This module provides
 * the geometric check: compute loop residual for a given cycle.
 * 
 * Simplified: we treat trust values as rotation angles.
 * A trust value t ∈ [-1, 1] maps to an angle θ = arccos(t) in [0, π].
 * The product of cosines around the cycle gives the loop residual.
 * 
 * For full geometric ZHC (3×3 rotation matrices), use the Rust crate.
 * This JS version is for client-side quick checks.
 */

import type { ZhcResult, TrustEdge } from './types.js';
import { trustToDirection, directionToTrust, DIRECTION_COUNT } from './pythagorean48.js';

/**
 * Compute the loop residual for a cycle in the trust graph.
 * 
 * For a flat connection, the product of trust transformations around any closed
 * cycle equals identity. Deviation from identity = loop residual.
 * 
 * Simplified method: 
 *   - Convert trust to angular displacement: θ = arccos(|trust|) * sign(trust)
 *   - Product of cosines around the cycle
 *   - Residual = 1 - product (0 = perfect flatness)
 * 
 * @param trustEdges - edges forming a cycle (last edge connects back to first)
 * @param tolerance - acceptable deviation (default 1e-6)
 */
export function computeLoopResidual(trustEdges: TrustEdge[], tolerance = 1e-6): ZhcResult {
  if (trustEdges.length < 3) {
    return {
      loop_residual: 0,
      consensus_reached: true,
      cycle_length: trustEdges.length,
    };
  }
  
  // Product of cosines around the cycle
  // We use the absolute trust value for the cosine product
  // The sign tells us whether the connection is reinforcing or opposing
  let cosProduct = 1.0;
  let negativeProduct = 1.0;  // product of signs
  
  for (const edge of trustEdges) {
    const trust = Math.max(-1, Math.min(1, edge.trust));
    const cosTheta = Math.cos(Math.acos(Math.abs(trust)));
    cosProduct *= cosTheta;
    
    // Track negative (opposing) connections
    if (trust < 0) {
      negativeProduct *= -1;
    }
  }
  
  // Loop residual: deviation from identity (0 = perfect)
  const loopResidual = Math.abs(1 - Math.abs(cosProduct));
  
  // Consensus reached if residual is within tolerance
  // AND the product of signs is positive (even number of negative edges)
  // A cycle with odd number of negative edges can't be flat
  const consensusReached = loopResidual < tolerance && negativeProduct > 0;
  
  return {
    loop_residual: loopResidual,
    consensus_reached: consensusReached,
    cycle_length: trustEdges.length,
  };
}

/**
 * Compute loop residual using Pythagorean48 direction indices.
 * More precise than floating-point trust values.
 * 
 * For direction d, the trust is: trust = cos(2π * d / 48)
 * The product of cosines around the cycle gives the residual.
 */
export function computeLoopResidualByDirection(
  directions: number[],
  tolerance = 1e-6
): ZhcResult {
  if (directions.length < 3) {
    return { loop_residual: 0, consensus_reached: true, cycle_length: directions.length };
  }
  
  let cosProduct = 1.0;
  let negativeCount = 0;
  
  for (const dir of directions) {
    const k = ((dir % DIRECTION_COUNT) + DIRECTION_COUNT) % DIRECTION_COUNT;
    // Direction 24-47 = negative trust
    if (k >= 24) negativeCount++;
    
    const trust = directionToTrust(dir);
    const cosTheta = Math.cos(Math.acos(Math.abs(trust)));
    cosProduct *= cosTheta;
  }
  
  const loopResidual = Math.abs(1 - Math.abs(cosProduct));
  const consensusReached = loopResidual < tolerance && negativeCount % 2 === 0;
  
  return {
    loop_residual: loopResidual,
    consensus_reached: consensusReached,
    cycle_length: directions.length,
  };
}

/**
 * Find all simple cycles in a fleet graph.
 * Uses a simple depth-first search.
 * 
 * This is expensive (O(V!) in worst case) — use only on small graphs.
 */
export function findCycles(
  edges: TrustEdge[],
  maxCycles = 10
): Array<TrustEdge[]> {
  // Build adjacency list
  const adj: Map<string, string[]> = new Map();
  
  for (const edge of edges) {
    if (!adj.has(edge.from)) adj.set(edge.from, []);
    if (!adj.has(edge.to)) adj.set(edge.to, []);
    adj.get(edge.from)!.push(edge.to);
    adj.get(edge.to)!.push(edge.from);
  }
  
  const cycles: Array<TrustEdge[]> = [];
  const visited = new Set<string>();
  
  function dfs(
    node: string,
    start: string,
    path: string[],
    depth: number
  ): void {
    if (cycles.length >= maxCycles) return;
    if (depth > 10) return;  // prevent runaway
    
    if (node === start && path.length >= 3) {
      // Found a cycle — build the edge list
      const cycleEdges: TrustEdge[] = [];
      for (let i = 0; i < path.length - 1; i++) {
        const from = path[i];
        const to = path[i + 1];
        const edge = edges.find(e =>
          (e.from === from && e.to === to) || (e.from === to && e.to === from)
        );
        if (edge) cycleEdges.push(edge);
      }
      cycles.push(cycleEdges);
      return;
    }
    
    if (visited.has(node)) return;
    visited.add(node);
    
    const neighbors = adj.get(node) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor) || neighbor === start) {
        dfs(neighbor, start, [...path, neighbor], depth + 1);
      }
    }
    
    visited.delete(node);
  }
  
  // Start DFS from each node
  for (const node of adj.keys()) {
    if (cycles.length >= maxCycles) break;
    visited.clear();
    dfs(node, node, [node], 0);
  }
  
  return cycles;
}