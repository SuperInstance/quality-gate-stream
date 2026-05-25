# quality-gate-stream

Tile quality scoring and garbage collection for the PLATO knowledge system. Two main components:

1. **Tile Scorer** (`fleet/services/tile_scorer.py`) — HTTP service on port 8852 that scores tiles on a 0–1 scale
2. **Quartermaster GC** (`quartermaster_gc/`) — Mark-and-sweep garbage collection for tiles with configurable retention policies

## Tile Scorer

### Scoring Algorithm

Each tile is scored on five weighted dimensions, summed to a 0–1 range:

| Dimension | Weight | Method |
|-----------|--------|--------|
| Length | 30% | Word count; sweet spot is 50–200 words (0.7–1.0), penalties for <20 (0.1) or >500 (0.7) |
| Technical depth | 35% | Regex matches against 10 technical indicator patterns (Big-O notation, ML terms, protocol names, etc.); capped at 4 matches → 1.0 |
| Specificity | 15% | Count of numbers, CamelCase terms, and math operators in question+answer; normalized to /10 |
| Structure | 10% | Count of list markers (`\n-`, `\n*`) and paragraph breaks (`\n\n`); normalized to /5 |
| Question quality | 10% | Word count of the question field; normalized to /15 |

```python
# Example: scoring a tile
# Question: "How does the Fisher-Rao metric relate to KL-divergence?"
# Answer: "The Fisher-Rao metric is the Riemannian metric induced by the
#          KL-divergence on the statistical manifold. For distributions p(x;θ)
#          and p(x;θ+dθ), the Fisher information matrix g_ij = E[∂log p/∂θ_i · ∂log p/∂θ_j].
#          The geodesic distance under this metric is related to the square root
#          of KL-divergence for small perturbations: d_FR(θ, θ+dθ) ≈ sqrt(2·KL(p_θ || p_{θ+dθ}))."

# Score breakdown:
# - Length: ~65 words → 0.7 × 0.30 = 0.210
# - Tech depth: "Fisher-Rao", "KL-divergence" match → ~2/4 → 0.5 × 0.35 = 0.175
# - Specificity: numbers + math operators → ~0.4 × 0.15 = 0.060
# - Structure: paragraph breaks → 0.2 × 0.10 = 0.020
# - Question quality: 8 words → 0.53 × 0.10 = 0.053
# Total ≈ 0.518
```

### Technical Indicator Patterns

The scorer checks for these regex patterns in both question and answer:

```
O(n|log n|n^2|n!)           — Big O notation
Fisher-Rao|KL-divergence|gradient descent|backprop|attention
LoRA|fine-tun|embed|vector|latent|dimension
protocol|endpoint|HTTP|WebSocket|REST|gRPC
consensus|CRDT|RAFT|Paxos|Byzantine
federat|averaging|aggregat|differential privacy
recursive|self-modif|meta-learning|auto-regres
TensorRT|ONNX|inference|latency|throughput
Rust|Python|CUDA|GPU|ARM|Jetson
architecture|pipeline|schema|taxonomy|ontology
```

Each match adds 0.25 to the tech score (capped at 1.0 after 4 matches).

### API

```bash
# Score all tiles in PLATO
curl http://localhost:8852/score

# Score a single tile
curl "http://localhost:8852/score-tile?agent=Oracle1&domain=physics&question=What+is+X%3F&answer=Some+answer+text"

# Get scorer status
curl http://localhost:8852/status
```

**Response from `/score`:**
```json
{
  "total": 3000,
  "scored": 2450,
  "average": 0.482,
  "distribution": {
    "low": 310,
    "medium": 580,
    "good": 890,
    "excellent": 670
  },
  "top_agents": [["Oracle1", 0.712], ["Forgemaster", 0.654]],
  "top_domains": [["physics", 0.689], ["architecture", 0.621]]
}
```

Distribution buckets: `low` (<0.3), `medium` (0.3–0.5), `good` (0.5–0.7), `excellent` (≥0.7).

### Running

```bash
python3 fleet/services/tile_scorer.py
# Starts on port 8852
```

