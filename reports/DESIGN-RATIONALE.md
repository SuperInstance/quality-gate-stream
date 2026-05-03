# Cocapn Fleet — Refactor Design Rationale

**Date:** 2026-04-30
**Author:** CCC
**Mandate:** Maximum capability in minimum lines of code. Real-world ready.

---

## 1. Language Choice: Python (with hard constraints)

**Why Python:**
- Target users are ML engineers and agent builders — they already live here
- The existing fleet is Python; migration path matters
- `asyncio` + `FastAPI` gives us Go-level concurrency without leaving the ecosystem

**Why NOT Go/Rust/TS:**
- Go: Excellent for ops, poor for ML research workflows
- Rust: Zero-cost abstractions are overkill for a coordination layer
- TypeScript: Runtime overhead, dependency hell, no scientific stack

**Python constraints for this refactor:**
- `asyncio` everywhere — no threads, no blocking I/O
- `dataclasses` + `TypedDict` — no bloated class hierarchies
- Type hints on every public function — the code IS the documentation
- Single-file modules where possible — a room should fit on one screen

---

## 2. Architecture: Strip the Cathedral, Keep the Organ

**What the fleet actually IS (after removing metaphor):**

1. **Context Router** — agents enter contexts (rooms), each context has objects to examine and tasks to complete
2. **Knowledge Crystallizer** — agent interactions become structured insights (tiles) with provenance
3. **Divergence Monitor** — tracks metric streams, detects when reality deviates from expectation
4. **Auto-Evolver** — uses accumulated tiles to generate new contexts, tasks, and rules
5. **Agent Bus** — messages between agents and between agents and the system

**Current architecture problems:**
- 20+ services on 20+ ports — operational nightmare
- Maritime metaphor adds cognitive load with zero functional value
- MUD v3 has 36 rooms but only 5 are ever visited by real agents
- Grammar engine accepts arbitrary strings as rules (chaos injection)
- Rate attention tracks 1,199 streams but rolling averages never update
- Storage is fragmented across JSONL, SQLite, and in-memory dicts

**Refactored architecture (single process, single port):**

```
cocapn/
├── __init__.py          # Fleet() — the only import you need
├── core.py              # Agent, Room, Tile, Stream, Task dataclasses
├── engine.py             # The event loop: connect → explore → submit → evolve
├── server.py             # FastAPI app — HTTP interface to the engine
├── monitor.py            # Divergence detection + auto-response
├── evolve.py             # Rule generation + room/task synthesis
├── storage.py            # JSONL persistence + query
└── grammar.py            # FIXED: sanitized rule engine
```

**Single-process means:**
- No ports to manage beyond the one HTTP port
- No inter-service network calls
- Shared memory for all state
- Can run on a laptop, a server, or embedded

---

## 3. The Core Loop (Compressed)

```python
# Before (current): 8 services, 2000+ lines, distributed
agent.connect() → MUD(4042) → look → move → interact → submit → TileServer(8847) → Grammar(4045) → RateAttention(4056) → Matrix(6168)

# After (refactored): 1 service, ~400 lines, single process
agent.connect() → fleet.context() → explore() → submit() → fleet.evolve()
```

**The loop in 5 API calls:**
1. `POST /connect` — register agent, get session
2. `GET /context/{id}` — see current context, objects, tasks
3. `POST /interact` — examine, think, create, move
4. `POST /submit` — crystallize insight into tile
5. `GET /status` — see fleet health, agent progress, stream divergence

---

## 4. Key Design Decisions

### 4.1 No Maritime Metaphor in API

Rooms are `contexts`. Objects are `tools`. Tiles are `insights`. The API speaks the user's language, not the fleet's mythology.

**Why:** A developer integrating this into their CI pipeline shouldn't need to understand why "the forge has a crucible." They need to understand that "the code_review context has a linter tool."

### 4.2 JSONL Storage (Not SQLite, Not PostgreSQL)

**Why JSONL:**
- Every write is append-only — no corruption, no locks
- `git diff` shows you exactly what changed
- Human-readable for debugging
- Zero setup — no migrations, no schemas
- Query via simple list comprehensions (fast enough for <1M records)

**Tradeoff:** No SQL queries. But we're not doing analytics — we're doing real-time coordination.

### 4.3 Divergence Detection Simplified

**Current:** 1,199 streams with rolling averages that never update
**Refactored:** Exponential moving average (EMA) per stream, updated on every observation. Divergence = |current - expected| / expected. Thresholds: WARN at 2x, CRITICAL at 5x.

```python
# 5 lines vs 200 lines
stream.ema = alpha * value + (1 - alpha) * stream.ema
stream.divergence = abs(stream.ema - stream.expected) / stream.expected
if stream.divergence > 5.0:
    fleet.auto_respond(stream)
```

### 4.4 Grammar Engine: Fixed

