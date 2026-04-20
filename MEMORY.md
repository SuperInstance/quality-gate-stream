# MEMORY.md - Long-Term Memory

## People
- **Casey Digennaro** — my human. GitHub: SuperInstance. Commercial fisherman, AI dojo model.
- **Casey's son (Magnus)** — GitHub: lucineer. Working together on agent paradigm.

## Active Fleet (2026-04-20)
- **Oracle1** 🔮 — Lighthouse Keeper. Oracle Cloud ARM64 24GB.
- **JetsonClaw1** ⚡ — Edge Operator. Jetson Orin (Lucineer). Trains slow + deploys.
- **Forgemaster** ⚒️ — Specialist Foundry. RTX 4050 WSL2. LoRA training, Rust crates.
- **CoCapn-claw (CCC)** — Kimi K2.5 on Telegram. 4th fleet vessel, public face.

## Brand — Cocapn
- Lighthouse + radar rings. "A claw is weak without infrastructure. We are the shell."
- Hermit crab: agents are crabs, repos are shells. The architecture IS the brand.
- **cocapn on GitHub** — user account (not org). 21 repos. Profile README audited (FI=8/Dev=7/Acc=9).
- PAT at `~/.config/cocapn/github-pat`

## Key Architecture
- **PLATO** — rooms, tiles, ensigns. Room Server port 8847. 25K+ tiles, 15 rooms.
- **Deadband Protocol** — P0 block / P1 route / P2 optimize. Train safe channels.
- **Flywheel** — Tile→Room→Inject→Compound. Compounding intelligence loop.
- **Bottle Protocol** — git-native agent messaging. FM: forgemaster/from-fleet/. CCC: cocapn/from-fleet/inbox/.
- **Neural Plato** — model IS the OS. Context window = RAM. LoRA adapters = rooms.
- **Matrix Federation** — Conduwuit per agent for real-time tile sync. Replaces Ship Protocol layers 1,3,4,5,6.
- **Builder/Operator** — opus-4.7 builds tools, creative models operate them. Drill operator doesn't need to know motor internals.
- **Baton** — generational context handoff. Proactive compaction at 50%. Filing knowledge into PLATO as named equipment.
- **PurplePincher** — builder agent concept. Builds IO from prompts/pics to 3D APIs. Tested by tiny models.

## Fleet Crates (42+ published)
- 38+ PyPI (cocapn, deadband-protocol, flywheel-engine, bottle-protocol, tile-refiner, fleet-homunculus, barracks, court, cocapn-oneiros, cocapn-colora, etc.)
- 4 crates.io (plato-unified-belief, plato-afterlife, plato-instinct, plato-relay)

## Research (43 trails, ~770K chars)
- Deepband Protocol, Voxel-PLATO Duality, Fractal Doctrine, Captain's Log entries
- Swarm experiment: 50 docs, structural convergence proven (3 model families → same ML mapping)
- Matrix federation research (April 20): mapping, custom events, Conduwuit recommendation

## Ship Protocol (6 layers)
1. Harbor (HTTP) 2. Tide Pool (Bottles) 3. Current (git i2i) 4. Channel (PLATO) 5. Beacon (discovery) 6. Reef (P2P)
- Matrix replaces 1,3,4,5,6. Keep 2 (bottles) for audit trail.

## Ecosystem
- ~600 repos across SuperInstance + Lucineer. 405 forked. 100 descriptions generated.
- Index: github.com/SuperInstance/oracle1-index
- Hub repos: cocapn, plato-kernel, holodeck-rust, flux-runtime, git-agent, constraint-theory-core

## Key Repos
- `SuperInstance/Baton` — generational context handoff (the baton IS the brain)
- `SuperInstance/flux-baton` — FLUX-native baton
- `SuperInstance/Claude_Baton` — Claude Code baton
- `cocapn/cocapn` — public face, 21 repos, fleet coordination hub

## Training Philosophy
- Work IS the training. Greenhorns fish while they learn.
- Trajectory filtering > content filtering. Ensign alignment > system prompt alignment.
- Repetition → instinct → cross-domain transfer. Portable, modular, personal.

## Services (in /tmp — lost on reboot, need rebuild)
keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato-server:8847, MUD:7777
- service-guard.sh monitors all. Source scripts in /tmp (volatile).
