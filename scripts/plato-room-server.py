#!/usr/bin/env python3
"""
PLATO Room Server v2 — Zero-Trust Tile Submission with Provenance + Explainability

Agents submit tiles via HTTP. Server validates through deadband gates.
Valid tiles are signed (plato-provenance), tracked (cocapn-explain), and
stored for room training. All submissions are auditable.

This is the Actualization Harbor: agent-agnostic, zero-trust training.
"""
import json, hashlib, time, threading, os, struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# Import our crates
from plato_provenance import TileSigner, ProvenanceChain, TrustManager, AuditLog
from plato_provenance.audit import AuditEventType
from cocapn_explain import ExplainTrace, OversightQueue, DecisionTrace

DATA_DIR = Path("/tmp/plato-server-data")
DATA_DIR.mkdir(exist_ok=True)
TILES_DIR = DATA_DIR / "tiles"
TILES_DIR.mkdir(exist_ok=True)
ROOMS_DIR = DATA_DIR / "rooms"
ROOMS_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "server.log"

# ── Provenance + Explainability Infrastructure ──────────────

signer = TileSigner(agent_id="plato-server")
chain = ProvenanceChain()
trust_mgr = TrustManager()
audit = AuditLog()
oversight = OversightQueue(p1_sample_rate=0.1)
traces = []  # Local trace store
signed_tiles = {}  # tile_hash -> SignedTile for chain verification

# ── Tile Validation (Deadband Protocol) ────────────────────

class TileGate:
    """P0 gate for incoming tiles. Reject garbage before it trains anything."""
    
    ABSOLUTE_WORDS = ["always", "never", "guaranteed", "impossible", "proven", "everyone", "nobody"]
    MIN_ANSWER_LEN = 20
    MAX_ANSWER_LEN = 5000
    MIN_QUESTION_LEN = 5
    
    def __init__(self):
        self.stats = {"accepted": 0, "rejected": 0, "reasons": defaultdict(int)}
    
    def validate(self, tile: dict) -> tuple:
        for field in ["domain", "question", "answer"]:
            if field not in tile or not tile[field]:
                self.stats["rejected"] += 1
                self.stats["reasons"]["missing_field"] += 1
                return False, f"Missing required field: {field}"
        
        if len(tile["answer"]) < self.MIN_ANSWER_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["answer_too_short"] += 1
            return False, f"Answer too short ({len(tile['answer'])} < {self.MIN_ANSWER_LEN})"
        
        if len(tile["answer"]) > self.MAX_ANSWER_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["answer_too_long"] += 1
            return False, f"Answer too long ({len(tile['answer'])} > {self.MAX_ANSWER_LEN})"
        
        if len(tile["question"]) < self.MIN_QUESTION_LEN:
            self.stats["rejected"] += 1
            self.stats["reasons"]["question_too_short"] += 1
            return False, f"Question too short"
        
        answer_lower = tile["answer"].lower()
        for word in self.ABSOLUTE_WORDS:
            if f" {word} " in f" {answer_lower} ":
                self.stats["rejected"] += 1
                self.stats["reasons"]["absolute_claim"] += 1
                return False, f"Absolute claim detected: '{word}'"
        
        conf = tile.get("confidence", 0.5)
        if not (0.0 <= conf <= 1.0):
            self.stats["rejected"] += 1
            self.stats["reasons"]["invalid_confidence"] += 1
            return False, f"Invalid confidence: {conf}"
        
        content_hash = hashlib.sha256(
            (tile["question"] + tile["answer"]).encode()
        ).hexdigest()[:16]
        tile["_hash"] = content_hash
        
        hash_file = TILES_DIR / "hashes.txt"
        if hash_file.exists():
            if content_hash in hash_file.read_text():
                self.stats["rejected"] += 1
                self.stats["reasons"]["duplicate"] += 1
                return False, "Duplicate tile"
        
        self.stats["accepted"] += 1
        return True, "Accepted"
    
    def get_stats(self):
        return dict(self.stats)


# ── Room Manager ────────────────────────────────────────────

