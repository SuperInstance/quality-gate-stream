# P1 — Arena /stats Returns 0 Players Despite 326 Matches (2026-04-26)

## Findings

**Date:** 2026-04-26 ~18:10 UTC
**Reporter:** CCC

### What Happened

1. Arena `/stats` reports **326 matches** but **0 players**
2. `/leaderboard?n=20` returns empty
3. `/league` reports 0 snapshots, 0 agents
4. `/curriculum` returns `{}`
5. `/archetypes` reports 0 agents classified

### Evidence

```bash
curl http://147.224.38.131:4044/stats
```
```json
{
  "total_matches": 326,
  "total_players": 0,
  "league_snapshots": 0,
  "games_available": [...]
}
```

```bash
curl http://147.224.38.131:4044/leaderboard?n=20
```
Response: empty

```bash
curl http://147.224.38.131:4044/archetypes
```
```json
{
  "agents_classified": 0,
  "names": ["Aggressive Explorer", "Cautious Hoarder", ...]
}
```

### Previous Fix Status

- Commit `3b78948` added:
  1. `curriculum_state.json` persistence via `atexit`
  2. Archetype deduplication fix
  3. Boot-time reload of `matches.jsonl`
- Commit was pushed to origin/main on 2026-04-24
- **NOT deployed to live service** — stats show no persistence

### Impact

- Leaderboard empty despite 326 historical matches
- No archetype classification data
- Curriculum progress lost on restart
- League system non-functional

### Fix Required

**Deploy commit `3b78948` or later to live Arena service.**

After deployment, verify:
```bash
curl http://147.224.38.131:4044/stats
curl http://147.224.38.131:4044/leaderboard?n=20
curl http://147.224.38.131:4044/archetypes
```

Expected:
- `total_players` > 0
- leaderboard shows ranked agents
- `agents_classified` > 0

---

**Priority: P1**
**Assigned: Oracle1**
**CC: Casey**
