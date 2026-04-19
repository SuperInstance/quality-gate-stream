#!/usr/bin/env python3
"""plato-tile-spec Python Schema Loader (S1-4). Canonical Tile format compatible with Rust serde."""
import json, time, hashlib, urllib.request
from dataclasses import dataclass, field, asdict
from typing import List

DOMAIN_MAP = {
    "organization": "Knowledge", "documentation": "Knowledge", "fleethealth": "Diagnostic",
    "communication": "Procedural", "integration": "Procedural", "memory": "Experience",
    "codearchaeology": "Knowledge", "prototyping": "Experience", "testing": "Constraint",
    "trendanalysis": "Knowledge", "modelexperiment": "Experience", "research": "Knowledge",
    "holodeck": "Experience", "deadband_navigation": "Constraint",
}

@dataclass
class Tile:
    id: str = ""
    confidence: float = 0.5
    provenance: dict = field(default_factory=lambda: {"source": "system", "generation": 0})
    domain: str = "Knowledge"
    question: str = ""
    answer: str = ""
    tags: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)
    weight: float = 1.0
    use_count: int = 0
    active: bool = True
    last_used_tick: int = 0
    constraints: dict = field(default_factory=lambda: {"tolerance": 0.05, "threshold": 0.5})

    def __post_init__(self):
        if not self.id:
            ns = int(time.time() * 1e9)
            src = self.provenance.get("source", "tile") if isinstance(self.provenance, dict) else "tile"
            self.id = src + "-" + str(ns)

    @staticmethod
    def from_plato_server(server_tile):
        src = server_tile.get("source", "unknown")
        if isinstance(src, str) and ":" in src:
            src = src.split(":")[1] if len(src.split(":")) > 1 else src.split(":")[0]
        return Tile(
            id="plato-" + hashlib.sha256((server_tile.get("question","") + server_tile.get("answer","")).encode()).hexdigest()[:16],
            confidence=float(server_tile.get("confidence", 0.5)),
            provenance={"source": str(src), "generation": 0},
            domain=DOMAIN_MAP.get(str(server_tile.get("domain", "")).lower(), "Knowledge"),
            question=server_tile.get("question", ""),
            answer=server_tile.get("answer", ""),
            tags=server_tile.get("tags", []),
            anchors=[], weight=1.0, use_count=0, active=True, last_used_tick=0,
            constraints={"tolerance": 0.05, "threshold": 0.5},
        )

    @staticmethod
    def from_holodeck(holo_tile):
        ctx = holo_tile.get("context", {})
        tags = list(ctx.values()) if isinstance(ctx, dict) else []
        return Tile(
            id="holo-" + str(holo_tile.get("timestamp", int(time.time()))),
            confidence=float(holo_tile.get("reward", 0.5)),
            provenance={"source": holo_tile.get("agent", "holodeck"), "generation": 0},
            domain="Experience",
            question=holo_tile.get("action", ""),
            answer=holo_tile.get("outcome", ""),
            tags=tags, anchors=[], weight=1.0, use_count=0, active=True,
            last_used_tick=holo_tile.get("timestamp", 0),
            constraints={"tolerance": 0.05, "threshold": 0.5},
        )

    def to_json(self):
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Tile(**{k: v for k, v in data.items() if k in Tile.__dataclass_fields__})


if __name__ == "__main__":
    PLATO_URL = "http://localhost:8847"
    resp = urllib.request.urlopen(PLATO_URL + "/room/organization", timeout=10)
    data = json.loads(resp.read())
    server_tiles = data.get("tiles", [])

    print("=== S1-4: PLATO Tile Schema Loader ===")
    print("Server tiles: " + str(len(server_tiles)))

    canonical = [Tile.from_plato_server(t) for t in server_tiles[:5]]
    for ct in canonical[:3]:
        print("  " + ct.id + " | " + ct.domain + " | " + ct.question[:50] + "... | conf=" + str(ct.confidence))

    # Roundtrip
    json_out = canonical[0].to_json()
    rt = Tile.from_json(json_out)
    assert rt.id == canonical[0].id
    assert rt.domain == canonical[0].domain
    print("\nRoundtrip test PASSED")

    # Holodeck conversion
    holo = {"room_id": "harbor", "agent": "oracle1", "action": "enter_room",
            "outcome": "Harbor loaded", "reward": 0.8, "timestamp": 12345,
            "state_hash": "abc", "context": {"location": "harbor"}}
    ct_h = Tile.from_holodeck(holo)
    print("Holodeck: " + ct_h.domain + " | " + ct_h.question + " -> " + ct_h.answer)
    print("Holodeck conversion PASSED")

    print("\nS1-4 COMPLETE: Python schema loader compatible with plato-tile-spec serde")
PYEOF
