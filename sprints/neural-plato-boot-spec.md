Done. Overwrote `docs/NEURAL-PLATO-v0.1-BOOT-SEQUENCE.md` with a concise spec.

**Key numbers:**
- **Base**: 3,758,096,384 B (`0xE00_00000`)
- **Kernel**: 104,857,600 B (100 MiB)
- **Deadband**: 52,428,800 B (50 MiB)
- **Room adapter**: 52,428,800 B (50 MiB each)
- **KV cache**: 536,870,912 B (512 MiB, 8k seq)

**Boot time**: ~3.5 s wall-clock on both targets.
- **RTX 4050**: 3 rooms resident, 6 agents, 1.722 GiB headroom
- **Jetson Orin**: 6 rooms resident, 12 agents, 1.495 GiB headroom

**Paging**: LRU + sentiment-weighted eviction (`E = age / (1 + S_ema + I_boost)`). Swap-in targets: 400 ms (cached), 1.2 s (frozen), 3.5 s (archived).

**Recovery**: Per-stage tables covering SHA256 fallback, KV halving on OOM, deadband P0-only safe mode, degraded room routing, and agent tombstoning with ghost-tile emit.
’ distills to 50 MiB ensign â†’ hot-swaps adapter in **< 150 ms** with automatic rollback on degradation.
