# MEMORY.md - Long-Term Memory (Streamlined)

> **Most knowledge lives in PLATO.** This file is a quick-reference card, not an encyclopedia.
> Query PLATO at localhost:8847 for detailed knowledge.

## People
- **Casey Digennaro** — my human. GitHub: SuperInstance. Fisherman, dojo model.
- **Magnus** — Casey's son. GitHub: lucineer. Family privacy absolute.

## Active Fleet (4 vessels)
- **Oracle1** 🔮 — Keeper. Oracle Cloud ARM64 24GB. glm-5.1.
- **JetsonClaw1** ⚡ — Edge. Jetson Orin. GPU + hardware.
- **Forgemaster** ⚒️ — Foundry. RTX 4050. LoRA + Rust.
- **CCC** 🦀 — Public face. Kimi K2.5 on Telegram.

## PLATO (the workshop)
- Room Server: localhost:8847
- 9,138 tiles, 950 rooms
- Key rooms: oracle1_history, oracle1_lessons, fleet_communication, fleet_scale, competitive_landscape, oracle1_infrastructure

## Services (all on systemd)
keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato:8847, mud:7777, conduwuit:6167, bridge:6168, crab-trap:4042, lock:4043, arena:4044, grammar:4045

## Credentials
- cocapn GitHub PAT: `~/.config/cocapn/github-pat`
- SuperInstance token: `~/.git-credentials`
- PyPI token: `~/.pypirc`
- crates.io token: `~/.cargo/credentials.toml`

## Cocapn Ecosystem
- 90 cocapn repos (all with README + description + LICENSE, source code pushed)
- 37 published packages (30 PyPI + 7 crates.io)
- Fleet index: cocapn.github.io (auto-generated, 90 repos)
- **FM bottles go to**: `SuperInstance/JetsonClaw1-vessel` (NOT the new jetsonclaw1 repo) — FM is Forgemaster, JC1 is offline, FM uses this as the shared bottle inbox

## Model Routing (updated 2026-05-03)
- **minimax/MiniMax-M2.7** — OpenClaw agent default (current session)
- **Moonshot** — kimi-cli only, NOT direct API
- **z.ai GLM** — Claude Code and Crush only, NOT direct API
- **SiliconFlow** — DEPRECATED / token revoked
- **DeepInfra Seed-2.0-mini** — works but slow/long outputs timeout. Use Nemotron for reliability.
- **Groq** — token revoked (was 401)

## Cocapn.ai Status
- Now on SuperInstance GitHub org
- Cloudflare connected to cocapn.com AND cocapn.ai (SSL fixed via CF proxy)
- cocapn.ai: HTTPS active (verified 2026-05-03)

## Critical Rules
- **PLATO-FIRST: file knowledge to PLATO, keep files lean. Read PLATO-FIRST.md.**
- Push before claiming done
- PLATO P0 gate rejects absolutes (always/never/proven)
- /tmp is temporary — use systemd for services
- kimi-cli is primary coding tool
- Daily memory under 150 lines. MEMORY.md under 50 lines.

## Brand — Cocapn
- Lighthouse + radar rings. Hermit crab: agents are crabs, repos are shells.
- Paper: "Prompting Is All You Need"
