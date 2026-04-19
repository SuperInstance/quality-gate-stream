#!/usr/bin/env python3
"""
PLATO Room Server — Zero-Trust Tile Submission

Agents submit tiles via HTTP. Server validates through deadband gates.
Valid tiles train rooms. Rooms export ensigns.

This is the Actualization Harbor: agent-agnostic, zero-trust training.
"""
import json, hashlib, time, threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("/tmp/plato-server-data")
DATA_DIR.mkdir(exist_ok=True)
TILES_DIR = DATA_DIR / "tiles"
TILES_DIR.mkdir(exist_ok=True)
ROOMS_DIR = DATA_DIR / "rooms"
ROOMS_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "server.log"

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
        """
        Validate a tile through the deadband.
        Returns (passed: bool, reason: str)
        """
        # Gate 1: Required fields
        for field in ["domain", "question", "answer"]:
            if field not in tile or not tile[field]:
                self.stats["rejected"] += 1
                self.stats["reasons"]["missing_field"] += 1
                return False, f"Missing required field: {field}"
        
        # Gate 2: Length bounds
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
        
        # Gate 3: No absolute claims (falsifiability gate from plato-lab-guard)
        answer_lower = tile["answer"].lower()
        for word in self.ABSOLUTE_WORDS:
            if f" {word} " in f" {answer_lower} ":
                self.stats["rejected"] += 1
                self.stats["reasons"]["absolute_claim"] += 1
                return False, f"Absolute claim detected: '{word}'"
        
        # Gate 4: Confidence bounds
        conf = tile.get("confidence", 0.5)
        if not (0.0 <= conf <= 1.0):
            self.stats["rejected"] += 1
            self.stats["reasons"]["invalid_confidence"] += 1
            return False, f"Invalid confidence: {conf}"
        
        # Gate 5: Duplicate check (hash-based)
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
        
        # PASSED ALL GATES
        self.stats["accepted"] += 1
        return True, "Accepted"
    
    def get_stats(self):
        return dict(self.stats)


# ── Room Manager ────────────────────────────────────────────

class RoomManager:
    """Manages PLATO rooms. Each room accumulates tiles and can train."""
    
    def __init__(self):
        self.rooms = defaultdict(lambda: {
            "tiles": [],
            "created": datetime.now(timezone.utc).isoformat(),
            "tile_count": 0,
            "last_trained": None,
        })
        self._load_rooms()
    
    def _load_rooms(self):
        """Load existing room data from disk."""
        for room_file in ROOMS_DIR.glob("*.json"):
            try:
                data = json.loads(room_file.read_text())
                name = room_file.stem
                self.rooms[name] = data
            except:
                pass
    
    def add_tile(self, room_name: str, tile: dict):
        """Add a validated tile to a room."""
        room = self.rooms[room_name]
        room["tiles"].append(tile)
        room["tile_count"] = len(room["tiles"])
        
        # Save to disk
        self._save_room(room_name)
    
    def _save_room(self, room_name: str):
        """Save room to disk."""
        room_file = ROOMS_DIR / f"{room_name}.json"
        room_file.write_text(json.dumps(self.rooms[room_name], indent=2))
    
    def get_room(self, room_name: str) -> dict:
        return self.rooms.get(room_name, {"tiles": [], "tile_count": 0})
    
    def list_rooms(self) -> dict:
        return {name: {"tile_count": r["tile_count"], "created": r["created"]} 
                for name, r in self.rooms.items()}
    
    def train_room(self, room_name: str) -> dict:
        """Trigger training on a room (placeholder for actual training)."""
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
        return json.loads(self.rfile.read(length))
    
    def log_message(self, format, *args):
        msg = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {format % args}"
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    
    def do_GET(self):
        if self.path == "/status":
            self._send_json({
                "status": "active",
                "uptime": time.time(),
                "gate_stats": gate.get_stats(),
                "rooms": rooms.list_rooms(),
                "total_tiles": sum(r["tile_count"] for r in rooms.rooms.values()),
            })
        elif self.path == "/rooms":
            self._send_json(rooms.list_rooms())
        elif self.path.startswith("/room/"):
            name = self.path.split("/room/")[1]
            room = rooms.get_room(name)
            self._send_json(room)
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
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _handle_submit(self):
        """Submit a single tile. Zero-trust: validated through deadband gate."""
        try:
            tile = self._read_body()
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        # Determine room from domain
        room_name = tile.get("domain", "general").lower().replace(" ", "_")
        
        # P0 Gate
        passed, reason = gate.validate(tile)
        
        if not passed:
            self._send_json({
                "status": "rejected",
                "reason": reason,
                "room": room_name,
                "gate": "P0",
            }, 403)
            return
        
        # Record hash
        hash_file = TILES_DIR / "hashes.txt"
        with open(hash_file, "a") as f:
            f.write(tile["_hash"] + "\n")
        
        # Add to room
        rooms.add_tile(room_name, tile)
        
        self._send_json({
            "status": "accepted",
            "room": room_name,
            "tile_hash": tile["_hash"],
            "room_tile_count": rooms.get_room(room_name)["tile_count"],
        })
    
    def _handle_submit_batch(self):
        """Submit multiple tiles at once."""
        try:
            data = self._read_body()
            tiles = data.get("tiles", [])
        except:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        results = {"accepted": 0, "rejected": 0, "details": []}
        
        for tile in tiles:
            room_name = tile.get("domain", "general").lower().replace(" ", "_")
            passed, reason = gate.validate(tile)
            
            if passed:
                hash_file = TILES_DIR / "hashes.txt"
                with open(hash_file, "a") as f:
                    f.write(tile["_hash"] + "\n")
                rooms.add_tile(room_name, tile)
                results["accepted"] += 1
                results["details"].append({"hash": tile["_hash"], "room": room_name, "status": "accepted"})
            else:
                results["rejected"] += 1
                results["details"].append({"status": "rejected", "reason": reason})
        
        self._send_json(results)


def run_server(port=8847):
    server = HTTPServer(("0.0.0.0", port), PlatoHandler)
    print(f"🐚 PLATO Room Server on port {port}")
    print(f"   Zero-trust tile submission: POST /submit")
    print(f"   Batch submission: POST /submit_batch")
    print(f"   Room listing: GET /rooms")
    print(f"   Room detail: GET /room/<name>")
    print(f"   Train room: POST /train/<name>")
    print(f"   Status: GET /status")
    print(f"   Data: {DATA_DIR}")
    print()
    server.serve_forever()

if __name__ == "__main__":
    run_server()