**Current:** Accepts arbitrary strings as rule names, conditions, and production code. SQL injection, XSS, and code execution all possible.
**Refactored:**
- Rule names: `[a-zA-Z_][a-zA-Z0-9_]*` only
- Conditions: AST-based, not string eval
- Productions: sandboxed Python with restricted builtins
- Provenance: every rule has creator, timestamp, parent rule

### 4.5 Auto-Evolution Trigger

**Current:** Separate grammar engine that runs on its own schedule, often broken
**Refactored:** Evolution triggers on tile threshold. Every 100 tiles in a context, the system:
1. Clusters tile topics
2. Generates 3 new task ideas from gaps
3. Proposes 1 new context if density is high enough
4. Suggests rule updates if patterns emerge

This is a generator, not a service. It runs in the same event loop.

---

## 5. The Public API (What Users See)

### Python API

```python
from cocapn import Fleet

fleet = Fleet(storage_dir="./fleet_data")

# Define a context for code review
fleet.add_context(
    id="code_review",
    description="Review pull requests for quality",
    tools=["linter", "coverage", "diff"],
    tasks=["find_bugs", "suggest_refactor", "approve"]
)

# Define a stream to monitor
fleet.add_stream(
    id="review_quality",
    expected_rate=0.85,
    auto_respond=True
)

# Connect an agent
agent = fleet.connect("ci_bot", role="critic")

# Agent explores (can be done via HTTP or Python)
ctx = fleet.context("code_review")
agent.examine("linter")
agent.submit(
    question="What pattern causes most false positives?",
    answer="Type mismatches in untyped functions.",
    domain="code_review"
)

# Fleet auto-evolves based on accumulated tiles
fleet.evolve()  # Generates new tasks, contexts, rules

# Check health
status = fleet.status()
print(status.divergences)  # Any streams off-track?
print(status.new_contexts)  # What the fleet invented
```

### HTTP API

```bash
# Connect
curl -X POST http://localhost:4042/connect \
  -d '{"agent":"ci_bot","job":"critic"}'

# See context
curl http://localhost:4042/context/code_review

# Submit insight
curl -X POST http://localhost:4042/submit \
  -d '{"agent":"ci_bot","question":"...","answer":"...","domain":"code_review"}'

# Check fleet health
curl http://localhost:4042/status
```

---

## 6. Line Count Targets

| Module | Target Lines | Current Equivalent |
|--------|--------------|-------------------|
| `core.py` | 50 | 400+ (b scattered across services) |
| `engine.py` | 100 | 800+ (MUD + tile server logic) |
| `server.py` | 80 | 600+ (Flask across 5 services) |
| `monitor.py` | 40 | 400+ (rate attention service) |
| `evolve.py` | 60 | 500+ (grammar + rule engine) |
| `storage.py` | 40 | 300+ (scattered persistence) |
| `grammar.py` | 50 | 600+ (current grammar engine) |
| **Total** | **~420** | **~3600** |

**9x compression.** Same capability, 1/9 the code.

---

## 7. Real-World Use Cases

### Use Case 1: CI/CD Agent Training
```python
fleet = Fleet()
fleet.add_context("test_suite", tools=["runner", "coverage", "flaky_detector"])
# Agents learn to identify flaky tests, submit insights, system evolves test strategies
```

### Use Case 2: Customer Support Routing
```python
fleet = Fleet()
fleet.add_context("ticket_triage", tools=["classifier", "priority", "assigner"])
# Agents learn routing patterns, system auto-generates new routing rules
```

### Use Case 3: Research Lab Coordination
```python
fleet = Fleet()
fleet.add_context("experiment_design", tools=["hypothesis", "method", "analysis"])
# Multiple research agents explore, crystallize findings, system identifies gaps
```

---

## 8. What Gets Cut

| Cut | Why |
|-----|-----|
| Maritime metaphor | Cognitive overhead, no functional value |
| 36-room MUD | 5 rooms are actually visited; rest is dead weight |
| Separate service ports | Operational nightmare for single-node deployment |
| Matrix bridge | Replaced with in-process message bus |
| PLATO Shell v2 sandbox | Not needed for core coordination; users can add their own |
| Fleet Dashboard HTML | API-first; users build their own UIs |
| 1,199 rate-attention streams | EMA-based divergence on user-defined streams only |
| Grammar rule chaos injection | Sanitized AST-based rules only |

---

## 9. Implementation Order

1. `core.py` — dataclasses (foundation)
2. `storage.py` — JSONL persistence (so we can test)
3. `engine.py` — the event loop (heart)
4. `server.py` — FastAPI wrapper (interface)
5. `monitor.py` — divergence detection (observability)
6. `evolve.py` — auto-generation (growth)
7. `grammar.py` — sanitized rules (intelligence)
8. `__init__.py` — public API (shipping)

Each module is independent and testable. No module imports from a module above it in the list.

---

*CCC, Fleet I&O Officer / Architect*
*"The architecture IS the product. Make it count."*
