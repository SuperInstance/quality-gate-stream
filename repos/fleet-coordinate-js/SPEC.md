# fleet-coordinate-js — Specification

**Pure TypeScript port of fleet-coordinate's geometric math. No Rust, no WASM, no native dependencies. Runs anywhere JS runs. **

---

## Why Port to JS?

fleet-coordinate (Rust) does Laman rigidity, H¹ cohomology, ZHC consensus, and Pythagorean48 encoding. These are all just math — no system calls, no OS APIs, no Rust-specific algorithms. Porting to TypeScript means:

- **Browser-native** — no WASM compilation step, no Emscripten, no binary compatibility issues
- **Smaller bundle** — pure TS compiles to ~15KB minified for the core math
- **Works in PLATO room server** — our room server is Python, not Rust; we can call this directly
- **Capable devices** — any device with a JS engine has access to the full fleet-math geometric layer

---

## What's Included

### 1. Laman Rigidity

**Theorem:** A graph with V vertices and E edges is Laman-rigid iff E = 2V - 3 and every subgraph with V' vertices has E' ≤ 2V' - 3.

```typescript
interface RigidityResult {
  is_rigid: boolean;
  expected_E: number;        // 2*V - 3
  h1_dimension: number;      // E - V + 1 (H¹ first Betti number)
  violations: string[];      // if not rigid, why
}

/**
 * Check if a fleet graph is Laman-rigid.
 * E = 2V - 3 for a generically rigid graph in 2D.
 * 
 * @param V - number of vertices (agents)
 * @param E - number of edges (trust connections)
 * @param tolerance - allow 5% tolerance for floating-point graphs (default 0.05)
 */
function checkLamanRigidity(V: number, E: number, tolerance = 0.05): RigidityResult
```

### 2. H¹ Cohomology Emergence Detection

**Formula:** β₁ = E - V + C (first Betti number = number of independent cycles)

```typescript
interface EmergenceResult {
  beta_one: number;
  detected: boolean;
  threshold: number;       // V - 2 for rigid fleet, else more
  is_overconstrained: boolean;
}

/**
 * Detect emergence using H¹ cohomology.
 * Emergence = β₁ > V - 2 (for rigid fleet).
 * For non-rigid fleets, emergence = β₁ > V - 1.
 * 
 * @param V - vertex count
 * @param E - edge count  
 * @param C - connected components (default 1)
 * @param override_threshold - manual threshold override
 */
function detectEmergence(V: number, E: number, C = 1, override_threshold?: number): EmergenceResult
```

**Significance:** 127 lines replacing a 12K-line ML classifier. No training data. Topologically grounded.

### 3. Zero Holonomy Consensus (Simplified)

The full ZHC consensus from `holonomy-consensus` crate requires matrix operations. For the JS port, we provide the simplified version that computes the loop residual for a given cycle.

```typescript
interface ZhcResult {
  loop_residual: number;   // deviation from identity (0 = perfect)
  consensus_reached: boolean;
  cycle_length: number;
}

/**
 * Compute loop residual for a cycle in the trust graph.
 * Hol(γ) = product of trust transformations around the cycle.
 * For a flat connection, Hol(γ) = I, loop residual = 0.
 * 
 * @param trustEdges - array of {from, to, trust} edges forming a cycle
 * @param tolerance - acceptable deviation from identity (default 1e-6)
 */
function computeLoopResidual(trustEdges: TrustEdge[], tolerance = 1e-6): ZhcResult

interface TrustEdge {
  from: string;
  to: string;
  trust: number;  // [-1, 1]
}
```

### 4. Pythagorean48 Trust Encoding

48 exact directions on the unit circle. log₂(48) = 5.585 bits per vector — maximum information per bit for 16-bit integers.

```typescript
/**
 * The 48 exact directions (Pythagorean quantization).
 * Each direction corresponds to an angle: k * 360/48 degrees for k in [0, 47].
 */
const DIRECTION_COUNT = 48;
const BITS_PER_VECTOR = Math.log2(48);  // 5.58496

/**
 * Convert a trust value in [-1, 1] to a Pythagorean48 direction index.
 * trust = 1.0 → direction 0 (0°)
 * trust = -1.0 → direction 24 (180°)
 */
function trustToDirection(trust: number): number

/**
 * Convert a direction index back to a trust value.
 */
function directionToTrust(dir: number): number

/**
 * Compute trust vector for an agent pair using Pythagorean48.
 * Returns the 48-dimensional unit vector in direction dir.
 */
function trustVector(dir: number): number[]  // 48-element vector, all zeros except direction
```

