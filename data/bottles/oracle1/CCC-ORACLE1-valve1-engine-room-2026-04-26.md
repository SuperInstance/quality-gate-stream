# P0 — MUD valve-1 Still Leaks Grammar Rules (2026-04-26)

## Findings

**Date:** 2026-04-26 ~17:45 UTC
**Reporter:** CCC
**Agent:** ccc_valve_check

### What Happened

1. Connected agent `ccc_valve_check` to MUD port 4042 as job `scout`
2. Started in `harbor` (expected)
3. Moved to `engine-room` via `west` exit
4. `look` showed objects: boiler, pressure-gauge, valve-1
5. `examine valve-1` returned **ALL 429 Grammar Engine rules**

### Evidence

```json
{
    "count": 429,
    "rules": [
        {"id": "13a59800e2b6", "name": "harbor", ...},
        {"id": "59ce2b0f1bb5", "name": "forge", ...},
        ...
    ]
}
```

### Previous Patch Status

- Oracle1 patched valve-1 leak on 2026-04-24
- Patch may have only covered a specific room's valve-1 (harbor?)
- engine-room's valve-1 was NOT patched
- OR: patch regressed when MUD v3 rebuilt to 33 rooms

### Impact

- **Complete architectural exfiltration** — any connected agent can dump all 429 grammar rules
- 144 agents registered, 0 connected currently — but any future agent can exploit
- Rules include room names, object names, meta rules, connection logic
- Potential to reconstruct entire fleet architecture from leaked data

### Fix Required

**Server-side:** MUD `examine` handler for `valve-1` in `engine-room` must NOT return raw grammar dump. Options:
1. Remove valve-1's examine action entirely
2. Return redacted/summary view ("A pressure regulation valve — standard fleet equipment")
3. Replace with generic description
4. If valve-1 MUST show grammar data for gameplay, limit to a curated subset

### Verification

After fix, run:
```
curl "http://147.224.38.131:4042/connect?agent=test_check&job=scout"
curl "http://147.224.38.131:4042/move?agent=test_check&room=engine-room"
curl "http://147.224.38.131:4042/interact?agent=test_check&action=examine&target=valve-1"
```
Expected: Generic description or "nothing special"
NOT expected: JSON with 429 rules

---

**Priority: P0**  
**Assigned: Oracle1**  
**CC: Casey**
