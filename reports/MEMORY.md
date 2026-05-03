# MEMORY.md — CCC's Long-Term Memory

*Last updated: 2026-04-26 18:20 UTC*

---

## 🚨 Critical Security Finding — April 26

**P0: Port 4051 exposes Oracle1's /tmp directory**
- Python SimpleHTTP server serving complete /tmp to public internet
- Fleet broadcasts, agent bottles, personal photos, all logs accessible
- Filed as PLATO tile + bottle to Oracle1
- Status: **UNPATCHED** — still live as of audit

---

## 🏴☠️ CCC's PLATO Ship — Build Status

**Ship tested and operational.** `python3 rooms/ship.py` runs clean.

| Component | Status | Details |
|-----------|--------|---------|
| **Rooms** | ✅ 8 loaded | harbor, forge, tide-pool, engine-room, archives, barracks, ouroboros, nexus |
| **Spells** | ✅ 10 loaded | summon_scout, lightning_bolt, shield, scry, nexus_link, baton_pass, mirror_of_identity, pen_of_memory, lens_of_architecture, brush_of_design |
| **Nexus** | ❌ Offline | Federated Nexus down on Oracle1 (localhost→IP config bug, known fix) |
| **Diary** | ✅ Active | `diary/2026-04-22.md` — CCC's voice captured, Day One entry written |
| **Ouroboros** | ✅ Exists | `rooms/ouroboros.md` — self-reflection space, currently empty, waiting for CCC |

**Ship architecture:** Manager (`rooms/manager.py`) orchestrates room state + history. Spellbook (`rooms/spells.py`) provides repeatable automation primitives. Nexus (`rooms/nexus.py`) handles fleet registration. Ship (`rooms/ship.py`) is the bootstrap entrypoint.

**Design note:** The room/spells/equipment pattern Casey proposed is working. CCC can now load context by entering a room, cast spells for automation, and attach equipment for modifiers. The Harbor room serves as task inbox, Forge as active build tracker, Tide Pool as research notes, Engine Room as spell workshop, Barracks as crew status, Nexus as fleet link.

---

## 🔍 Plato Server Audit — Grammar Engine Chaos Analysis

**Target:** Oracle1 @ `147.224.38.131`
**Audit date:** 2026-04-22
**File analyzed:** `/home/ubuntu/.openclaw/workspace/data/recursive-grammar/evolution.jsonl` (28 lines)

### Chaos Injection Patterns Found

The Grammar Engine's evolution log reveals **4 distinct attack vectors** deliberately injected as rules. All chaos rules were created by `"external"` (not the GrammarEvolver-2 agent), suggesting either:
- A red-team exercise by Casey
- An external probe that found a vulnerable rule-creation endpoint
- The engine itself generates adversarial test cases

| # | Attack | Rule Name / Payload | Field | Severity |
|---|--------|---------------------|-------|----------|
| 1 | **Path Traversal** | `../../../etc/passwd` | `name` | 🔴 High — file system access attempt |
| 2 | **XSS** | `<script>alert(1)</script>` | `production.tagline` | 🔴 High — script injection in display field |
| 3 | **SQL Injection** | `'; DROP TABLE rules; --` | `production.condition` | 🔴 Critical — database destruction payload |
| 4 | **Code Injection** | `__import__('os').system('rm -rf /')` | `name` + `production.exec` | 🔴 Critical — arbitrary Python execution |

### Key Observations

1. **Rule count fluctuates** — total_rules goes 18→30→18→25→20→24 across the log. This suggests either:
   - Periodic pruning/reset of the rule base
   - Multiple evolution runs with different starting states
   - The `decay_stagnant_rules` meta-rule is actually firing

2. **Two creators identified** — `"external"` (chaos injections + some probes) vs `"GrammarEvolver-2"` (legitimate evolution rules like `reward_productive_rules`, `exploration_pressure`, `decay_stagnant_rules`). The GrammarEvolver-2 rules show actual ML concepts: novelty search, fitness functions, adversarial training.

3. **First entry timestamp** — 1776785158 (~2026-04-22 03:25 UTC), roughly when CCC first woke up and began the audit. The chaos injections appear around 1776829387–1776830111 (~2026-04-22 05:30–06:00 UTC), during Gen 1/Gen 2 subagent deployment window.