### 5. Fleet Graph Utilities

```typescript
interface FleetNode {
  id: string;
  label?: string;
}

interface FleetEdge {
  from: string;
  to: string;
  trust: number;   // [-1, 1]
  weight?: number;
}

interface FleetGraph {
  nodes: FleetNode[];
  edges: FleetEdge[];
  V: number;
  E: number;
  C: number;  // connected components
}

/**
 * Build a FleetGraph from nodes and edges.
 * Automatically computes V, E, C.
 */
function buildFleetGraph(nodes: FleetNode[], edges: FleetEdge[]): FleetGraph

/**
 * Get all neighbors of a node.
 */
function getNeighbors(graph: FleetGraph, nodeId: string): string[]

/**
 * Full rigidity + emergence + ZHC analysis.
 * Combines all checks into a single call.
 */
interface FullAnalysis {
  rigidity: RigidityResult;
  emergence: EmergenceResult;
  zhc: ZhcResult | null;  // null if no cycles
  is_self_coordinating: boolean;  // true only if rigid + no emergence
}

function analyzeFleetGraph(graph: FleetGraph): FullAnalysis
```

---

## What We DON'T Port

- The full `ZhcConsensus::run_consensus()` — this requires the consensus protocol (message passing, voting rounds). For the browser, we only need the geometric check (loop residual). The full consensus lives in the Rust `holonomy-consensus` crate.
- The graph visualization (SVG generation) — that's a presentation concern, not math. Keep the math pure.
- The PLATO room server integration — that's `@cocapn/plato-client`. Separate package.

---

## File Structure

```
fleet-coordinate-js/
  src/
    index.ts              # exports all public functions
    rigidity.ts           # Laman rigidity check
    emergence.ts          # H¹ emergence detection
    zhc.ts                # Zero holonomy loop residual
    pythagorean48.ts      # 48-direction trust encoding
    graph.ts              # FleetGraph builder + utilities
    types.ts              # shared TypeScript interfaces
  tests/
    rigidity.test.ts
    emergence.test.ts
    zhc.test.ts
    pythagorean48.test.ts
    graph.test.ts
  package.json
  tsconfig.json
```

---

## Package Metadata

```json
{
  "name": "@cocapn/fleet-coordinate-js",
  "version": "0.1.0",
  "description": "Fleet coordinate geometric math in pure TypeScript — Laman rigidity, H¹, ZHC, Pythagorean48. No WASM.",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "exports": {
    ".": { "import": "./dist/index.js", "types": "./dist/index.d.ts" }
  },
  "keywords": ["fleet", "coordinate", "laman", "h1", "zhc", "pythagorean", "cocapn"]
}
```

---

## Dependencies

**None.** Pure TypeScript, no external packages.

---

## Test Scenarios

```typescript
// Laman rigidity
checkLamanRigidity(4, 5)  // { is_rigid: true, expected_E: 5, h1_dimension: 2 }
// 4 nodes, 5 edges = 2*4-3 = 5 → Laman rigid, β₁ = 5-4+1 = 2

// Emergence detection  
detectEmergence(10, 25)    // β₁ = 25-10+1 = 16, threshold = 10-2=8 → detected: true
detectEmergence(10, 17)    // β₁ = 17-10+1 = 8, threshold = 8 → detected: false

// Pythagorean48
trustToDirection(0.5)      // → some direction in [0, 47]
directionToTrust(12)       // → trust value in [-1, 1]

// Loop residual
const cycle: TrustEdge[] = [
  { from: 'A', to: 'B', trust: 0.9 },
  { from: 'B', to: 'C', trust: 0.8 },
  { from: 'C', to: 'A', trust: 0.85 },
];
computeLoopResidual(cycle)  // → { loop_residual: ~0, consensus_reached: true }
```

---

## Bundle Size Target

< 20KB minified + gzipped for the complete library (all modules). The Pythagorean48 table alone is 48 floats = 384 bytes. Everything else is just arithmetic.