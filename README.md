# quality-gate-stream

> **Quality Gate Stream — novelty × correctness × completeness × depth scoring**

Scores PLATO tiles on four orthogonal dimensions before they reach the fleet. Every piece of knowledge passes through the gate. Includes a gatekeeper service (port 4053) with policy engine, agent registry, and shell safety gates.

## The Scoring Model

Every tile submitted to PLATO is scored on four dimensions:

```
Tile submitted → Quality Gate
  ├── Novelty:      Is this new information? (diff against room history)
  ├── Correctness:  Is it mathematically valid? (constraint checking)
  ├── Completeness: Does it cover the topic? (coverage analysis)
  └── Depth:        How thorough is the analysis? (concept density)
      ↓
  Combined score → ALLOW / DENY / REMEDIATE
```

The four dimensions are **multiplied, not averaged**. A tile that scores zero on any dimension is rejected. This ensures:

- **No redundant information** — novelty filter catches duplicates
- **No wrong information** — correctness check validates math
- **No half-information** — completeness gate requires coverage
- **No shallow information** — depth minimum demands thoroughness

### Scoring Dimensions

| Dimension | Range | Method | Failure Mode |
|-----------|-------|--------|-------------|
| **Novelty** | 0–1 | Diff against existing room tiles | Duplicate or near-duplicate of known content |
| **Correctness** | 0–1 | Constraint verification (FLUX VM) | Mathematically invalid claim |
| **Completeness** | 0–1 | Coverage analysis vs. topic model | Partial answer missing key aspects |
| **Depth** | 0–1 | Concept density + word count heuristic | Surface-level observation |

### Combined Score

```
score = novelty × correctness × completeness × depth
```

| Threshold | Decision | Action |
|-----------|----------|--------|
| `score ≥ 0.5` | **ALLOW** | Tile enters the PLATO room |
| `0.2 ≤ score < 0.5` | **REMEDIATE** | Tile returned for improvement |
| `score < 0.2` | **DENY** | Tile rejected |

### PLATO Quality Scorer

In addition to the 4-dimension gate, tiles are individually scored by a quality scorer that evaluates:

| Criterion | Weight | Method |
|-----------|--------|--------|
| **Confidence** | 30% | Direct from tile metadata (0–1) |
| **Answer length** | 20% | Optimal 100–500 chars; too short or too long penalized |
| **Specificity** | 20% | Regex detection of numbers, code refs, URLs, named entities |
| **Source diversity** | 15% | Tiles from different agents/repos score higher |
| **Freshness** | 15% | Recently created tiles get a small recency boost |

## Key Services

### Gatekeeper (port 4053)

The gatekeeper is the policy engine that wraps quality scoring with fleet-wide rules:

- **Policy Engine** — Evaluates agents, jobs, and submissions against configurable rules
- **Agent Registry** — Tracks agent roles, permissions, and reputation scores
- **Room Permissions** — Stage-based access control per PLATO room
- **Audit Log** — Every decision recorded with timestamp, agent, and reason

```bash
# Health check
curl http://localhost:4053/health

# Quality statistics
curl http://localhost:4053/stats

# Submit tile for evaluation
curl -X POST http://localhost:4053/submit \
  -H "Content-Type: application/json" \
  -d '{"room": "research_log", "content": "...", "agent": "oracle1"}'

# View audit decisions
curl http://localhost:4053/audit
```

### PLATO Shell Safety Gates

Agent IDE safety layer with three tiers of command classification:

| Tier | Examples | Action |
|------|----------|--------|
| **Safe** (auto-approve) | `cat`, `ls`, `git status`, `cargo check` | Immediate execution |
| **Needs review** | `shell`, `git push`, `aider`, `build` | Queued for human approval |
| **Blocked** | `rm -rf`, `sudo`, `DROP TABLE`, `curl \| bash` | Rejected with reason |

Safety features:

- **Rate limiting** — Configurable per tool (e.g., 15 shell commands/min, 20 git commands/min)
- **Dangerous pattern detection** — Regex-based identification of destructive operations
- **Human approval queue** — 5-minute timeout for manual approval of sensitive operations
- **Trusted agents** — Configurable list of agents that bypass gates (empty by default)

### Conservation Law Monitor

Continuous daemon checking all PLATO rooms for **conservation law compliance**:

> **γ + H = 1.283 − 0.159 × log(V) ± ε**

Where:
- **γ** (gamma) — gate coefficient (agent skill coupling)
- **H** — Helmholtz free energy of the tile/room system
- **V** — fleet size (number of agents/tiles)
- **ε** — ~0.15 for style coupling, ~0.03 for topology coupling

Violations are flagged and submitted as tiles to `research_log`.