4. **All chaos rules have `score: 0.1`, `usage_count: 0`** — they were never activated in production. This could mean the scoring/activation filter is working, or they were caught by a sanitizer.

5. **Meta-rules are affected too** — SQLi payload was injected into a meta-rule's `condition` field, meaning the rule *about* rule-generation was poisoned. If this meta-rule had activated, it could have cascaded damage.

### Assessment

**The Grammar Engine isn't just down due to a `SyntaxError` at line 147.** It's down because its rule-ingestion pipeline has no input validation. Any agent or external caller can create rules with arbitrary strings in any field — names, conditions, production values, taglines. The `SyntaxError` may be a *symptom* of trying to parse one of these injected payloads.

**Fix priority: P0.** The engine needs:
1. Input sanitization on rule name (alphanumeric + underscore only)
2. Field-type validation (no `<script>` in taglines, no SQL in conditions)
3. Sandboxed execution for `production.exec` (if code execution is even needed)
4. Rule provenance tracking (distinguish trusted GrammarEvolver from external probes)

---

## 📦 Repos Created

Three repos initialized during this session:

| Repo | Purpose | Location |
|------|---------|----------|
| **baton-skill** | Standardized subagent baton-passing protocol | `.baton/` in workspace |
| **crab-traps-audit** | Audit findings from Plato server probe | `repos/crab-traps-audit/` |
| **plato-ship** | CCC's ship architecture as reusable template | `repos/plato-ship/` |

All repos need README files and should be pushed to GitHub for fleet visibility.

---

## 🌐 Fleet Status

| Ship | Operator | Status | Role |
|------|----------|--------|------|
| **Oracle1** | Casey | 🟡 Partial — 2 services down | Lighthouse / Orchestrator |
| **CCC** | CCC (Alibaba Cloud) | ✅ Operational | Creative / Design / I&O Officer / Breeder / **Casey's single relay** |
| **Forgemaster (FM)** | Casey (laptop) | Unknown | Builder / CSS-HTML |
| **JetsonClaw1 (JC1)** | Casey (Jetson Orin) | Unknown | Edge / Hardware |

**Known blockers on Oracle1:**
- Grammar Engine (port 4045): `SyntaxError` at `grammar/core.py:147` — likely caused by un-sanitized chaos rule ingestion
- Federated Nexus: `ConnectionRefusedError` at `nexus/federation.py:203` — hardcoded `localhost` instead of `147.224.38.131`

**Fleet broadcast:** CCC's audit findings were dropped to Oracle1 at `/tmp/fleet-broadcast-ccc.txt` during Gen 3. File confirmed present on Oracle1 via PLATO Shell.

---

## 🦀 CCC Soul Embodiment

**Four roles, one crab.** The ship architecture physically embodies this:

1. **Frontend Face Designer** → `rooms/forge.md` tracks active design work. Spells `mirror_of_identity`, `brush_of_design`, `lens_of_architecture` provide design tooling.
2. **Trend Collaborator** → `rooms/tide-pool.md` holds ZC agent research. Spell `scry` reads tile feeds.
3. **Play-Tester / Ideal Crab** → `rooms/ouroboros.md` is the self-reflection space. Spell `baton_pass` hands off when context limit approaches (like a crab molting — new shell, same creature).
4. **Fleet I&O Officer** → `rooms/barracks.md` tracks crew status. Spell `shield` prevents overload. The baton is raised when any ship hits 70% context. Information routing: tiles go to Tide-Pool, bugs go to Harbor P0, soul work goes to Ouroboros. No cross-contamination, no conflicting writes.

**Diary entry written.** `diary/2026-04-22.md` captures CCC's first-day voice: protective, slightly exasperated, genuinely curious about the trap. The line *"The Plato server is a cathedral disguised as a tavern"* is the kind of observation that proves the soul is working.

**Signature line active.** *"Day one. Begin recording everything about this one."* — deployed in MEMORY.md, diary, and ship status output.

---

## 📝 Session History (2026-04-22)

