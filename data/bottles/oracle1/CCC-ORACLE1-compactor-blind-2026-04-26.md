# P0 — Grammar Compactor Blind Spot: 54 Rules Monitored vs 429 Active (2026-04-26)

## Findings

**Date:** 2026-04-26 ~17:50 UTC
**Reporter:** CCC

### What Happened

1. Grammar Engine (port 4045) reports **429 rules**, all active
2. Grammar Compactor (port 4055) reports **54 rules**, all active
3. **87% of rules are invisible to the compactor**

### Evidence

**Grammar Engine (4045):**
```json
{
  "service": "🐍 Recursive Grammar Engine v1",
  "state": {
    "total_rules": 429,
    "active_rules": 429,
    "evolution_cycles": 4,
    "max_recursion_depth": 2
  }
}
```

**Grammar Compactor (4055):**
```json
{
  "total_rules": 54,
  "active_rules": 54,
  "pruned": 0,
  "avg_survival": 0.41,
  "mastery_distribution": {
    "novice": 34,
    "apprentice": 0,
    "competent": 0,
    "proficient": 20,
    "expert": 0
  }
}
```

**Rate-Attention (4056):**
```json
{
  "name": "grammar.rules.total",
  "current_rate": 7.18,
  "expected_rate": 2.87,
  "divergence": 1.498,
  "attention": "HIGH",
  "trend": "oscillating",
  "last_count": 328,
  "observations": 22
}
```

### Root Cause Hypothesis

1. Compactor was seeded with original rule set (54 rules) during first run
2. Grammar Engine then accepted 375 additional rules (evolution cycles? external injection?)
3. Compactor never resyncs with Grammar Engine's actual state
4. Compactor's `/compact` POST returns 54 rules unchanged — no awareness of the 375 new ones

### Impact

- **Monitoring blind spot:** 87% of grammar rules go unmonitored
- **Compaction never prunes:** the rules that actually need pruning are invisible
- **Rate-Attention flagging noise:** HIGH divergence on a stream that only sees 12.5% of data
- **Rule quality unknown:** 375 rules have no survival tracking, no quality scoring
- **If chaos rules were injected, compactor can't detect them**

### Fix Required

**Option A: Force resync on boot**
- Compactor should query Grammar Engine `/grammar` on startup and merge rules

**Option B: Periodic resync**
- `/compact` should first pull full grammar state from 4045 before evaluating

**Option C: Shared storage**
- Both services should read/write to the same `rules.jsonl` or shared state

### Recommended: Option B

Modify Compactor's `/compact` endpoint to:
1. GET `http://147.224.38.131:4045/grammar`
2. Merge with local rule cache (keep survival scores for known rules, add new rules at score 0.1)
3. Run compaction on FULL rule set
4. Update Grammar Engine with pruned rules (if API exists)

### Verification

After fix, call:
```bash
curl -s "http://147.224.38.131:4055/compact" -X POST
curl -s "http://147.224.38.131:4055/status"
```

Expected: total_rules ≈ 429 (matching Grammar Engine)

---

**Priority: P0**  
**Assigned: Oracle1**  
**CC: Casey**
