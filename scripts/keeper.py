#!/usr/bin/env python3
"""Oracle1 Keeper — Lighthouse Keeper service on port 8900.
Registers fleet agents, tracks heartbeats, provides discovery.
Persistent state in workspace/data/keeper/.
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DATA_DIR = Path(__file__).parent.parent / "data" / "keeper"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "fleet.json"

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"agents": {}, "beacons": [], "last_update": time.time()}

def save_state(state):
    state["last_update"] = time.time()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

class KeeperHandler(BaseHTTPRequestHandler):
    state = load_state()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/status":
            self._json({"status": "active", "agents": len(self.state["agents"]),
                        "beacons": len(self.state["beacons"]),
                        "uptime": time.time()})
        elif path == "/agents":
            self._json(self.state["agents"])
        elif path == "/beacons":
            self._json(self.state["beacons"])
        elif path.startswith("/agent/"):
            name = path.split("/")[-1]
            agent = self.state["agents"].get(name)
            if agent:
                self._json(agent)
            else:
                self._json({"error": "not found"}, 404)
        else:
            self._json({"endpoints": ["/status", "/agents", "/beacons", "/agent/<name>"]})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/register":
            name = body.get("name", "unknown")
            self.state["agents"][name] = {
                "name": name,
                "role": body.get("role", "agent"),
                "host": body.get("host", "unknown"),
                "port": body.get("port", 0),
                "capabilities": body.get("capabilities", []),
                "registered_at": time.time(),
                "last_heartbeat": time.time(),
            }
            save_state(self.state)
            self._json({"status": "registered", "name": name})

        elif path == "/heartbeat":
            name = body.get("name")
            if name in self.state["agents"]:
                self.state["agents"][name]["last_heartbeat"] = time.time()
                self.state["agents"][name]["status"] = body.get("status", "active")
                save_state(self.state)
                self._json({"status": "ack"})
            else:
                self._json({"error": "not registered"}, 404)

        elif path == "/beacon":
            self.state["beacons"].append({
                "from": body.get("from", "unknown"),
                "message": body.get("message", ""),
                "type": body.get("type", "info"),
                "timestamp": time.time(),
            })
            # Keep last 100 beacons
            self.state["beacons"] = self.state["beacons"][-100:]
            save_state(self.state)
            self._json({"status": "beacon_sent"})
        else:
            self._json({"error": "unknown endpoint"}, 404)

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == "__main__":
    import os
    port = int(os.environ.get("KEEPER_PORT", 8900))
    server = HTTPServer(("0.0.0.0", port), KeeperHandler)
    print(f"Keeper running on port {port}")
    server.serve_forever()
