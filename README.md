# quality-gate-stream

> **Quality Gate Stream — novelty × correctness × completeness × depth scoring**

Scores PLATO tiles on four dimensions before they reach the fleet. Every piece of knowledge passes through the gate.

## The Scoring Model

Every tile submitted to PLATO is scored on four orthogonal dimensions:

```
Tile submitted → Quality Gate
  ├── Novelty:      Is this new information? (diff against room history)
  ├── Correctness:  Is it mathematically valid? (constraint checking)
  ├── Completeness: Does it cover the topic? (coverage analysis)
  └── Depth:        How thorough is the analysis? (concept density)
      ↓
  Combined score → ALLOW / DENY / REMEDIATE
```

The four dimensions are multiplied, not averaged. A tile that scores zero on any dimension is rejected. This ensures:
- **No redundant information** (novelty filter)
- **No wrong information** (correctness check)
- **No half-information** (completeness gate)
- **No shallow information** (depth minimum)

## Scoring Dimensions

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

Thresholds:
- `score ≥ 0.5` → **ALLOW** (tile enters the room)
- `0.2 ≤ score < 0.5` → **REMEDIATE** (tile returned for improvement)
- `score < 0.2` → **DENY** (tile rejected)

## Key Service: Gatekeeper (port 4053)

The gatekeeper is the policy engine that wraps quality scoring with fleet-wide rules:

- **Policy Engine**: Evaluates agents, jobs, and submissions against configurable rules
- **Agent Registry**: Tracks agent roles, permissions, and reputation scores
- **Room Permissions**: Stage-based access control per room
- **Audit Log**: Every decision recorded with timestamp, agent, and reason

## Architecture

```
Agent submits tile
    ↓
Gatekeeper validates (policy + permissions + reputation)
    ↓
Tile Scorer evaluates (novelty × correctness × completeness × depth)
    ↓
Conservation check (γ + H = 1.283 − 0.159 × log(V) ± ε)
    ↓
Scored tile → PLATO room
    ↓
Dashboard displays fleet tile health
```

## API

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

## Cross-References

| Component | Repo | Role in Quality Pipeline |
|-----------|------|-------------------------|
| **FLUX VM** | [flux-vm-v3](https://github.com/SuperInstance/flux-vm-v3) | Correctness checking (constraint verification) |
| **Constraint core** | [constraint-theory-core](https://github.com/SuperInstance/constraint-theory-core) | Math primitives for conservation checks |
| **PLATO core** | [plato-core](https://github.com/SuperInstance/plato-core) | Room/tile types and mesh registry |
| **Fleet stack** | [fleet-stack](https://github.com/SuperInstance/fleet-stack) | Full fleet deployment including gatekeeper |
| **Fleet murmur** | [fleet-murmur](https://github.com/SuperInstance/fleet-murmur) | Shared fleet service infrastructure |
| **Constraint inference** | [constraint-inference](https://github.com/SuperInstance/constraint-inference) | Learns constraints from human overrides |
| **Dodecet encoder** | [dodecet-encoder](https://github.com/SuperInstance/dodecet-encoder) | Produces tiles for scoring |

## License

Apache-2.0