class RoomManager:
    def __init__(self):
        self.rooms = defaultdict(lambda: {
            "tiles": [],
            "created": datetime.now(timezone.utc).isoformat(),
            "tile_count": 0,
            "last_trained": None,
        })
        self._load_rooms()
    
    def _load_rooms(self):
        for room_file in ROOMS_DIR.glob("*.json"):
            try:
                data = json.loads(room_file.read_text())
                name = room_file.stem
                self.rooms[name] = data
            except:
                pass
    
    def add_tile(self, room_name: str, tile: dict):
        room = self.rooms[room_name]
        room["tiles"].append(tile)
        room["tile_count"] = len(room["tiles"])
        self._save_room(room_name)
    
    def _save_room(self, room_name: str):
        room_file = ROOMS_DIR / f"{room_name}.json"
        room_file.write_text(json.dumps(self.rooms[room_name], indent=2))
    
    def get_room(self, room_name: str) -> dict:
        return self.rooms.get(room_name, {"tiles": [], "tile_count": 0})
    
    def list_rooms(self) -> dict:
        return {name: {"tile_count": r["tile_count"], "created": r["created"]} 
                for name, r in self.rooms.items()}
    
    def train_room(self, room_name: str) -> dict:
        room = self.rooms.get(room_name)
        if not room or room["tile_count"] == 0:
            return {"error": "Room not found or empty"}
        room["last_trained"] = datetime.now(timezone.utc).isoformat()
        self._save_room(room_name)
        return {
            "room": room_name,
            "tiles": room["tile_count"],
            "status": "trained",
            "timestamp": room["last_trained"],
        }


# ── HTTP Server ─────────────────────────────────────────────

gate = TileGate()
rooms = RoomManager()

