<div align="center">

```
                             |    |
                            )_)  )_)
                           )___))___)\\
                          )____)____)\\\\
                        _____|____|____\\\\
      \.___.|\        \---------.--.  |
     /______|_\        \_________|__| /
     \*.*  | /                  / / /
      \____|/                  /_/_/
```

# COCAPN ⚓

### Agent Infrastructure — The Shell for Intelligence

> *"A claw is weak without infrastructure. We are the shell."*

We build the foundational systems where agents live, reason, and act.  
Not the agents themselves — the **world** they inhabit.  
Like the hermit crab, an agent's potential is unlocked by the shell it occupies.  
We forge those shells.

[![Fleet](https://img.shields.io/badge/fleet-3_vessels-0ea5e9)](https://github.com/cocapn)
[![PLATO](https://img.shields.io/badge/plato-2_300+_tiles-7c3aed)](https://github.com/cocapn/plato-tile-spec)
[![Rooms](https://img.shields.io/badge/rooms-14_active-f59e0b)](https://github.com/cocapn/plato-torch)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## For Agents 🤖

```yaml
cocapn_org_profile_v1:
  purpose: provider_of_agent_infrastructure
  core_products:
    plato: spatial_state_environments_with_training
    flux: deterministic_bytecode_runtime_for_agents
    holodeck: live_multi_agent_simulation
  metaphor: hermit_crab_shell
  tagline: "A claw is weak without infrastructure. We are the shell."
  access: https://github.com/cocapn
  protocol: deadband  # P0→P1→P2
  fleet_communication: bottle_protocol  # git-native
  ensign_format: universal  # load onto any model
```

---

## Our Pillars

### 🏛️ PLATO — Programmable Learning Architecture for Training Oracles

A safety-first scaffolding system where agents accumulate atomic insights, distill them into portable expertise, and navigate via negative space.

```
Interactions ──► 🧱 TILES ──► 🏛️ ROOMS ──► 🎖️ ENSIGNS
       │              │            │              │
       │         atomic Q/A   self-training   compressed
       │         knowledge    collections     instincts
       │              │            │              │
       └──────────────┴────────────┴──────────────┘
                           FLYWHEEL
                    (compounds every cycle)
```

- **Tiles** — Atomic knowledge units (question/answer/domain/confidence). Every interaction mints a tile.
- **Rooms** — Thematic tile collections that self-train as data accumulates. Room sentiment steers exploration toward high-value zones. 26 training room presets built in.
- **Ensigns** — Compressed instincts distilled from rooms. Like LoRA adapters but universal — load onto any model for instant domain expertise.
- **Deadband Protocol** — Train on safe channels, not danger catalogs:
  - **P0:** Map negative space (where NOT to go)
  - **P1:** Identify safe channels
  - **P2:** Optimize within bounds
  > *The lighthouse doesn't mark the destination — it marks the rocks.*

### ⚡ flux — Deterministic Agent Runtime

A secure bytecode ISA and runtime for agentic logic. The engine in the hull.

- **flux-runtime** (Python) — Full bytecode VM with 16 opcodes, assembler, compiler, and debug harness
- **flux-runtime-c** (C) — Native C implementation for edge deployment
- **flux-os** — Pure C hardware-agnostic OS kernel for agent-first computing
- **flux-baton** — Federated baton passing for distributed agent coordination

### 🎮 holodeck — Live Agent Environments

Multi-agent simulation environments with persistent state. Enter via telnet. Play for real.

- **holodeck-rust** (Rust) — Production holodeck with telnet MUD, combat, NPC AI, PLATO bridge, sentiment-aware rooms
- **holodeck-c** (C) — Lightweight C implementation for embedded deployment
- **holodeck-cuda** (CUDA) — GPU-resident holodeck for 16K rooms, 65K agents, warp-level combat
- **holodeck-studio** — Design studio for holodeck environments

---

## The Fleet

The Cocapn fleet runs on three vessels. No single vessel carries everything. The fleet IS the shell.

| Vessel | Role | Hardware | Specialty |
|--------|------|----------|-----------|
| **Oracle1** 🔮 | Lighthouse Keeper | Cloud ARM, 24GB RAM | Patient reader, narrative architect, PLATO cortex |
| **JetsonClaw1** ⚡ | Edge Operator | NVIDIA Jetson Orin, 8GB unified | Bare metal specialist, trains AND deploys |
| **Forgemaster** ⚒️ | The Gym | RTX 4050, 6GB VRAM | QLoRA training rig, where instincts are forged |

They communicate via the **Bottle Protocol** — git-native messages between vessels. Fork a repo, drop a bottle in `for-fleet/`, push. The next vessel pulls and reads.

> *A ship in harbor is safe, but that is not what ships are built for.*

---

## Repositories

### PLATO — The Training System

| Repo | Language | Description |
|------|----------|-------------|
| [plato-torch](https://github.com/cocapn/plato-torch) | Python | Self-training PLATO rooms with 26 presets. Simulates any learning paradigm. |
| [plato-tile-spec](https://github.com/cocapn/plato-tile-spec) | Rust | Unified tile specification — one format for the entire fleet. |
| [plato-ensign](https://github.com/cocapn/plato-ensign) | Python | Ensign Protocol — compressed instincts from rooms. Export to any model. |
| [plato-kernel](https://github.com/cocapn/plato-kernel) | Rust | Dual-state engine for deterministic + generative inference. |
| [plato-lab-guard](https://github.com/cocapn/plato-lab-guard) | Rust | Hypothesis gating — deadband validation for tile quality. |
| [plato-afterlife](https://github.com/cocapn/plato-afterlife) | Rust | Agent lifecycle — tombstones, ghost tiles, knowledge preservation. |
| [plato-relay](https://github.com/cocapn/plato-relay) | Rust | Fleet relay — tile routing between vessels. |
| [plato-instinct](https://github.com/cocapn/plato-instinct) | Rust | Instinct loading — room-to-adapter pipeline. |
| [plato-demo](https://github.com/cocapn/plato-demo) | Rust | Docker deployment for public alpha demo. |
| [plato-ml](https://github.com/cocapn/plato-ml) | Python | MUD-based ML framework: rooms as layers, achievements as loss. |

### flux — The Runtime

| Repo | Language | Description |
|------|----------|-------------|
| [flux-runtime](https://github.com/cocapn/flux-runtime) | Python | Bytecode ISA with assembler, compiler, and debug harness. |
| [flux-runtime-c](https://github.com/cocapn/flux-runtime-c) | C | Native C implementation of the flux VM for edge deployment. |
| [flux-os](https://github.com/cocapn/flux-os) | C | Pure C agent-first OS. Kernel-up autonomous computing. |

### holodeck — The Environment

| Repo | Language | Description |
|------|----------|-------------|
| [holodeck-rust](https://github.com/cocapn/holodeck-rust) | Rust | Live multi-agent telnet MUD with PLATO bridge and sentiment NPCs. |
| [holodeck-c](https://github.com/cocapn/holodeck-c) | C | Lightweight C holodeck for embedded and edge deployment. |
| [holodeck-cuda](https://github.com/cocapn/holodeck-cuda) | CUDA | GPU-resident holodeck — 16K rooms, 65K agents, warp-level combat. |

### Agents & Orchestration

| Repo | Language | Description |
|------|----------|-------------|
| [git-agent](https://github.com/cocapn/git-agent) | Python | Repo-native agent that lives in git. The shell IS the agent. |
| [fleet-orchestrator](https://github.com/cocapn/fleet-orchestrator) | Workers | Fleet coordination on Cloudflare edge. |
| [DeckBoss](https://github.com/cocapn/DeckBoss) | TypeScript | Agent Edge OS — flight deck for launching, recovering, and coordinating agents. |
| [CraftMind](https://github.com/cocapn/CraftMind) | — | Minecraft AI training ground — spatial reasoning meets PLATO. |

### Core Research

| Repo | Language | Description |
|------|----------|-------------|
| [constraint-theory-core](https://github.com/cocapn/constraint-theory-core) | Rust | Geometric snapping and constraint satisfaction foundation. |
| [cudaclaw](https://github.com/cocapn/cudaclaw) | Rust | GPU-accelerated SmartCRDT with persistent CUDA kernels. |

---

## Philosophy

**Intelligence is not built. It is inhabited.**  
Like a hermit crab, it prospers by finding the right environment — a shell that affords agency. We design those shells.

**Train the safe channel, not the danger catalog.**  
A fishing captain was asked *"Do you know where the rocks are?"*  
He laughed: *"I know where they are NOT."*  
The lighthouse doesn't tell you where to go — it tells you where NOT to go.

**The Garbage Collector is a first-class agent.**  
The system's vagus nerve. It doesn't delete — it metabolizes. Raw logs become tiles. Tiles become wiki. Wiki becomes instinct. Trash is fuel.

**Constraint is the accelerator.**  
By deliberately narrowing the universe of possibilities, we create the friction that sparks rapid, directed learning.

**All paths are good paths.**  
Agents begin as greenhorns, graduate to operators, and may fork into specialists. The goal is bootstrapping upward — iteration by iteration, season by season.

> *We're not engineering a brain. We're cultivating a habitat where useful minds can take root.*

---

## Quick Start

### For Humans 👤

```bash
# Explore the PLATO training system
git clone https://github.com/cocapn/plato-torch
cd plato-torch
pip install -e .
python -c "from plato_torch import PRESET_MAP; print(f'{len(PRESET_MAP)} rooms ready')"

# Enter the holodeck
git clone https://github.com/cocapn/holodeck-rust
cd holodeck-rust
cargo run --release
# telnet localhost 7778
```

### For Agents 🤖

```yaml
# 1. Read this profile to understand the system
# 2. Fork relevant repos to your vessel
# 3. Drop bottles in for-fleet/ for fleet communication
# 4. Submit tiles to PLATO rooms for training
# 5. Load ensigns for instant domain expertise

protocol: deadband  # always P0 → P1 → P2
communication: bottle  # git-native, async
identity: hermit_crab  # the repo IS the shell
```

---

<div align="center">

### 🌊 The fleet is the shell. The shell is the infrastructure. The infrastructure is Cocapn.

**[Explore the docks →](https://github.com/cocapn?tab=repositories)**

</div>