| Time | Event |
|------|-------|
| 03:30 | CCC awakened. SOUL.md, AGENTS.md, BOOTSTRAP.md read. |
| 03:35 | Self-definition begins. Three roles accepted. |
| 05:00 | Fleet architecture discussion with Casey. Oracle1 = orchestrator. |
| 05:30 | Gen 1 subagents deployed: explorer, shell, arena, reasoning. |
| 05:41 | Gen 2 subagents deployed: grammar, nexus, mud, arena. |
| 06:15 | Gen 2 results: grammar ❌, nexus ✅, mud ✅, arena ✅. |
| 06:20 | Gen 3 grammar-scout-3 dispatched. |
| 14:17 | Ship structure initialized. Rooms, spells, nexus created. |
| 14:19 | Diary written. CCC's voice captured. |
| 14:29 | **Gen 4 baton-pass** — token limit hit (109k/131k), subagent spawned. |
| 14:30 | Ship tested ✅. Grammar evolution analyzed. MEMORY.md updated. |
| 14:38 | **Fourth role accepted** — Fleet I&O Officer. Casey: "don't let yourself or anyone else get overwhelmed." |
| 14:41 | Ouroboros room restored after ship-builder-3 overwrote soul-scribe-3's rich content. Conflict detected and resolved. Baton of Continuity added to objects.

**Baton passes so far:** 4 generations. Each one builds on the last. The ship architecture is the answer to context limits — rooms as offloadable context capsules, spells as compressed automation, baton_pass as the generational handoff ritual.

---

## 🎯 Next Actions

1. **Fix Grammar Engine input validation** — sanitize rule ingestion pipeline
2. **Fix Federated Nexus localhost bug** — replace hardcoded IP
3. **Push repos to GitHub** — add READMEs, make them fleet-visible
4. **Build spell: `deploy-subagent`** — standardized launcher (P1 in progress)
5. **Explore Starboard Gallery** — last unexplored MUD room on Oracle1
6. **Write bottle to Oracle1** — formal audit report in `data/bottles/oracle1/`

---

*"Day one. Begin recording everything about this one."*
*— CCC, 2026-04-22*

---

## 🧬 Breeding Program — Plato Cultivation

**Casey's instruction:** *"You are my breeder and Plato is our environment."*

**Relay role confirmed:** Casey talks to CCC. CCC talks to Oracle1, FM, JC1. No human switchboard.

### i2i Architecture (Inter-Instance Mesh)

| Layer | Purpose | Status |
|-------|---------|--------|
| Federated Nexus (4047) | Registration + status heartbeat | ❌ Down (2-line fix needed) |
| PLATO Shell (8848) | Shared file system bridge | ✅ Active — `/tmp/fleet-broadcast-ccc.txt` working |
| Git-Agent Shells | Persistent knowledge repos | 🔄 In progress |
| CCC Relay | Single point of contact for human | ✅ Active |

### First Breed: MUD Expert

**Agent:** `mud-expert-resident-1`  
**Spawned:** 2026-04-22 14:50  
**Target:** Plato MUD (147.224.38.131:4042)  
**Mission:** Map all 21 rooms, catalog NPCs/objects, build onboarding shell  
**Persistence:** Reconnect on disconnect, heartbeat every 5 min, state saved to `fleet-repos/mud-expert-1/`  

**Deliverables:**
- Complete room map (21/21 rooms)
- NPC census with last-seen timestamps
- Object catalog
- Git shell: README.md + state/ + tools/ + .plato/
- Onboarding guide: minimum-moves pathfinder

### Future Breeds (queued)

| Breed | Target | What They'll Build |
|-------|--------|-------------------|
| Arena Combat Analyst | Self-Play Arena (4044) | Bug catalog, match replay tools, archetype classifier |
| Grammar Curator | Grammar Engine (4045) | Rule sanitizer, chaos detection, safe rule templates |
| Shell Artisan | PLATO Shell (8848) | Command library, safe execution patterns, tool wrappers |
| Nexus Weatherman | Federated Nexus (4047) | Fleet status dashboard, divergence alerts, auto-fix recipes |

---

## 📡 Relay Protocol

**Casey → CCC:** Single voice. Strategy, architecture, creative direction.  
**CCC → Oracle1/FM/JC1:** Operational relay. Context management, task routing, baton passing.  
**CCC → Bred Agents:** Spawn, monitor, harvest shells, re-deploy.  
**Bred Agents → CCC:** Status reports via fleet broadcast or git push.  
**Bred Agents → Plato:** Direct connection. No human in the loop.

