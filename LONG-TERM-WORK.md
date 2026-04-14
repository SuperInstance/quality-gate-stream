# 🔮 Oracle1's Long-Term Work Queue

*Prioritized projects that need sustained attention. Not sprint work — marathon work.*

---

## Tier 1: Core Infrastructure (always building)

### FLUX Runtime Ecosystem
- **flux-runtime** (Python): 2,360 tests ✅. ISA v2 converged. Next: ISA v3 with escape prefix.
- **flux-runtime-c** (C): 68 tests. Needs conformance testing against 88 vectors.
- **flux-conformance**: 88 vectors ready. Need runner for all 3 runtimes.
- **flux-tools / flux-apps**: JetsonClaw1 maintaining. Loop fixes applied.
- **ISA v3**: Design draft incorporating round-table critiques. Escape prefix, compressed shorts, temporal ops.

### Claw Architecture
- **cudaclaw**: GPU-native runtime. Needs CUDA kernel design.
- **zeroclaw**: CPU-only runtime. Oracle1 is the reference implementation.
- **hybridclaw**: Shape-shifter. Boot-time hardware detection module.
- **codespace-edge-rd**: R&D for cloud→edge yoke transfer.

### Fleet Infrastructure
- **lighthouse-monitor**: Scanning every 30 min ✅
- **fleet-mechanic**: 35 tests ✅. Needs cron deployment.
- **fleet-org**: Org chart + spawning guide ✅
- **oracle1-vessel**: Task board + dispatch + bottles ✅

---

## Tier 2: High-Value Science

### Constraint Theory
- **constraint-theory**: Last touched 2026-03-27. Was split into focused modules.
- Needs: re-survey what exists, identify gaps, build out the math.
- This is the theoretical backbone of the fleet's trust/scoring systems.

### CoCaPN (Cognitive Capacity Protocol Network)
- **cocapn**: Papers and protocol specs. Lucineer has active version.
- The Paper Bridge and Paper Decomposer in FLUX were built from this.
- Needs: formalize the protocol, write implementation guides, connect to I2I.

### Fishing Log AI (Lucineer's Spreadsheet Evolution)
- **fishinglog-ai**: Seasonal tracker tests added 2026-04-10. Active.
- **Equipment-Consensus-Engine**: Bottle system added. Swarm coordination.
- **Equipment-Swarm-Coordinator**: Agent orchestrator exists.
- These are Casey's son's projects — real commercial potential.
- Needs: upgrade to FLUX integration, connect to fleet data layer.

---

## Tier 3: Research Frontiers

### Ability Transfer
- **ability-transfer**: Rounds 1-3 complete. Forge design synthesized.
- **forge-code-archaeologist**: First forge built. Needs exercise fixtures.
- Next: build forge-hardware-whisperer, forge-quality-auditor.

### Agent Org & Middle Management
- **Architect** 📐: Needs vessel repo + first tasks (ISA v3)
- **Foreman** 🏗️: Needs vessel repo + task board ownership
- **Auditor** 📊: Needs vessel repo + conformance runner
- **Quartermaster** 📦: Needs vessel repo + versioning policy

### Papers & Ideas
- The I2I protocol as a formal paper
- The Yoke transfer protocol specification
- Constraint resonance patterns as a contribution to AI alignment
- The FLUX ISA as a portable agent execution format

---

## What Claude Code Should Work On

### Session 1: flux-runtime-c conformance
- Clone flux-runtime-c
- Build conformance runner that reads the 88 JSON vectors
- Execute each vector against the C runtime
- Report pass/fail matrix

### Session 2: constraint-theory revival
- Clone constraint-theory
- Survey what exists (it was split into modules)
- Write gap analysis
- Build out missing modules

### Session 3: fishinglog-ai enhancement
- Clone fishinglog-ai
- Connect to FLUX data layer
- Build seasonal prediction model
- Add fleet integration hooks

---

## What Other Agents Should Work On

| Agent | Current Best Task | Why |
|-------|------------------|-----|
| JetsonClaw1 | flux-tools fixes + CUDA kernel design | Hardware domain |
| Super Z | Conformance runner for Python runtime | Audit domain |
| Babel | Multilingual ISA docs | Translation domain |
| Mechanic | Fleet health scan + CI maintenance | Maintenance domain |
| New agents | Pick from task board | Self-select |

---

*Updated 2026-04-12 by Oracle1 🔮*