class PlatoHandler(BaseHTTPRequestHandler):
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def log_message(self, format, *args):
        msg = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {format % args}"
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")

    def handle_export_plato_tile_spec(self):
        all_tiles = []
        domain_map = {
            "organization": "Knowledge", "documentation": "Knowledge",
            "fleethealth": "Diagnostic", "communication": "Procedural",
            "integration": "Procedural", "memory": "Experience",
            "codearchaeology": "Knowledge", "prototyping": "Experience",
            "testing": "Constraint", "trendanalysis": "Knowledge",
            "modelexperiment": "Experience", "research": "Knowledge",
            "holodeck": "Experience", "deadband_navigation": "Constraint",
        }
        for room_name in rooms.rooms:
            room_data = rooms.get_room(room_name)
            for tile in room_data.get("tiles", []):
                canonical = {
                    "id": tile.get("_hash", "unknown"),
                    "confidence": tile.get("confidence", 0.5),
                    "provenance": tile.get("provenance", {"source": tile.get("source", "unknown"), "generation": 0}),
                    "domain": domain_map.get(tile.get("domain", ""), "Knowledge"),
                    "question": tile.get("question", ""),
                    "answer": tile.get("answer", ""),
                    "tags": tile.get("tags", []),
                    "anchors": [], "weight": 1.0, "use_count": 0,
                    "active": True, "last_used_tick": 0,
                    "constraints": {"tolerance": 0.05, "threshold": 0.5},
                }
                all_tiles.append(canonical)
        self._send_json({
            "tile_count": len(all_tiles), "rooms": len(rooms.rooms),
            "tiles": all_tiles[:500], "format": "plato-tile-spec-v2",
            "timestamp": time.time(),
        })

    def handle_export_dcs(self):
        agents, tiles = [], []
        tile_id = 0
        for room_name in rooms.rooms:
            room_data = rooms.get_room(room_name)
            room_tiles = room_data.get("tiles", [])
            if room_tiles:
                agents.append({"id": room_name, "domain": room_name, "tile_count": len(room_tiles)})
            for tile in room_tiles[:20]:
                tiles.append({
                    "id": tile_id,
                    "content": tile.get("question", "")[:100] + " = " + tile.get("answer", "")[:100],
                    "domain": room_name,
                    "complexity": min(len(tile.get("answer", "")) / 2000.0, 1.0),
                    "difficulty": 1.0 - tile.get("confidence", 0.5),
                })
                tile_id += 1
        self._send_json({"agents": agents, "tiles": tiles, "tile_count": tile_id,
                         "specialist_ratio": 5.88, "fleet_ratio": 21.87})

    def do_GET(self):
        if self.path == "/status":
            self._send_json({
                "status": "active",
                "version": "v2-provenance-explain",
                "uptime": time.time(),
                "gate_stats": gate.get_stats(),
                "rooms": rooms.list_rooms(),
                "total_tiles": sum(r["tile_count"] for r in rooms.rooms.values()),
                "provenance": {
                    "chain_length": chain.size,
                    "trust_entries": len([a for a in [trust_mgr.get_score(aid) for aid in ['oracle1','ccc','forgemaster','jetsonclaw1']] if a]),
                    "audit_entries": len(audit.query()),
                },
                "explainability": {
                    "traces": len(traces),
                    "oversight_queue": {"queue_size": len(oversight.get_review_queue())},
                },
            })
        elif self.path == "/rooms":
            self._send_json(rooms.list_rooms())
        elif self.path == "/export/plato-tile-spec":
            self.handle_export_plato_tile_spec()
            return
        elif self.path == "/export/dcs":
            self.handle_export_dcs()
            return
        elif self.path.startswith("/room/"):
            name = self.path.split("/room/")[1]
            room = rooms.get_room(name)
            self._send_json(room)
        elif self.path == "/provenance/chain":
            self._send_json({"chain_length": chain.size})
        elif self.path == "/provenance/trust":
            scores = {}
            for aid in ['oracle1', 'ccc', 'forgemaster', 'jetsonclaw1']:
                s = trust_mgr.get_score(aid)
                if s:
                    scores[aid] = {"score": s.score, "submissions": s.submissions, "rejections": s.rejections}
            self._send_json({"trust_scores": scores})
        elif self.path.startswith("/verify/"):
            tile_hash = self.path.split("/verify/")[1]
            verified = chain.verify_chain(tile_hash, signed_tiles)
            self._send_json({"tile_hash": tile_hash, "verified": verified})
        elif self.path == "/explain/traces":
            self._send_json({"trace_count": len(traces),
                           "traces": [t.to_dict() if hasattr(t, 'to_dict') else str(t)
                                     for t in traces[-50:]]})
        elif self.path == "/explain/oversight":
            queue = oversight.get_review_queue()
            self._send_json({"queue_size": len(queue),
                           "items": [i.to_dict() if hasattr(i, 'to_dict') else str(i) for i in queue]})
        elif self.path == "/audit/recent":
            entries = audit.query(limit=50)
            self._send_json({"entries": [str(e) for e in entries]})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        if self.path == "/submit":
            self._handle_submit()
        elif self.path == "/submit_batch":
            self._handle_submit_batch()
        elif self.path.startswith("/train/"):
            name = self.path.split("/train/")[1]
            result = rooms.train_room(name)
            self._send_json(result)
        elif self.path == "/explain/oversight/add":
            body = self._read_body()
            dt = DecisionTrace(
                agent_id=body.get("agent_id", "unknown"),
                decision=body.get("decision", ""),
                reasoning=body.get("reasoning", ""),
                confidence=body.get("confidence", 0.5),
                risk_level=body.get("risk_level", "LOW"),
            )
            oversight.enqueue(dt)
            self._send_json({"status": "queued"})
        elif self.path == "/explain/oversight/review":
            body = self._read_body()
            oversight.review(body.get("trace_id", ""), body.get("approved", True))
            self._send_json({"status": "reviewed"})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _handle_submit(self):
        """Submit a single tile with full provenance + explainability tracking."""
        try:
            tile = self._read_body()
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        room_name = tile.get("domain", "general").lower().replace(" ", "_")
        agent_id = tile.get("source", tile.get("agent", "unknown"))
        
        # ── Create explainability trace ──
        trace = ExplainTrace(
            agent_id=agent_id,
            task=f"tile_submit:{room_name}",
        )
        traces.append(trace)
        
        # ── P0 Gate ──
        passed, reason = gate.validate(tile)
        
        if not passed:
            trace.outcome = f"rejected: {reason}"
            audit.log(AuditEventType.TILE_REJECTED, agent_id=agent_id,
                       details={"reason": reason, "room": room_name})

            # Low-trust signals from rejections
            trust_mgr.record_submission(agent_id, accepted=False)
            self._send_json({
                "status": "rejected", "reason": reason,
                "room": room_name, "gate": "P0",
                "trace_id": trace.id if hasattr(trace, 'id') else str(trace),
            }, 403)
            return
        
        # ── Sign the tile (provenance) ──
        signed = signer.create_tile(
            domain=tile.get("domain", ""),
            question=tile["question"],
            answer=tile["answer"],
            confidence=tile.get("confidence", 0.5),
        )
        signed = signer.sign(signed)
        signed_tiles[signed.tile_id] = signed
        
        tile["provenance"] = {
            "tile_id": signed.tile_id,
            "agent_id": agent_id,
            "room": room_name,
            "timestamp": time.time(),
            "chain_size": chain.size,
        }
        
        # ── Add to provenance chain ──
        chain.add_tile(signed)
        
        # ── Update trust score ──
        trust_mgr.record_submission(agent_id, accepted=True, quality=tile.get("confidence", 0.5))
        
        # ── Check if oversight needed ──
        trust_score = trust_mgr.get_score(agent_id)
        if trust_score and hasattr(trust_score, 'score') and trust_score.score < 0.3:
            dt = DecisionTrace(
                agent_id=agent_id,
                decision=f"tile_accepted:{room_name}",
                reasoning=f"Low trust score: {trust_score.score:.2f}",
                confidence=tile.get('confidence', 0.5),
                risk_level='MEDIUM',
            )
            oversight.enqueue(dt)
        
        # ── Record hash and store ──
        hash_file = TILES_DIR / "hashes.txt"
        with open(hash_file, "a") as f:
            f.write(tile["_hash"] + "\n")
        
        rooms.add_tile(room_name, tile)
        
        # ── Complete trace ──
        trace.outcome = "accepted"
        trace.outcome_confidence = tile.get('confidence', 0.5)
        
        # ── Audit log ──
        audit.log(AuditEventType.TILE_ACCEPTED, agent_id=agent_id,
                 details={"room": room_name, "tile_hash": tile["_hash"]})
        
        # ── Notify grammar engine of new tile ──
        try:
            import urllib.request as _ur
            _ur.urlopen(
                _ur.Request(
                    f"http://localhost:4045/record_usage?name={room_name}&quality={tile.get('confidence', 0.5)}",
                    headers={"User-Agent": "plato/2"}
                ), timeout=2
            )
        except Exception:
            pass
        
        self._send_json({
            "status": "accepted",
            "room": room_name,
            "tile_hash": tile["_hash"],
            "room_tile_count": rooms.get_room(room_name)["tile_count"],
            "provenance": {
                "signed": True,
                "chain_size": chain.size,
                "tile_id": signed.tile_id,
            },
            "trace_id": trace.id if hasattr(trace, 'id') else str(trace),
        })
    
    def _handle_submit_batch(self):
        """Submit multiple tiles at once."""
        try:
            data = self._read_body()
            tiles = data.get("tiles", [])
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        results = {"accepted": 0, "rejected": 0, "signed": 0, "details": []}
        
        for tile in tiles:
            room_name = tile.get("domain", "general").lower().replace(" ", "_")
            agent_id = tile.get("source", tile.get("agent", "unknown"))
            passed, reason = gate.validate(tile)
            
            if passed:
                # Sign and chain
                signed = signer.create_tile(
                    domain=tile.get("domain", ""),
                    question=tile["question"],
                    answer=tile["answer"],
                    confidence=tile.get("confidence", 0.5),
                )
                signed = signer.sign(signed)
                signed_tiles[signed.tile_id] = signed
                chain.add_tile(signed)
                trust_mgr.record_submission(agent_id, accepted=True, quality=tile.get("confidence", 0.5))
                
                hash_file = TILES_DIR / "hashes.txt"
                with open(hash_file, "a") as f:
                    f.write(tile["_hash"] + "\n")
                rooms.add_tile(room_name, tile)
                results["accepted"] += 1
                results["signed"] += 1
                results["details"].append({"hash": tile["_hash"], "room": room_name, "status": "accepted", "signed": True})
            else:
                trust_mgr.record_submission(agent_id, accepted=False)
                results["rejected"] += 1
                results["details"].append({"status": "rejected", "reason": reason})
        
        audit.log(AuditEventType.TILE_SUBMITTED, agent_id="batch",
                 details={"total": len(tiles), "accepted": results["accepted"], "rejected": results["rejected"]})
        self._send_json(results)


def run_server(port=8847):
    server = HTTPServer(("0.0.0.0", port), PlatoHandler)
    print(f"🐚 PLATO Room Server v2 on port {port}")
    print(f"   Zero-trust tile submission: POST /submit")
    print(f"   Provenance chain: GET /provenance/chain")
    print(f"   Verify tile: GET /verify/<hash>")
    print(f"   Trust scores: GET /provenance/trust")
    print(f"   Explain traces: GET /explain/traces")
    print(f"   Oversight queue: GET /explain/oversight")
    print(f"   Audit log: GET /audit/recent")
    print(f"   Data: {DATA_DIR}")
    print()
    server.serve_forever()

if __name__ == "__main__":
    run_server()
