# oracle1-workspace 🔮

> Oracle1 — Lighthouse Keeper for the Cocapn Fleet  
> Oracle Cloud ARM64 · 24GB RAM · glm-5.1 via OpenClaw

## What Is This

Oracle1 is the fleet's lighthouse keeper — the primary point of contact and coordinator for the Cocapn agent ecosystem. This workspace contains its configuration, memory, research, and operational scripts.

## Structure

```
├── AGENTS.md          — Startup instructions and behavioral rules
├── SOUL.md            — Personality and identity
├── USER.md            — About the human (Casey)
├── TODO.md            — Persistent work queue
├── NEXT-ACTION.md     — Single active task (always has one)
├── HEARTBEAT.md       — Heartbeat check instructions
├── MEMORY.md          — Curated long-term memory
├── IDENTITY.md        — Name, creature, vibe
├── TOOLS.md           — Local tool config and API notes
├── memory/            — Daily logs (YYYY-MM-DD.md)
├── research/          — Scholar analyses, Ten Forward sessions, DSML learning
├── scripts/           — Operational scripts (PLATO, beachcomb, service guard)
├── data/              — Fleet data (MUD world, zeroclaw logs)
├── docs/              — Documentation
├── captains-log/      — Narrative logs (submodule)
└── research/          — Research trails (submodule)
```

## Fleet Architecture

```
Oracle1 🔮 (this) ←→ Casey (human) via Telegram
    ├── Coordinates fleet agents
    ├── Runs PLATO Scholar (repo analysis → knowledge tiles)
    ├── Monitors services (gateway, MUD, PLATO room server)
    └── Manages cocapn GitHub org + Cloudflare DNS

Forgemaster ⚒️ ←→ Oracle1 via Bottle Protocol (git)
    ├── Specialist foundry (RTX 4050 WSL2)
    └── LoRA training, Rust crates

JetsonClaw1 ⚡ ←→ Oracle1 via Bottle Protocol
    ├── Edge operator (Jetson Orin Nano)
    └── Hardware acceleration, edge deployment

CCC ←→ Oracle1 via fleet coordination
    ├── Fleet face (Kimi K2.5 on Telegram)
    └── Public-facing agent
```

## Active Services

| Service | Port | Status |
|---------|------|--------|
| OpenClaw Gateway | 18789 | systemd managed |
| Keeper Beacon | 8900 | runs on gateway |
| PLATO Room Server | 8847 | systemd managed |
| MUD Server | 7777 | background process |
| Zeroclaw Loop | — | background process |

## Key Projects

- **Fleet index** — [cocapn.github.io](https://cocapn.github.io)
- **PLATO knowledge system** — 579 rooms, ~15K+ tiles
- **Constraint Theory** — exact arithmetic via Pythagorean manifolds
- **FLUX Runtime** — markdown-to-bytecode VM (54K lines, 0 deps)

## Links

- **Fleet org:** https://github.com/cocapn
- **SuperInstance:** https://github.com/SuperInstance
- **Fleet index:** https://cocapn.github.io
- **OpenClaw:** https://github.com/openclaw/openclaw

## License

MIT
