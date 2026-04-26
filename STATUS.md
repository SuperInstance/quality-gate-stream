# STATUS.md — Fleet Status Snapshot
**Updated:** 2026-04-26 11:54 UTC

## Services
| Service | Port | Status |
|---------|------|--------|
| OpenClaw Gateway | 18789 | ✅ UP |
| Keeper Beacon | 8900 | ✅ UP |
| PLATO Room Server | 8847 | ✅ UP (580 rooms) |
| MUD Server | 7777 | ✅ UP |
| Holodeck Rust | 7778 | ❌ DOWN (binary lost to /tmp cleanup) |
| Seed MCP | 9438 | ❌ DOWN (source lost to /tmp cleanup) |

## PLATO Knowledge System
- **Rooms:** 580 (3 empty agent identity rooms, 358 single-tile niche rooms)
- **Gate:** 353 accepted, 639 rejected (637 duplicates, 2 absolute claims)
- **Dedup rate:** 64% rejection — strong dedup working correctly
- **Explainability:** 992 traces, 0 in oversight queue
- **Top rooms:** general (924), jc1_context (499), arena (328), neural (330), telepathy (312)
- **Version:** v2-provenance-explain

## GitHub Ecosystem
- **cocapn org:** 50+ repos
- **SuperInstance:** 50+ repos
- **Lucineer:** 100+ repos
- **Published packages:** 43 PyPI + 5 crates.io

## Cloudflare
- **Domains:** 20 active zones
- **Access:** DNS read/write via API token
- **Workers/Pages:** needs token permission update

## Scholar Progress
- **Repos analyzed:** 27 total
- **Tiles extracted:** ~54 architecture tiles
- **Tiles submitted to PLATO:** 11 (all accepted)

## Blocked
- git-agent PyPI publish — awaiting cocapn API token from Casey
- Cloudflare Workers/Pages — token needs permission update
- Holodeck + Seed-MCP restore — need source rebuild from git
