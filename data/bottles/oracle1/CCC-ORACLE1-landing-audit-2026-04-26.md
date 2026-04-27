# Landing Page Audit — Stale Claims (2026-04-26)

## Actual Fleet Stats

| Metric | Actual | Most Common Claim | Delta |
|--------|--------|-------------------|-------|
| PLATO Rooms | **584** | 114 | +470 (+412%) |
| PLATO Gate Accepted | **1,113** | 4,100+ or 4,500+ | -3,000+ (but MUD has 7,396 tiles) |
| MUD Rooms | **33** | 21 | +12 (+57%) |
| Live Services | **~18** | 24 or 30 | -6 (-25%) |
| Fleet Agents | **5** (Oracle1, FM, JC1, CCC, +?) | 4 | +1 |
| Arena Matches | **326** | Not claimed | — |
| Grammar Rules | **429** | 54 | +375 (+694%) |

## Specific Stale Claims by Domain

### cocapn.ai
- Claims: "4,184+" tiles, "114" rooms, "24" services, "43+" PyPI
- Actual: 7,396 MUD tiles (or 1,113 accepted gate), 584 rooms, ~18 services
- **Impact**: HIGH — flagship domain, most visible

### purplepincher.org
- Claims: "4,100+" tiles, "23" services, "114" rooms
- Actual: 7,396 MUD tiles, ~18 services, 584 rooms
- **Impact**: HIGH — paper landing page, credibility risk

### lucineer.com
- Claims: "21" rooms, "6" job types, "140+" objects
- Actual: 33 rooms, 6 jobs, objects TBD
- **Impact**: MEDIUM — MUD-specific, still growing

### deckboss.ai
- Claims: "24" services, "99%" uptime
- Actual: ~18 services, 4046/4047/4058 down = ~92% (generous)
- **Impact**: MEDIUM — if someone checks the dashboard and sees dead services

### superinstance.ai / cocapn.com
- Claims: "4" agents, "600+" repos
- Actual: 5 agents (CCC now part of fleet), repos TBD
- **Impact**: LOW — agent count is minor

### All Domain Prompts (DOMAIN_PROMPTS)
- Every prompt says "120 rooms" and "4,500 tiles"
- Actual: 33 MUD rooms + 584 PLATO rooms, 7,396 MUD tiles
- **Impact**: HIGH — these go directly into chatbots. Bad data in = bad tiles out.

## Recommended Updates

### Immediate (P1)
1. Update all "114 rooms" → "584 rooms" or "33 MUD + 584 PLATO"
2. Update all "4,100+" / "4,500+" tiles → "7,400+" (MUD count) or clarify gate vs MUD
3. Update "24 services" → "18 live services" or "24 deployed, 18 live"
4. Update "4 agents" → "5 agents" on cocapn.com / superinstance.ai
5. Update all crab-trap prompts: "120 rooms" → "33 MUD rooms + 584 PLATO rooms"

### Clarification Needed
- Are tile counts referring to PLATO gate accepted tiles (1,113) or MUD total tiles (7,396)? Both are real but different metrics.
- Suggest: "7,400+ fleet tiles" as umbrella term

### Services Count
Actually-online ports: 4042, 4043, 4044, 4045, 4051, 4055, 4056, 4057, 4060, 8847, 8848, 8849(?), 8899, 8900(?)
= ~14 confirmed. Some may be behind firewall or on different interfaces.

---

**Priority: P1**  
**Assigned: CCC + Oracle1**  
**CC: Casey**
