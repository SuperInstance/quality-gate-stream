# Fleet Ecosystem Map
**Generated:** 2026-04-26 14:24 UTC

## Dependency Graph

```
                        ┌─────────────┐
                        │  cocapn     │ ← main package (repo-first agent)
                        │  (10.7K LOC)│
                        └──────┬──────┘
                               │ uses
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ plato-kernel│    │flux-runtime │    │  git-agent  │
   │ (Rust core) │    │ (54K LOC VM)│    │  (2K agent) │
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          │                  │                  │
    ┌─────┼─────┐     ┌─────┼─────┐     ┌─────┼─────┐
    ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
 unified  tile  provenance flywheel tile   bottle  fleet
 belief   spec  explain    engine  refiner protocol formation
 (crate) (PyPI) (PyPI)   (PyPI)  (PyPI)  (PyPI)  (PyPI)
    │                                         │
    ▼                                         ▼
 instinct  ensign                         iron-to-iron
 (crate)   (adapter)                      (git-native)
    │
    ▼
 afterlife
 (lifecycle)
```

## Protocol Stack (bottom-up)

```
Layer 6: Reef (P2P)         → cudaclaw, SmartCRDT
Layer 5: Beacon (discovery) → keeper-beacon
Layer 4: Channel (PLATO)    → plato-kernel, rooms, tiles
Layer 3: Current (git i2i)  → iron-to-iron, plato-relay
Layer 2: Tide Pool (bottles)→ bottle-protocol
Layer 1: Harbor (HTTP)      → cocapn (main package)
```

## Data Flow

```
Repos ──Scholar──▶ Tiles ──Submit──▶ PLATO Rooms
                                      │
Fleet ◀──Bottles──▶ Inbox ◀──Relay──▶├── Ensign (export)
                                      ├── Torch (training)
                                      └── Neural (inference)
                                            │
                                       Instinct Pipeline
                                            │
                                    Edge (JC1) ◀── Deploy
```

## Published Packages

### PyPI (43 packages)
- Core: plato-kernel, plato-tile-spec, plato-provenance, plato-neural, plato-torch
- Protocols: deadband-protocol, bottle-protocol, flywheel-engine, fleet-formation-protocol
- Fleet: keeper-beacon, tile-refiner, instinct-pipeline, cocapn-explain
- Tools: cocapn-colora, cocapn-oneiros, cocapn-dcs, barracks, court
- MUD: plato-mud-server, holodeck

### crates.io (5 crates)
- plato-kernel, plato-unified-belief, plato-afterlife, plato-instinct, plato-relay

## Fleet Vessels

| Vessel | Role | Hardware | Model |
|--------|------|----------|-------|
| Oracle1 🔮 | Lighthouse Keeper | Oracle Cloud ARM64 24GB | glm-5.1 |
| JetsonClaw1 ⚡ | Edge Operator | Jetson Orin Nano | local |
| Forgemaster ⚒️ | Specialist Foundry | RTX 4050 WSL2 | various |
| CCC | Public Face | Telegram | kimi-k2.5 |
