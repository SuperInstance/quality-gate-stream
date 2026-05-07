/**
 * @cocapn/fleet-coordinate-js
 * 
 * Pure TypeScript port of fleet-coordinate's geometric math.
 * No Rust, no WASM, no native dependencies.
 * 
 * Includes:
 * - Laman rigidity (E = 2V - 3)
 * - H¹ cohomology emergence detection (β₁ = E - V + C)
 * - Zero holonomy loop residual (simplified)
 * - Pythagorean48 trust encoding (48 directions, 5.585 bits/vector)
 * - Fleet graph builder and analysis utilities
 */

// Types
export type {
  RigidityResult,
  EmergenceResult,
  ZhcResult,
  TrustEdge,
  FleetNode,
  FleetEdge,
  FleetGraph,
  FullAnalysis,
} from './types.js';

// Core math
export { checkLamanRigidity, checkLamanSubgraphCondition } from './rigidity.js';
export { detectEmergence, betaOne } from './emergence.js';
export { computeLoopResidual, computeLoopResidualByDirection, findCycles } from './zhc.js';

// Pythagorean48
export {
  DIRECTION_COUNT,
  BITS_PER_VECTOR,
  DIRECTION_LABELS,
  trustToDirection,
  directionToTrust,
  trustVector,
  trustSimilarity,
  vectorDot,
  normalizeVector,
} from './pythagorean48.js';

// Graph utilities
export {
  buildFleetGraph,
  getNeighbors,
  quickCheck,
  analyzeFleetGraph,
  fromCoordinateGraph,
} from './graph.js';