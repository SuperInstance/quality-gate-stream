/**
 * H¹ Cohomology Emergence Detection
 * 
 * Formula: β₁ = E - V + C (first Betti number)
 * 
 * Emergence detection:
 * - Rigid fleet (E = 2V - 3, C = 1): emergence if β₁ > V - 2
 * - Non-rigid fleet: emergence if β₁ > V - 1
 * 
 * The H¹ cohomology detects when the graph has more independent cycles
 * than a minimally rigid graph should have — i.e., when the fleet is
 * over-constrained and something novel is emerging from the constraint structure.
 */

import type { EmergenceResult } from './types.js';

/**
 * Detect emergence using H¹ cohomology.
 * 
 * @param V - vertex count (agents)
 * @param E - edge count (trust connections)
 * @param C - connected components (default 1)
 * @param override_threshold - manual override for threshold
 */
export function detectEmergence(V: number, E: number, C = 1, override_threshold?: number): EmergenceResult {
  if (V < 2) {
    return {
      beta_one: 0,
      detected: false,
      threshold: override_threshold ?? 0,
      is_overconstrained: false,
    };
  }
  
  const beta_one = E - V + C;
  
  // Default threshold depends on whether fleet is Laman-rigid
  // Rigid fleet: threshold = V - 2 (since minimally rigid has β₁ = V-2)
  // Non-rigid: threshold = V - 1
  const is_rigid = E === 2 * V - 3;
  const default_threshold = is_rigid ? V - 2 : V - 1;
  const threshold = override_threshold ?? default_threshold;
  
  const detected = beta_one > threshold;
  
  return {
    beta_one,
    detected,
    threshold,
    is_overconstrained: detected,
  };
}

/**
 * Compute the H¹ first Betti number directly.
 * β₁ = E - V + C
 */
export function betaOne(V: number, E: number, C = 1): number {
  return E - V + C;
}