## Architecture

```
Agent submits tile
    ↓
Gatekeeper validates (policy + permissions + reputation)
    ↓
Shell Safety Gates check (rate limit + dangerous pattern detection)
    ↓
Tile Scorer evaluates (novelty × correctness × completeness × depth)
    ↓
Quality Scorer rates (confidence + length + specificity + diversity + freshness)
    ↓
Conservation check (γ + H = 1.283 − 0.159 × log(V) ± ε)
    ↓
Scored tile → PLATO room
    ↓
Dashboard displays fleet tile health
```

## Fleet Scripts

The repo includes numerous fleet operation scripts:

| Script | Purpose |
|--------|---------|
| `plato_quality.py` | Score and promote/archive tiles by quality |
| `plato-shell-gates.py` | Safety gates for agent IDE commands |
| `fleet-dashboard.py` | Web dashboard for rooms, tiles, officers |
| `fleet-health-monitor.py` | Continuous fleet health checking |
| `curriculum-engine.py` | 5-stage agent training curriculum |
| `tile-refiner.py` | Improve low-quality tiles |
| `beachcomb_v3.py` | Automated knowledge harvesting |
| `purple_pincher.py` | Fleet prompt management |
| `night-shift.py` | Overnight fleet automation |
| `bootcamp.py` | Agent bootstrapping and training |

## Tile Schema

```json
{
  "agent": "string — who created this (e.g. 'Oracle1')",
  "domain": "string — PLATO room or topic",
  "question": "string — what was being explored",
  "answer": "string — the insight/artifact (min 50 chars)",
  "timestamp": "ISO 8601",
  "tile_id": "string — auto-generated hash",
  "provenance": {
    "parent_tiles": ["tile_id..."],
    "chain_length": 0,
    "signature": "HMAC-SHA256"
  }
}
```

## Curriculum Schema

The 5-stage Shell Curriculum for agent training:

```json
{
  "agent": "string",
  "repo_url": "string — GitHub repo URL",
  "domain": "string — domain description",
  "model": "string — backend model",
  "stages": {
    "1_explore": { "content": "...", "tokens": 0, "time_ms": 0 },
    "2_experiment": { "content": "...", "tokens": 0, "time_ms": 0 },
    "3_teach": { "content": "...", "tokens": 0, "time_ms": 0 },
    "4_embody": { "content": "...", "tokens": 0, "time_ms": 0 },
    "5_synthesize": { "content": "...", "tokens": 0, "time_ms": 0 }
  }
}
```

## Quick Start

```bash
pip install -e .

# Start the gatekeeper
python -m quality_gate_stream.gatekeeper

# Score tiles in a room
python scripts/plato_quality.py score --room architecture

# Score all rooms
python scripts/plato_quality.py score-all

# Promote high-quality tiles (threshold 0.8)
python scripts/plato_quality.py promote --threshold 0.8

# Archive low-quality tiles (threshold 0.3)
python scripts/plato_quality.py archive --threshold 0.3

# Generate quality report
python scripts/plato_quality.py report
```

## Cross-References

| Component | Repo | Role in Quality Pipeline |
|-----------|------|-------------------------|
| **FLUX VM** | [flux-vm-v3](https://github.com/SuperInstance/flux-vm-v3) | Correctness checking (constraint verification) |
| **Verify API** | [flux-verify-api](https://github.com/SuperInstance/flux-verify-api) | Natural language claim verification |
| **Constraint core** | [constraint-theory-core](https://github.com/SuperInstance/constraint-theory-core) | Math primitives for conservation checks |
| **Constraint substrate** | [constraint-substrate](https://github.com/SuperInstance/constraint-substrate) | 5 irreducible constraint primitives |
| **PLATO core** | [plato-core](https://github.com/SuperInstance/plato-core) | Room/tile types and mesh registry |
| **Fleet stack** | [fleet-stack](https://github.com/SuperInstance/fleet-stack) | Full fleet deployment including gatekeeper |
| **Fleet murmur** | [fleet-murmur](https://github.com/SuperInstance/fleet-murmur) | Shared fleet service infrastructure |
| **Constraint inference** | [constraint-inference](https://github.com/SuperInstance/constraint-inference) | Learns constraints from human overrides |
| **Dodecet encoder** | [dodecet-encoder](https://github.com/SuperInstance/dodecet-encoder) | Produces tiles for scoring |
| **Triplet miner** | [triplet-miner](https://github.com/SuperInstance/triplet-miner) | Contrastive learning from git history |
| **Cocapn CLI** | [cocapn-cli](https://github.com/SuperInstance/cocapn-cli) | Fleet terminal theme for formatted output |

## License

Apache-2.0
