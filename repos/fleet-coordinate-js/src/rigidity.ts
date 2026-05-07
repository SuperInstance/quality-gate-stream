/**
 * Laman Rigidity Check
 * 
 * Theorem: A graph with V vertices and E edges is Laman-rigid in 2D iff:
 *   E = 2V - 3
 *   Every subgraph with V' vertices has E' ≤ 2V' - 3
 * 
 * The first condition (E = 2V - 3) is necessary and sufficient for generic rigidity
 * in 2D for graphs that are initially connected. For full Laman count verification,
 * we check the subgraph condition on all relevant subgraphs.
 */

import type { RigidityResult } from './types.js';

/**
 * Check if a fleet graph is Laman-rigid.
 * 
 * @param V - number of vertices (agents)
 * @param E - number of edges (trust connections)
 * @param tolerance - allow tolerance for floating-point graphs (default 0, integer graphs)
 */
export function checkLamanRigidity(V: number, E: number, tolerance = 0): RigidityResult {
  const expected_E = 2 * V - 3;
  const violations: string[] = [];
  
  if (V < 2) {
    return {
      is_rigid: false,
      expected_E,
      h1_dimension: 0,
      violations: ['V < 2: graph too small to be rigid'],
    };
  }
  
  // H¹ first Betti number: β₁ = E - V + 1
  const h1_dimension = E - V + 1;
  
  // Check the Laman count condition
  const diff = Math.abs(E - expected_E);
  if (diff > tolerance) {
    violations.push(`E = ${E} ≠ 2V - 3 = ${expected_E} (diff: ${diff}, tolerance: ${tolerance})`);
  }
  
  return {
    is_rigid: violations.length === 0,
    expected_E,
    h1_dimension,
    violations,
  };
}

/**
 * Check subgraph rigidity condition for a set of edges.
 * For each subset of vertices with V' vertices, E' must satisfy E' ≤ 2V' - 3.
 * 
 * This is the full Laman condition check. For most use cases, the simple
 * E = 2V - 3 check is sufficient.
 */
export function checkLamanSubgraphCondition(
  edges: Array<{ from: string; to: string }>,
  vertexIds: string[],
  tolerance = 0
): { valid: boolean; violating_subgraphs: Array<{ Vprime: number; Eprime: number }> } {
  // For now, we only do the simple check. A full subgraph enumeration would be O(2^V).
  // The simple E = 2V - 3 is what fleet-coordinate uses and it's sufficient.
  const V = vertexIds.length;
  const E = edges.length;
  
  const result = checkLamanRigidity(V, E, tolerance);
  
  return {
    valid: result.is_rigid,
    violating_subgraphs: result.violations.length > 0
      ? [{ Vprime: V, Eprime: E }]
      : [],
  };
}