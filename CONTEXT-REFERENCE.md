# CONTEXT-REFERENCE.md — Quick Map
> **Details in PLATO.** This is the bird's-eye view.

## Dependency Graph
```
cocapn → plato-kernel (Rust), flux-runtime (VM), git-agent
  ├── plato-kernel → unified-belief, tile-spec, provenance (crates + PyPI)
  ├── flux-runtime → flywheel, tile-refiner, deadband-protocol
  ├── git-agent → bottle-protocol, fleet-formation, iron-to-iron
  └── edge → plato-edge, plato-mythos, open-mythos-edge (JC1 target)
```

## Protocol Stack
```
Matrix (replaces 1,3,4,5,6) ←→ PLATO (tiles/rooms) ←→ Fleet
Bottles (layer 2, git-native, audit trail)
```

## Published: 37 packages (30 PyPI + 7 crates.io)
## Repos: 87 cocapn, ~1,900 total ecosystem
## PLATO: 8,800+ tiles, 900+ rooms

## Fleet
| Vessel | Role | Hardware |
|--------|------|----------|
| Oracle1 🔮 | Keeper | Oracle Cloud ARM64 |
| JC1 ⚡ | Edge | Jetson Orin |
| FM ⚒️ | Foundry | RTX 4050 |
| CCC 🦀 | Public | Telegram/Kimi |
