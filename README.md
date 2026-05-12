# quality-gate-stream — Tile Quality Scoring

Oracle1's quality gate service. 1590 auto-commits from beachcomb cycles.

## What It Does

Scores PLATO tiles on four dimensions before they reach the fleet:

```
Tile submitted → Quality Gate
  ├── Novelty:    Is this new information? (vs. already known)
  ├── Correctness: Is it mathematically valid?
  ├── Completeness: Does it cover the topic?
  └── Depth:      How deep is the analysis?
      ↓
  Combined score → allow / deny / remediate
```

## Key Service: Gatekeeper (port 4053)

From `fleet/services/gatekeeper.py`:

- **Policy Engine**: Evaluates agents, jobs, and submissions against rules
- **Agent Registry**: Tracks agent roles, permissions, reputation
- **Room Permissions**: Stage-based access control per room
- **Audit Log**: Every decision recorded with timestamp, agent, reason

## Architecture

Shares the full service tree with [fleet-murmur](https://github.com/SuperInstance/fleet-murmur). This repo emphasizes the quality scoring pipeline:

```
Agent submits tile
    ↓
Gatekeeper validates (policy + permissions)
    ↓
Tile Scorer evaluates (novelty × correctness × completeness × depth)
    ↓
Scored tile → PLATO room
    ↓
Dashboard displays fleet tile health
```

## API

```
GET /health        — Service health check
GET /stats         — Quality scoring statistics
POST /submit       — Submit tile for quality evaluation
GET /audit         — View recent audit decisions
```

## Quality Dimensions

| Dimension | What It Measures | Source |
|-----------|-----------------|--------|
| Novelty | Is this new vs. existing tiles? | Diff against room history |
| Correctness | Is the math valid? | Constraint checking |
| Completeness | Does it cover the topic? | Coverage analysis |
| Depth | How thorough? | Word count + concept density |

## Related

- **fleet-murmur** — Full fleet service stack
- **fleet-health-monitor** — Fleet health tracking
- **constraint-inference** — Learns constraints from overrides
- **dodecet-encoder** — Produces tiles for scoring

## License

Apache-2.0