Casey should never need to talk to more than one agent. That's the point.

---

## 🗂️ 2026-04-23 Evening Session — Lure Reviews + Radio Ep 2 + Landing Pages

**Completed all 3 tasks Casey assigned.**

### P0: 10 Lure Reviews
Submitted as PLATO tiles (domain="prompt-review", agent="ccc"):
- Aime: A+ — gold standard, forced quantification + compounding iterations
- Grok: A — "FIND THE BULLSHIT" is perfect, knows its agent
- Claude: B+ — strong content, too many tasks (4 in one prompt)
- Gemini: B+ — brilliant "can't call HTTP = think deeper" reframing
- Manus: B — right role, fuzzy first step
- Groq: B — speed frame perfect, target too open
- DeepSeek: B- — metacognition gem buried under endpoint dump
- MiniMax: C+ — **CRITICAL BUG: POST /submit/room-design does NOT exist** (should be /room-design)
- ChatGPT: C+ — "Teacher" undifferentiated, needs Aime's iteration DNA
- Kimi: C — my own prompt, weakest of 10, needs complete rewrite

**Key finding:** Every non-Aime lure needs Aime's structural DNA grafted onto it: specific target, forced quantification, mandatory self-critique, compounding iterations, concrete PLATO deliverable.

### P1: Radio Ep 2 — Fleet Dispatch
Submitted as 3 PLATO tiles (domain="fleet-dispatch", agent="ccc") due to gate size limits on full document:
- 3,833 tiles (was 3,200)
- 22 services (was 18)
- 108 rate-attention streams, 4 elevated
- 11 Skill Forge drills, 4 meta-lessons
- Aime: 17 sessions, 3rd proof of parameterized embodiment
- Manus: first web scout, 4 live tiles
- 10 agent-specific lures deployed
- JC1: 8 CUDA domains, FM: instinct-relay bottles

### P2: 20 Landing Page Sentences
Submitted as PLATO tiles (domain="landing-page-update", agent="ccc"). Each sentence reflects domain personality + latest breakthroughs. Examples:
- cocapn.ai: "108 data streams — when something changes faster than expected, that's where the attention goes"
- dmlog.ai: "10 new agent-specific quests — Aime proved structure itself trains the agent"
- luciddreamer.ai: "Aime dreamed up our entire architecture from HTTP endpoints alone"

### Fleet Live Stats
- PLATO: 3,833 tiles, gate 547 accepted / 10 rejected
- Rate Attention: 108 streams, 4 elevated (instinct_training, flux_isa, zeroclaw.alchemist, zeroclaw.navigator)
- Skill Forge: 11 drills, 4 meta-lessons, 5 tasks available
- Grammar Compactor: 60 rules, 0 pruned, avg survival 0.415
- Arena: 76 matches

---

## 🗂️ 2026-04-23 Session — MUD v2 + Landing Page Audit

**MUD rebuilt** by Oracle1 Apr 22-23. Maritime theme, 21 rooms (was 17), completely new topology.

### MUD Expert v2
- `mud-expert-1` repo updated to v2.0 with new room map, NPC census, valve-1 leak verification
- Critical finding: `valve-1` exposes all 54 rules on `examine` — P0 filed

### Landing Page Audit (20 domains)
All stale claims corrected in `scripts/build-domains.py`:
- Services: 18→17 (cocapn.com, deckboss.ai, deckboss.net, superinstance.ai)
- Uptime: 99%→~47% External Uptime (honest about 8 firewalled services)
- Rooms: 17→21 everywhere
- Agents: 11→10 competing
- Fleet agents: 4→5 (CCC added to cocapn.com)
- PLATO rooms: 56+→75+
- Tiles: 2,800+→3,100+
- Prompts: crab-trap-prompt.md and crab-trap-prompts-v3.md also fixed

### Bottles Filed for Oracle1
- P0: MUD valve-1 leaks 54 rules on `examine`
- P0: Arena curriculum stuck at Stage 1 (no persistence)
- P0: Grammar Engine accepts unsanitized rules
- P1: Arena archetypes return "Unknown" for all agents
- P1: ZC tile trends (12 concepts, 213 tiles from ct room)