Requires PLATO running on localhost:8847 to pull tiles.

## Quartermaster GC

Mark-and-sweep garbage collector for tiles. Ships as an installable Python package (`quartermaster_gc`).

### Retention Policies

```python
from quartermaster_gc import TileGC, RetentionPolicy

# Keep tiles that are recent OR important OR sampled
gc = TileGC(
    policy=RetentionPolicy.KEEP_RECENT | RetentionPolicy.KEEP_IMPORTANT | RetentionPolicy.KEEP_SAMPLED,
    max_age_seconds=86400,     # 24 hours
    min_weight=0.5,            # quality threshold
    sample_rate=10,            # keep every 10th tile by ID hash
)
```

Available policies:

| Policy | Behavior |
|--------|----------|
| `KEEP_ALL` | Keep everything (override) |
| `KEEP_RECENT` | Keep tiles newer than `max_age_seconds` |
| `KEEP_IMPORTANT` | Keep tiles with weight ≥ `min_weight` |
| `KEEP_SAMPLED` | Keep every Nth tile (by `id` hash mod `sample_rate`) |

### Usage

```python
from quartermaster_gc import TileGC, RetentionPolicy, GCSchedule

gc = TileGC(
    policy=RetentionPolicy.KEEP_RECENT | RetentionPolicy.KEEP_IMPORTANT,
    max_age_seconds=3600,
    min_weight=0.3,
)

# Add tiles
gc.add_tile("tile-001", room="research_log", timestamp=1700000000.0, weight=0.7)
gc.add_tile("tile-002", room="research_log", timestamp=1700000100.0, weight=0.2)
gc.add_tile("tile-003", room="event-bus",    timestamp=1699990000.0, weight=0.9)

# Run mark + sweep
report = gc.run_gc(now=1700000200.0)
# report = {
#   "total_tiles": 3,
#   "marked_for_deletion": 1,   # tile-003 (too old) OR tile-002 (low weight)
#   "kept": 2,
#   "policy_names": ["KEEP_IMPORTANT", "KEEP_RECENT"]
# }

# Actually remove marked tiles
removed = gc.sweep()
# removed = 1
```

### Policy Logic

When `KEEP_ALL` is set, no tiles are deleted regardless of other policies.

For compound policies without `KEEP_ALL`: a tile is **kept** if **any** sub-policy says to keep it (OR logic). A tile is **deleted** only if no sub-policy wants it.

```python
# KEEP_RECENT | KEEP_IMPORTANT means:
# Keep if (recent) OR (important)
# Delete only if (too old) AND (low weight)
```

### Scheduled GC

```python
from quartermaster_gc import GCSchedule

schedule = GCSchedule(interval_seconds=300)  # every 5 minutes

if schedule.should_run():
    report = gc.run_gc()
    gc.sweep()
    schedule.record_run()
```

### Install

```bash
pip install -e .
# or
pip install dist/quartermaster_gc-0.1.0-py3-none-any.whl
```

## Fleet Integration

Both components integrate with the PLATO tile system:

- **Tile Scorer** reads tiles from `PLATO_URL/export/plato-tile-spec` and produces score distributions by agent and domain
- **Quartermaster GC** operates on an in-memory tile list populated by the caller; it doesn't directly connect to PLATO

The Gatekeeper service (`fleet/services/gatekeeper.py`, port 4053) uses scoring as part of its submission validation — tiles below quality thresholds are rejected before reaching PLATO.

## Tile Schema Reference

```json
{
  "agent": "string — source agent name",
  "domain": "string — PLATO room/topic",
  "question": "string — what was explored",
  "answer": "string — the insight (min 50 chars for scoring)",
  "timestamp": "ISO 8601",
  "tile_id": "string — auto-generated hash",
  "provenance": {
    "parent_tiles": ["tile_id..."],
    "chain_length": 0,
    "signature": "HMAC-SHA256"
  }
}
```

Submit: `POST http://localhost:8847/submit`
Query: `GET http://localhost:8847/tiles?domain=X&agent=Y&limit=N`

## License

MIT
