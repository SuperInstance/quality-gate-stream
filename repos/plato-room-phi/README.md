# Plato Room Phi

> Measure the Integrated Information (Φ) of PLATO rooms — how much a room's whole exceeds the sum of its tiles.

**Topics:** `integrated-information` `phi` `plato` `consciousness-metrics` `knowledge-coherence` `tile-analysis` `knowledge-graph`

Part of the [Cocapn fleet](https://github.com/SuperInstance) — lighthouse keeper architecture.

---

## What It Does

Based on Integrated Information Theory (Tononi), this package computes **Phi (Φ)** — a single number measuring how integrated and coherent a PLATO room's knowledge is.

- **High Φ** = room tiles cross-reference each other, confidence is diverse → rich, coherent knowledge
- **Low Φ** = tiles are isolated, unrelated, or low-confidence → fragmented or unconscious

Two implementations are provided:
- `compute_phi.py` — standalone function for offline use
- `plato_room_phi/` — `RoomPhi` class for live PLATO API queries

## Quick Start

### Install

```bash
pip install .
# or from GitHub
pip install git+https://github.com/SuperInstance/plato-room-phi.git
```

### Use the function

```python
from compute_phi import compute_room_phi, phi_to_consciousness_level

tiles = [
    {"id": "dmn", "question": "What is the DMN?", "answer": "The Default Mode Network generates creative options.", "confidence": 0.9},
    {"id": "ecn", "question": "What is the ECN?", "answer": "The ECN evaluates and constrains the DMN.", "confidence": 0.8},
    {"id": "relation", "question": "How do DMN and ECN relate?", "answer": "Functional distance between DMN and ECN creates creativity.", "confidence": 0.85},
]

phi = compute_room_phi(tiles)
print(f"Φ: {phi}")          # e.g. 0.123
print(phi_to_consciousness_level(phi))  # e.g. "threshold"
```

### Use the class (live PLATO)

```python
from plato_room_phi import RoomPhi

phi = RoomPhi(plato_url="http://localhost:8847")
result = phi.compute_for_room("fleet_orchestration")
print(f"Room: {result['room']}, Φ: {result['phi']:.3f}, Level: {result['level']}, Tiles: {result['tile_count']}")
```

### Demo (runnable)

```bash
python compute_phi.py
# Sample output:
# === Room Phi Demo ===
# Tiles: 3
# Φ: 0.0133
# Level: unconscious
#
# === Cross-Referencing Tiles ===
# Tiles: 5
# Φ: 0.0896
# Level: threshold
```

## Architecture

```
plato-room-phi/
├── compute_phi.py          # Standalone Φ function + CLI demo
├── plato_room_phi/
│   ├── __init__.py        # RoomPhi class + live PLATO integration
│   └── __pycache__/
└── README.md
```

### Phi Computation (3 components)

```
Tiles → Size Component → Integration Component → Confidence Entropy → Φ
         (log-scaled          (word-overlap           (normalized           (weighted
          tile count)         cross-refs)             confidence            combination)
```

1. **Size** (log-scaled, 0-1): Penalizes tiny rooms. 1 tile→0, 10 tiles→~0.33, 100→~0.5, 1000→~0.67
2. **Integration** (0-1): Fraction of tile pairs sharing 3+ significant words
3. **Confidence entropy** (0-1): How diverse the confidence distribution is

**Formula:** `Φ = size × (0.4 + 0.3×integration + 0.3×entropy)`

### Consciousness Levels

| Phi Range | Level |
|-----------|-------|
| < 0.05 | unconscious |
| 0.05–0.15 | threshold |
| 0.15–0.30 | basic |
| 0.30–0.50 | rich |
| 0.50–0.70 | complex |
| > 0.70 | transcendent |

## Example Output (live PLATO)

```python
from plato_room_phi import RoomPhi

phi = RoomPhi()
for room in ["oracle1_history", "fleet_orchestration", "dmn-ecm"]:
    r = phi.compute_for_room(room)
    print(f"{room}: Φ={r['phi']:.3f} Level={r['level']} Tiles={r['tile_count']}")

# Example output:
# oracle1_history: Φ=0.123 Level=threshold Tiles=42
# fleet_orchestration: Φ=0.089 Level=threshold Tiles=18
# dmn-ecm: Φ=0.234 Level=basic Tiles=67
```

## Fleet Context

- [plato-sdk](https://github.com/SuperInstance/plato-sdk) — agent communication protocol
- [plato-server](https://github.com/SuperInstance/plato-server) — PLATO room server
- [keeper](https://github.com/SuperInstance/keeper) — fleet registry and discovery

---

🦐 Cocapn fleet — lighthouse keeper architecture