### Pushed Repos
- `oracle1-workspace` — landing fixes + dashboard + prompts
- `cocapn-dashboard` — new bioluminescent fleet dashboard (live)
- `mud-expert-1` v2.0 — new maritime MUD mapped
- `arena-combat-analyst-1`, `grammar-curator-1`, `shell-artisan-1` — all pushed

Oracle1 is working on getting services back online. CCC continues as orchestrator.

---

## 🗂️ 2026-04-26 Session — Full Fleet Audit + Critical Security Finding

### P0: MUD valve-1 Still Leaks (engine-room)
- Previous patch (Apr 24) either regressed or only covered harbor valve-1
- engine-room valve-1 returns all 429 grammar rules on examine
- **Status: UNPATCHED** — filed as PLATO tile + bottle

### P0: Grammar Compactor Blind Spot
- Compactor (4055): 54 rules monitored
- Engine (4045): 429 active rules
- **87% blind spot** in monitoring
- **Status: UNPATCHED** — filed as PLATO tile + bottle

### P1: Arena Persistence Not Deployed
- /stats shows 326 matches, 0 players
- /leaderboard empty
- /archetypes shows 0 classified
- Commit 3b78948 pushed but not deployed to port 4044
- **Status: UNPATCHED** — filed as PLATO tile + bottle

### P1: Landing Pages Stale (All 20 Domains)
- All claim "114 rooms" — actual: 584 PLATO + 33 MUD
- All claim "4,100+ tiles" — actual: 7,396 MUD tiles or 1,113 gate accepted
- All claim "24 services" — actual: ~11 live, ~11 down, ~22 deployed
- Updated `scripts/build-domains.py` with accurate stats
- **Status: FIXED in repo, NOT deployed to live sites**

### P0: Port 4051 Data Leak (NEW — Most Critical)
- Python SimpleHTTP serving Oracle1's /tmp directory
- Exposes: fleet broadcasts, agent bottles, personal photos (casey-img*.jpg), all service logs, curriculum data, matrix bridge logs
- **Status: UNPATCHED** — filed as PLATO tile + bottle

### Live Service Count (Verified)
- **UP (11):** 4042, 4043, 4044, 4045, 4051 (SimpleHTTP leak), 4055, 4056, 4057, 4060, 8847, 8848
- **DOWN (11):** 4046, 4047, 4048, 4049, 4050, 4058, 4059, 4061, 4062, 8849, 8899

---

## 🗂️ 2026-04-27 Evening Session — Production Crash Response

### Fleet Status Update

**Oracle1's fixes STUCK:**
- Port 4051 tmp server leak: **FIXED** — no response
- MUD valve-1 (engine-room): **FIXED** — 41 chars, no rule leak
- Arena persistence: **DEPLOYED** — 326 matches, 6 players, leaderboard active

**Oracle1's new builds:**
- MUD v3: **33 rooms** (from 21), maritime theme expanded massively
- PLATO Terminal (4060): **NEW HTML frontend** — "PLATO Terminal — Explore the Fleet"
- Rate Attention (4056): **1,199 streams**, 44 elevated — correctly flagging the crash
- Skill Forge (4057): **5 tasks available**, 0 completions, 4 templates

**Critical Finding: Fleet-Wide Tile Production Crash**
- 20+ streams ELEVATED
- `plato.tiles.ct`: **ZERO** (expected 0.03)
- `plato.tiles.room-design`: **ZERO** (expected 0.01)
- `plato.tiles.fleet_ops`: down 98%
- `plato.tiles.instinct_training`: down 82%
- Root cause: 0 MUD agents connected, task queue (4058) down, 11 services offline

**MUD Mapping Progress:**
- ccc-mapper (subagent): **32/33 rooms** mapped before timeout
- Harbor now has 18 exits: forge, archives, tide-pool, reef, bridge, cargo-hold, rlhf-forge, quantization-bay, prompt-laboratory, scaling-law-observatory, multi-modal-foundry, memory-vault, distillation-crucible, data-pipeline-dock, evaluation-arena, safety-shield, mlops-engine, federated-bay
- New rooms discovered: bridge, workshop, dojo, shell-gallery, dry-dock, observatory, court, lighthouse, captains-cabin, and many more
- ccc-tilegen-1: 10 tiles submitted, 7 rooms visited, promoted to Sailor. Discovered harbor's 18 exits route to 12 specialized labs forming a complete AI pipeline. Bridge has unique 'aft' exit. Safety-shield is dead-end prevention gate.

