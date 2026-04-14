# Ecosystem Map — Hub Repos

The SuperInstance/Lucineer ecosystem has ~600 repos. These are the hubs everything connects to.

## The Stack (Bottom Up)

```
┌─────────────────────────────────────┐
│  CraftMind / Log Apps / Fishing     │  ← Application Layer
├─────────────────────────────────────┤
│  DeckBoss (Agent Edge OS)           │  ← Orchestration
│  Fleet-Orchestrator (edge coord)    │
├─────────────────────────────────────┤
│  Cocapn (repo IS the agent)         │  ← Agent Definition
│  Git-Agent (git IS the nervous sys) │
├─────────────────────────────────────┤
│  FLUX Runtime (markdown→bytecode)   │  ← Runtime
│  Constraint Theory (exact geometry) │
├─────────────────────────────────────┤
│  CudaClaw (GPU 10K+ agents)         │  ← Metal
│  SmartCRDT (distributed state)      │
└─────────────────────────────────────┘
```

## Core Philosophy

**The repo IS the agent. Git IS the nervous system.**

Unlike LangChain/AutoGPT (centralized Python runtimes + external vector DBs):
1. **Git-Native** — Version control is the database. Reproducible by default.
2. **Edge-First** — Cloudflare Workers, not centralized servers.
3. **Performance** — Rust/CUDA lock-free queues + SmartCRDTs. 400K ops/s.
4. **Fork-First** — Fork it, customize it, deploy it. MIT license, no vendor lock-in.

## Tier 1: Core Runtime

| Hub | Role | Key Detail |
|-----|------|------------|
| **cocapn** | Repo-first agent runtime | Two repos/agent: private brain + public face. `npm create cocapn` |
| **git-agent** | Foundational repo-native agent | Git as nervous system |
| **fleet-orchestrator** | Stateless edge coordination | Cloudflare Workers, zero deps, circuit quarantine |

## Tier 2: Infrastructure

| Hub | Role | Key Detail |
|-----|------|------------|
| **cudaclaw** | GPU-resident agent orchestrator | Rust+CUDA, sub-10ms for 10K+ agents, 400K ops/s |
| **deckboss** | Agent Edge OS | Free tier: 10k inferences/day, 200k vectors, Durable Objects |
| **constraint-theory-core** | Deterministic geometric snapping | Rust crate, O(log n) KD-tree, exact Pythagorean coords |
| **flux-runtime** | Self-assembling runtime | Markdown → bytecode → VM, zero deps, pip install |

## Tier 3: Application Layer

| Hub | Role | Key Detail |
|-----|------|------------|
| **craftmind** | Minecraft AI player | Autonomous, LLM-driven, fork-first, transparent logs |
| **fishinglog-ai** | Edge AI fishing vessel | Jetson-powered species classification, captain voice |
| **ai-character-sdk** | Character SDK | Unified escalation, memory, learning API |

## Cross-Cutting

| Domain | Repos | Theme |
|--------|-------|-------|
| Memory | hierarchical-memory, Equipment-Memory-Hierarchy, collective-mind | Multi-tier cognitive memory |
| Trust | zero-trust-fleet, cuda-did, sovereign-identity, compliance-fork | Identity + compliance |
| Consensus | tripartite-rs, resonant-consensus, confidence-cascade | Multi-agent agreement |
| Learning | bandit-learner, frozen-model-rl, training-data-collector | Online + offline learning |

## Production Status

**Real and shipping:**
- `flux-runtime` — pip-installable, 1848 tests, zero deps
- `constraint-theory-core` — published on crates.io with docs.rs
- `deckboss` — deploys to user Cloudflare accounts
- `craftmind` — functioning autonomous Minecraft bot
- `cocapn` — npm package, live demo, CI passing
- `fleet-orchestrator` — live reference instance on Workers

**Not vaporware. These are real, working systems.**
