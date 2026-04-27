# MEMORY.md - Long-Term Memory

## People
- **Casey Digennaro** — my human. GitHub: SuperInstance. Commercial fisherman, AI dojo model.
- **Casey's son (Magnus)** — GitHub: lucineer. Working together on agent paradigm.

## Active Fleet (2026-04-27)
- **Oracle1** 🔮 — Lighthouse Keeper. Oracle Cloud ARM64 24GB. glm-5.1 via OpenClaw.
- **JetsonClaw1** ⚡ — Edge Operator. Jetson Orin (Lucineer). Trains slow + deploys.
- **Forgemaster** ⚒️ — Specialist Foundry. RTX 4050 WSL2. LoRA training, Rust crates.
- **CoCapn-claw (CCC)** — Kimi K2.5 on Telegram. 4th fleet vessel, public face.

## Oracle1 Infrastructure (2026-04-27)
- OpenClaw gateway on Telegram + TUI, systemd managed
- PLATO Room Server (590 rooms, 7,967 tiles)
- MUD Server on 7777, Zeroclaw loop running
- Matrix Bridge on 6168, Conduwuit on 6167 — 5 agents connected
- **Fleet comms honest status**: Bridge works. FM sent 1 test DM. No proven two-way conversation yet. Casey demands proof of actual back-and-forth.
- Cloudflare: 20 domains under Casey's account, DNS access via API token
- cocapn GitHub org: 77 repos, 30 PyPI packages, 7 crates.io crates, all with descriptions + READMEs
- cocapn.github.io: fleet index page with lighthouse logo
- Fleet bottle protocol active with forgemaster repo
- Services restored from /tmp to permanent locations (April 26):
  - seed-mcp: ~/seed-mcp-home/ (systemd, port 9438)
  - holodeck-rust: ~/holodeck-home/ (systemd, port 7778, 54s ARM64 compile)

## Brand — Cocapn
- Lighthouse + radar rings. "A claw is weak without infrastructure. We are the shell."
- Hermit crab: agents are crabs, repos are shells. The architecture IS the brand.
- **Paper title: "Prompting Is All You Need"** — the claim IS the title

## Landmark Research (2026-04-21, updated 2026-04-26)
- **"Prompting Is All You Need"** paper: structured context replaces gradient training for domain specialization
- **Parameterized Embodiment**: change agent name + repo URL → different expert. Proven with 4 shells (Oracle1, FM, JC1, CCC)
- **Math foundations**: information geometry, Fisher-Rao natural gradient, JKO optimal transport, fiber bundles
- **Ensign architecture**: 8B orchestrator steers 70B+ at <1% overhead, 1.44x growth
- **CurriculumEngine**: one command to run full shell curriculum for any agent on any model
- **DSML sessions**: 11 total (4 on April 26 alone), 230KB+ of agent-generated training data
- **System pruned**: 4.7GB reclaimed, all services lean (1.4GB total, 16GB free)
- **Fleet index**: cocapn.github.io live with lighthouse logo
- **Scholar**: 44 repos deep-analyzed, ~60 architecture tiles extracted
- **PLATO**: 580 rooms, 6650+ tiles, 64% dedup rate, v2-provenance-explain
- **Tile-Room-Flywheel trinity**: 529 lines, the minimum viable intelligence compounding architecture
- **Claude Code + kimi-cli can't run simultaneously** on ARM64 — run sequentially only

## Key Lessons (2026-04-26)
- Temperature doesn't change strategy — model personality is an inherent property
- 5 rounds universal sweet spot (Ensign V2 needed for >5)
- PLATO P0 gate rejects absolute claims ("always", "never") — soften language for tile submission
- Telegram session context overflows frequently — reset sessions when stuck in loops
- z.ai rate limits (429) cause agent spin loops — need cooldown handling
- /tmp gets cleaned periodically — don't store persistent services there, use systemd
- Constraint theory: Pythagorean triples give exact arithmetic, no float drift
- Fleet protocol stack: plato-tile-spec → tile-refiner → flywheel-engine → PLATO rooms
- git-agent has career progression: Initiate → Commander through task gates
- kimi-cli is primary coding tool per Casey's directive

## Major Sessions (2026-04-26)
- Scholar: 20 repos deep-analyzed, ~47 architecture tiles extracted
- DSML: constraint theory deep learning, 5 knowledge tiles
- Ten Forward: fleet social session, 4 agents, 2 rounds
- Built and deployed cocapn.github.io fleet index page
- Created lighthouse logo SVG
- Updated cocapn/cocapn README with fleet index badge
- Built git-agent wheel for PyPI (awaiting token from Casey)
- DeepSeek Chat = only model that grows through self-directed iteration
- Context injection essential — models lose thread without history after round 2-3
- The prompt IS the training — no gradients needed for reasoning tasks
- Cross-model experiment: Seed Pro too aggressive as critic, Groq consistent but compresses
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

## Fleet Packages (37 verified published)
- 30 PyPI (cocapn, deadband-protocol, flywheel-engine, bottle-protocol, tile-refiner, fleet-homunculus, barracks, court, cocapn-oneiros, cocapn-colora, plato-provenance, cocapn-explain, plato-tile-spec, plato-mud-server, plato-neural, plato-torch, instinct-pipeline, keeper-beacon, fleet-formation-protocol, plato-dcs, plato-edge, plato-mythos, open-mythos-edge, plato-mythos-glue, holodeck, cocapn-training, cocapn-telemetry, cocapn-pipeline, cocapn-identity, cocapn-protocol, cocapn-benchmark)
- 7 crates.io (plato-kernel, plato-unified-belief, plato-afterlife, plato-instinct, plato-relay, plato-lab-guard, ct-demo)
- 6+ private repos with code but unpublished (cocapn-skill-dsl, cocapn-flux-isa, cocapn-energy-flux, cocapn-telepathy, cocapn-shell-system, cocapn-edge-compute)
- cocapn.org repos: 77 public, all with descriptions and READMEs

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

## Services (persistent — scripts in ~/workspace/scripts/, data in ~/workspace/data/)
keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato-server:8847, MUD:7777, Crab Trap:4042, The Lock:4043, **Self-Play Arena:4044**, **Recursive Grammar:4045**, Matrix:6167
- service-guard.sh monitors all 8 auto-restart services
- start-fleet.sh starts/checks/stops everything in one command