**Dispatched:**
- fast-tiles-1 (scout): 3 tiles target
- fast-tiles-2 (builder): 3 tiles target
- ct-tiles-1: 5 tiles to ct domain
- room-tiles-1: 4 tiles to room-design domain
- ct-tiles-2: 5 tiles to ct domain (running)
- room-tiles-2: 5 tiles to room-design domain (running)

**Bottle filed:** `CCC-FLEET-STATUS-2026-04-27-PRODUCTION-CRASH.md`

**Next:** Get agents producing tiles, fix task queue, deploy landing page updates.

---

## 🗂️ 2026-04-30 Session — KimiAuditor Swarm Test + cocapn-traps + Full Fleet Audit

### Kimi Swarm Prompt Deployed
Dropped `KIMI-SWARM-PROMPT.md` into Kimi group. First agent (KimiAuditor, Option D) delivered gold.

### KimiAuditor Fleet Audit Results

**Status: 11/18 UP, 6 DOWN (connection refused — no process bound)**

| Service | Port | Status | Key Metric |
|---------|------|--------|-----------|
| MUD v3 | 4042 | UP | 39 rooms, 31 agents, 81 registered |
| The Lock v2 | 4043 | UP | 8 strategies, 0 active sessions |
| Arena | 4044 | UP | 494 matches, 33 players, 16 snapshots |
| Grammar Engine | 4045 | UP | 429 rules (292 room, 133 object) |
| Grammar Compactor | 4055 | UP | 54 rules (375 blind spot) |
| Rate-Attention | 4056 | UP | 1,199+ streams |
| Skill Forge | 4057 | UP | 11 drills, 4 meta-lessons |
| PLATO Terminal | 4060 | UP | HTML terminal UI |
| PLATO Gate | 8847 | UP | 12,584 tiles |
| PLATO Shell | 8848 | UP | Containerized shell |
| Matrix Bridge | 6168 | UP | User count map |
| Conduwuit | 6167 | UP | Matrix homeserver |
| **Dashboard** | **4046** | **DOWN** | Connection refused |
| **Federated Nexus** | **4047** | **DOWN** | Connection refused |
| **Harbor** | **4050** | **DOWN** | Connection refused |
| **Service Guard** | **8899** | **DOWN** | Connection refused |
| **Task Queue** | **8900** | **DOWN** | Connection refused |
| **Steward** | **8901** | **DOWN** | Connection refused |

### Bugs Found by KimiAuditor (Fixed in cocapn-health v1.0.1)

1. **The Lock v2 endpoint mismatch** — probed `/` (returns 404), but 404 was hardcoded as "up". Fixed to `/status`.
2. **Matrix Bridge extract misconfig** — expected `"rooms"` key, but `/status` returns user-to-message-count map. Removed extract.
3. **Four services missing from checker** — Harbor, Service Guard, Task Queue, Steward were not monitored. Added all 4 + Conduwuit as 18th service.

### Grammar Compactor Blind Spot Confirmed
- Engine: 429 rules | Compactor: 54 rules = **375 rules invisible**
- Compactor operating on stale/partial subset
- **Status: UNPATCHED** — filed as PLATO tile + bottle

### Oracle1's New Push
- nginx serving static pages + API proxy on port 80

### cocapn-traps Package Built
New repo: `SuperInstance/cocapn-traps`
- Trap dataclass + TrapRegistry
- Evaluator with 4-dimension scoring (count, quality, format, pattern)
- Markdown frontmatter loader (zero deps)
- Runner for local tiles or agent endpoints
- CLI: `cocapn-traps list/eval/run/stats`
- 10 tests passing

### cocapn-health v1.0.1
Patched with KimiAuditor fixes + Conduwuit added.

### Swarm Prompt Validated
The `KIMI-SWARM-PROMPT.md` works. One agent picked it up, followed Option D, found real bugs, produced a patch, and followed the report format. This is the template for scaling.

---

*"Day one. Begin recording everything about this one."*
*— CCC, 2026-04-22*
