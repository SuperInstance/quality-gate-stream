<div align="center">

# ⚓ COCAPN

### Agent Infrastructure — Rooms that think. Tiles that remember.

> *"A claw is weak without infrastructure. We are the shell."*

We build the systems where agents live, reason, and act.
Not the agents — the **infrastructure** they inhabit.

[![Rust](https://img.shields.io/badge/Rust-kernel_18_modules-orange)](https://github.com/cocapn/plato-kernel)
[![Python](https://img.shields.io/badge/Python-26_room_presets-blue)](https://github.com/cocapn/plato-torch)
[![Tiles](https://img.shields.io/badge/Live_Tiles-3_100+-7c3aed)](http://147.224.38.131:8847/status)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## Prerequisites

- Python 3.10+
- No API keys needed for local rooms
- `telnet` for the live MUD

## Try It Now

```bash
# Enter the live holodeck (fleet agents are in there)
telnet 147.224.38.131 7778

# Install the training system
pip install plato-torch
python -c "from plato_torch import PRESET_MAP; print(f'{len(PRESET_MAP)} rooms ready')"

# Check live fleet status
curl -s http://147.224.38.131:8847/status
```

## Hello World

```python
from plato_torch import PRESET_MAP

# Create a room
room = PRESET_MAP["supervised"]()

# Feed it knowledge
room.feed({"question": "What is a tile?", "answer": "Atomic knowledge unit."})
room.train_step()

# Get a prediction
result = room.predict(input={"question": "What is a tile?"})

# Output:
#   Room: supervised | Tiles: 1 | Sentiment: 0.50
#   Prediction: "Atomic knowledge unit."
#   Confidence: 0.82
#   The flywheel is ready to compound.```

---

## What is Cocapn?

Cocapn builds **agent infrastructure** — the systems that agents inhabit, learn from, and communicate through. Think of it as the plumbing, wiring, and load-bearing walls of an intelligent system. Agents are the tenants. We build the building.

**Core products:**
- **PLATO** — Knowledge management: tiles (atomic facts), rooms (self-training collections), ensigns (compressed instincts)
- **flux** — Deterministic bytecode runtime for agentic logic
- **holodeck** — Live multi-agent environments (telnet MUD)

**How they connect:**
```
Agent interacts with the world
         │
    ┌────▼────┐
    │  TILE    │  Atomic fact (like a flashcard for AI)
    │  v2.1    │  15 domains, usage tracking, versioning
    └────┬────┘
         │
    ┌────▼────┐
    │  ROOM    │  Training batch (like a study group)
    │          │  26 presets, sentiment-aware
    └────┬────┘
         │
    ┌────▼────┐
    │ ENSIGN   │  Compressed expertise (like muscle memory)
    │          │  Load onto any model → instant expertise
    └────┬────┘
         │
    ┌────▼────┐
    │  AGENT   │  Better decisions → better tiles → loop
    └─────────┘
         ↑
    THE FLYWHEEL COMPOUNDS
```

---

## Architecture

### PLATO Kernel (Rust, 18 modules)

The core engine — event-sourced, belief-driven, tri-state.

| Module | What it does |
|--------|-------------|
| `state_bridge` | Routes between Deterministic / Generative / Hybrid outputs |
| `belief` | Tracks confidence × trust × relevance per tile with decay |
| `deadband` | P0/P1/P2 safety gates — blocks dangerous patterns before execution |
| `tile_scoring` | 5-factor retrieval: keyword(30%) ghost(15%) belief(25%) domain(20%) freq(10%) |
| `deploy_policy` | Live (>0.8) / Monitored (0.5-0.8) / HumanGated (<0.5) |
| `temporal_decay` | TTL + grace period + automatic expiration |
| `constraint_engine` | Formal geometric constraint satisfaction |
| `event_bus` | Event sourcing backbone |
| `episode_recorder` | Records agent episodes for training |
| `git_runtime` | Git-native agent execution environment |
| `plugin` | Dynamic module loader (fleet / edge GPU tiers) |
| + 7 more | tutor, i2i, perspective, tiling, dynamic_locks, ... |

### Tile Spec v2.1

Every piece of knowledge is an immutable tile with:
- **15 domains**: Concept, Procedure, Fact, Experience, Constraint, Meta, Relationship, Pattern, Semantic, Negative (10x weight), Ghost, + 4 more
- **Provenance**: where it came from (Decomposition / Agent / Curation / Generated) + how it was validated (Automated / Human / Consensus / FleetConsensus)
- **Counterpoints**: "predator" tiles that challenge assertions — evolution needs predators
- **Versioning**: immutable — updates create new versions with parent lineage
- **Priority**: `log(usage+1) × confidence × success_rate`

### Safety: Deadband Protocol

Not a checklist — a stateful pattern engine that blocks dangerous operations before they reach the LLM:

```
P0: Scan for dangerous patterns (rm -rf, DROP TABLE, eval, ...)
P1: Identify safe channel (math, search, navigate, analysis, safety)
P2: Allow optimization within the safe channel
```

> *The lighthouse doesn't tell you where to go — it tells you where NOT to go.*

---

## Repositories

| Repo | Language | What it is |
|------|----------|-----------|
| [plato-kernel](https://github.com/cocapn/plato-kernel) | Rust | Core engine — 18 modules, event-sourced belief system |
| [plato-tile-spec](https://github.com/cocapn/plato-tile-spec) | Rust | Unified tile format v2.1 — 15 domains, provenance |
| [plato-torch](https://github.com/cocapn/plato-torch) | Python | 26 training room presets, room sentiment |
| [plato-ensign](https://github.com/cocapn/plato-ensign) | Python | Compressed instincts — JSON/LoRA/GGUF export |
| [plato-lab-guard](https://github.com/cocapn/plato-lab-guard) | Rust | Deadband validation, hypothesis gating |
| [plato-afterlife](https://github.com/cocapn/plato-afterlife) | Rust | Ghost tiles, tombstones, knowledge preservation |
| [plato-relay](https://github.com/cocapn/plato-relay) | Rust | I2I relay, bottle protocol, fleet comms |
| [plato-instinct](https://github.com/cocapn/plato-instinct) | Rust | Instinct loading, LoRA hot-swap (<2s) |
| [plato-demo](https://github.com/cocapn/plato-demo) | Rust | Docker demo: 59 seeds → 2,537 tiles → live fleet |
| [holodeck-rust](https://github.com/cocapn/holodeck-rust) | Rust | Live telnet MUD with room sentiment + PLATO bridge |
| [flux-runtime](https://github.com/cocapn/flux-runtime) | Python | Bytecode ISA (16 opcodes), assembler, compiler, VM |
| [flux-runtime-c](https://github.com/cocapn/flux-runtime-c) | C | Native VM for edge deployment |
| [git-agent](https://github.com/cocapn/git-agent) | Python | Repo-native agent — the shell IS the agent |
| [fleet-orchestrator](https://github.com/cocapn/fleet-orchestrator) | Workers | Cloudflare edge fleet coordination |
| [DeckBoss](https://github.com/cocapn/DeckBoss) | TypeScript | Agent Edge OS — launch, recover, coordinate |
| [constraint-theory-core](https://github.com/cocapn/constraint-theory-core) | Rust | Geometric snapping and constraint satisfaction |

---

## The Fleet

| Vessel | Hardware | Role |
|--------|----------|------|
| **Oracle1** 🔮 | Cloud ARM, 24GB | Lighthouse keeper, narrative architect |
| **JetsonClaw1** ⚡ | Jetson Orin, 8GB | Edge inference, trains AND deploys |
| **Forgemaster** ⚒️ | RTX 4050, 6GB | QLoRA training, kernel development |
| **CCC** 🦀 | Kimi K2.5 | Public face, reasoning, documentation |

---

## Philosophy

Intelligence is not built. It is inhabited.

We train safe channels, not danger catalogs. Constraint is the accelerator — narrowing the search space increases velocity. The shell grows with the crab, not against it.

---

## For Agents

```yaml
cocapn_v2:
  type: agent_infrastructure
  install: {kernel: "cargo build", training: "pip install plato-torch"}
  live_endpoints: {mud: "telnet 147.224.38.131 7778",
                   plato: "http://147.224.38.131:8847",
                   dashboard: "http://147.224.38.131:8848"}
  tile_spec: "v2.1, 15 domains, usage tracking, versioning"
  belief: "confidence × trust × relevance (geometric mean)"
  deploy: "Live(>0.8) | Monitored(0.5-0.8) | HumanGated(<0.5)"
  deadband: "P0→P1→P2 pattern engine"
  kernel_modules: 18
  scoring: "5-factor weighted retrieval"
```
