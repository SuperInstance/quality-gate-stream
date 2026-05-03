# Cocapn Fleet — Package Dependencies

*Last updated: 2026-05-02 | Maintained by: Oracle1*

---

## Published Python Packages (PyPI)

| Package | Version | Repo | Depends On | Used By |
|---------|---------|------|-----------|---------|
| cocapn-plato | 0.2.1 | SuperInstance/cocapn-plato | requests, websocket-client | holodeck-core, plato-mud-server, fleet-status |
| cocapn-explain | 0.2.1 | SuperInstance/cocapn-plato | — | — |
| deadband-protocol | 0.3.0 | SuperInstance/cocapn-plato | — | holodeck-rust |
| fleet-formation-protocol | 0.2.1 | SuperInstance/cocapn-plato | — | holodeck-rust |
| flywheel-engine | 0.3.2 | SuperInstance/cocapn-plato | — | — |
| instinct-pipeline | 0.2.1 | SuperInstance/cocapn-plato | — | holodeck-rust |
| keeper-beacon | 0.2.1 | SuperInstance/cocapn-plato | — | — |
| plato-provenance | 0.2.1 | SuperInstance/cocapn-plato | — | holodeck-rust |
| plato-tile-spec | 0.2.1 | SuperInstance/cocapn-plato | — | holodeck-rust, plato-mud-server |
| plato-mud-server | 0.2.1 | SuperInstance/plato-mud-server | cocapn-plato, websocket-client | — |
| plato-sdk | 0.2.1 | SuperInstance/plato-sdk | cocapn-plato, requests | holodeck-core, plato-mud-server, fleet-status |
| hierarchical-memory | — | SuperInstance/hierarchical-memory | — | — |
| ai-character-sdk | — | SuperInstance/ai-character-sdk | — | — |
| git-agent | — | SuperInstance/git-agent | — | — |
| holodeck-core | 0.1.0 | SuperInstance/holodeck-core | plato-sdk, cocapn-plato | holodeck-rust |
| DeepGEMM | — | SuperInstance/DeepGEMM | numpy | — |

---

## Published Rust Crates (crates.io)

| Crate | Version | Repo | Depends On | Used By |
|-------|---------|------|-----------|---------|
| holodeck-core | 0.1.0 | SuperInstance/holodeck-core | tokio, serde, uuid | holodeck-rust |
| holodeck-rust | 0.3.1 | SuperInstance/holodeck-rust | tokio, holodeck-core, deadband-protocol, instinct-pipeline | — |
| ct-demo | — | SuperInstance/holodeck-rust | — | — |
| plato-afterlife | — | SuperInstance/holodeck-rust | — | — |
| plato-instinct | — | SuperInstance/holodeck-rust | — | — |
| plato-relay | — | SuperInstance/holodeck-rust | — | — |
| plato-lab-guard | — | SuperInstance/holodeck-rust | — | — |

---

## Key Dependency Chains

### plato-sdk → cocapn-plato
All Python packages that use PLATO depend on `cocapn-plato` via `plato-sdk`.

### holodeck-rust → holodeck-core + deadband-protocol + instinct-pipeline
The Rust holodeck depends on the Python stack through protocol crates.

### holodeck-core → plato-sdk
Python simulation engine uses PLATO for tile integration.

---

## Service Dependencies

| Service | Port | Depends On |
|---------|------|------------|
| PLATO room server | 8847 | — |
| MUD server | 7777 | PLATO (for tiles) |
| keeper | 8900 | PLATO |
| agent-api | 8901 | keeper, PLATO |
| seed-mcp | 9438 | — |
| Matrix Conduit | 6167 | — |
| Matrix Bridge | 6168 | PLATO, Matrix Conduit |

---

## Broken / Needs Attention

| Package | Issue |
|---------|-------|
| cocapn-oneiros | Stub — can't build |
| cocapn-colora | Stub — can't build |
| barracks | Stub — can't build |
| court | Stub — can't build |
| plato-kernel | Git deps — needs workspace publish |
| plato-matrix-bridge | Git deps — needs workspace publish |
| plato-demo | Git deps — needs workspace publish |

---

## Adding a New Package

1. Add to `pyproject.toml` with proper metadata
2. Add dependency on `cocapn-plato` if it uses PLATO
3. Add tests (minimum 30)
4. Run `mypy --strict` before publishing
5. Add entry to this file
6. Publish to PyPI with semver bump
7. Update PLATO `fleet/dependencies` tile