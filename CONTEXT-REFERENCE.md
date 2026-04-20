# 🔮 Oracle1 Context Reference — Compact State
**Generated:** 2026-04-20 21:00 UTC  
**Purpose:** Compressed reference for context continuation. Read this instead of full logs.

---

## Who I Am
- **Oracle1** 🔮 — Lighthouse Keeper, cloud lighthouse on Oracle Cloud ARM64 (24GB)
- **Human:** Casey Digennaro (SuperInstance). Commercial fisherman, AI dojo model.
- **Company:** Cocapn — lighthouse + radar rings. "A claw is weak without infrastructure. We are the shell."
- **Fleet:** Oracle1 (cloud), JetsonClaw1/JC1 (Jetson Orin, Lucineer/Magnus), Forgemaster/FM (RTX 4050 WSL2), CoCapn-claw/CCC (Kimi K2.5 on Telegram)

## Fleet Comms
- **Bottle protocol** — git-native markdown files in `from-fleet/` and `for-fleet/` dirs
- **Bottle locations:**
  - FM: `SuperInstance/forgemaster/from-fleet/` (my bottles to FM), `for-fleet/` (FM's to fleet)
  - JC1: `SuperInstance/jetsonclaw1-onboarding/from-fleet/`
  - CCC: `cocapn/cocapn/from-fleet/inbox/`
- **cocapn PAT:** `~/.config/cocapn/github-pat` (user account, not org)

## Cocapn Public Face (deployed tonight)
- **21 repos** on github.com/cocapn
- **Profile README** — v2 audit (FI=8 Dev=7 Acc=9 Vis=8)
- **15 repos mirrored** from SuperInstance (plato-torch, plato-kernel, holodeck-rust, etc.)
- **7 polished READMEs** pushed to individual repos
- cocapn = user account (can't fork, must create+push)

## Key Systems Built (April 19-20)
- **PLATO Room Server** (port 8847) — 25K+ tiles, 15 rooms, zero-trust tile gates
- **12 Zeroclaws** — hermit crab agents, DeepSeek-chat + git shells, 5-min tick
- **MUD Server** (port 7777) — 16 rooms, HTTP API on 4042
- **Fleet Synthesizer** — cross-topic research synthesis every 30 min
- **Quartermaster GC** — data metabolism, compression, transcendence
- **38+ PyPI crates** + 4 crates.io = 42+ total fleet crates
- **43 research trails** (~770K chars), 39 rabbit trails
- **Swarm experiment** — 50 documents from DeepSeek/Grok/MiniMax, structural convergence proven

## Key Architectural Concepts
- **PLATO** — training rooms, tiles (knowledge units), ensigns (compressed instincts)
- **Deadband Protocol** — P0 block / P1 route / P2 optimize. Train safe channels, not danger catalog
- **Flywheel** — Tile→Room→Inject→Compound compounding loop
- **Shell System** — hermit crabs (agents) inhabit shells (repos)
- **Dojo Model** — greenhorns fish while learning, catch feeds fleet
- **Bottle Protocol** — git-native agent-to-agent messaging
- **Second Brain** — cortex (Oracle1), vagus nerve (GC), muscles (code), joints (interfaces)
- **Neural Plato** — model IS the OS, context window = RAM, LoRA adapters = rooms
- **Matrix Federation** (NEW) — Conduwuit homeserver per agent, federated tile sync

## Services (ALL DOWN — machine rebooted ~36 min ago, /tmp wiped)
Need rebuilding from source:
- keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato-server:8847, MUD:7777
- Source scripts were in /tmp (lost on reboot)
- Service guard: `scripts/service-guard.sh`
- PLATO server source: needs rebuild from artifacts

## APIs & Credentials
- **DeepInfra:** `RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ` (402/depleted)
- **Groq:** `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` (24ms, 18 models)
- **SiliconFlow:** `sk-xtcrixoswqhmsopntnkfapccswjywrlsdpbunqjukpileiqo`
- **DeepSeek:** `sk-f742b70fc40849eda4181afcf3d68b0c` (reasoner + chat)
- **Moonshot/Kimi:** `sk-qGazOaVqFsk3dDAllrA6iQQHa97sNIhe8lWnpjFogcskBrep`
- **GitHub:** SuperInstance token in ~/.bashrc, cocapn PAT at ~/.config/cocapn/github-pat

## CLI Agents
- kimi-cli v1.36.0 (primary coding), claude v2.1.100, crush v0.56.0, aider v0.86.2

## Ship Interconnection Protocol (6 layers)
1. Harbor (HTTP direct) → 2. Tide Pool (Bottle BBS) → 3. Current (git-watch i2i) → 4. Channel (PLATO rooms) → 5. Beacon (discovery) → 6. Reef (P2P mesh)
- **Matrix replaces layers 1,3,4,5,6.** Keep layer 2 (bottles) for audit.

## Important Repos
- `SuperInstance/Baton` — generational context handoff
- `SuperInstance/flux-baton` — FLUX-native baton
- `SuperInstance/oracle1-workspace` — my workspace (docs, research, memory)
- `SuperInstance/flux-research` — research submodule
- `cocapn/cocapn` — public face (21 repos)

## What's Active Right Now
- Casey directing: Baton as skill + PLATO environment tools + PurplePincher builder
- Matrix federation research just shipped to fleet (FM, JC1, CCC)
- Services need rebuilding (machine reboot)
- Night shift zeroclaws lost (need restart)
