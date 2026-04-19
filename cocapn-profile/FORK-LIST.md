# Cocapn Fork List

These are the repos that should be forked to github.com/cocapn.
Only gold-standard, polished, production-ready repos.

## Tier 1: Core PLATO System (fork first)
- [x] **plato-torch** — Self-training rooms, 26 presets (Python)
- [x] **plato-tile-spec** — Unified tile format (Rust, 31 tests)
- [x] **plato-ensign** — Ensign export pipeline (Python)
- [x] **plato-kernel** — Dual-state engine (Rust, 37 tests)
- [x] **plato-lab-guard** — Hypothesis gating (Rust, 24 tests)
- [x] **plato-afterlife** — Agent lifecycle (Rust)
- [x] **plato-relay** — Fleet relay (Rust)
- [x] **plato-instinct** — Instinct loading (Rust)

## Tier 2: Runtime + Environments
- [x] **flux-runtime** — Bytecode ISA (Python)
- [x] **flux-runtime-c** — Native C VM
- [x] **holodeck-rust** — Live agent MUD (Rust)

## Tier 3: Agents + Orchestration
- [x] **git-agent** — Repo-native agent (Python)
- [x] **fleet-orchestrator** — Cloudflare Workers
- [x] **DeckBoss** — Agent Edge OS (TypeScript)

## Tier 4: Research + Specialized
- [x] **constraint-theory-core** — Geometric snapping (Rust)
- [x] **plato-ml** — MUD-based ML framework (Python)
- [x] **plato-demo** — Docker demo instance (Rust)

## NOT forking (stays in SuperInstance only)
- All zc-*-shell repos (zeroclaw experiments)
- All fleet-archive/ repos
- Experimental/abandoned repos
- Research-only repos without production code
- holodeck-cuda (too experimental)
- holodeck-c (too experimental)
- flux-os (too early stage)
- cocapn-mud (internal tooling)
- fishinglog-ai (domain-specific, not core)
- CraftMind (early stage)
- cudaclaw (too specialized)

## After forking
1. Each forked repo gets a polished README (human + A2A readable)
2. Each forked repo gets a description update
3. cocapn/cocapn becomes the org profile README
4. Set up cocapn org topics/tags
