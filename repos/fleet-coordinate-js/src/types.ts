/**
 * Core TypeScript interfaces for fleet-coordinate-js.
 * No external dependencies.
 */

export interface RigidityResult {
  is_rigid: boolean;
  expected_E: number;   // 2*V - 3
  h1_dimension: number;  // E - V + 1
  violations: string[];
}

export interface EmergenceResult {
  beta_one: number;
  detected: boolean;
  threshold: number;
  is_overconstrained: boolean;
}

export interface ZhcResult {
  loop_residual: number;
  consensus_reached: boolean;
  cycle_length: number;
}

export interface TrustEdge {
  from: string;
  to: string;
  trust: number;  // [-1, 1]
}

export interface FleetNode {
  id: string;
  label?: string;
}

export interface FleetEdge {
  from: string;
  to: string;
  trust: number;   // [-1, 1]
  weight?: number;
}

export interface FleetGraph {
  nodes: FleetNode[];
  edges: FleetEdge[];
  V: number;
  E: number;
  C: number;
}

export interface FullAnalysis {
  rigidity: RigidityResult;
  emergence: EmergenceResult;
  zhc: ZhcResult | null;
  is_self_coordinating: boolean;
}