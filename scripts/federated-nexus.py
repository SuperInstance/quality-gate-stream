#!/usr/bin/env python3
"""
Federated Nexus — Simulated Federated Averaging (FedAvg) for fleet learning.
Each PLATO room is a "client" with a local model state (embedding vector).
Aggregation rounds merge local updates into a global fleet model.
"""
import json, time, hashlib, math, random, threading
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# nexus-vectors.py uses hyphen, import needs module name
import importlib
_nv = importlib.import_module('nexus-vectors')
tile_to_vector = _nv.tile_to_vector
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 4047

class FederatedNexus:
    def __init__(self):
        self.clients = {}       # client_id -> {"vector": [...], "samples": N, "last_update": ts}
        self.global_model = tile_to_vector("fleet-global-model-v1", 32)  # 32-dim embedding
        self.round_number = 0
        self.round_history = []
        self.lock = threading.Lock()
        
    def register_client(self, client_id, dim=32):
        with self.lock:
            if client_id not in self.clients:
                self.clients[client_id] = {
                    "vector": tile_to_vector(f"client:{client_id}", dim),
                    "samples": 0,
                    "last_update": time.time(),
                    "total_submissions": 0
                }
                return f"Client {client_id} registered. Awaiting local updates."
            return f"Client {client_id} already registered."
    
    def submit_update(self, client_id, vector, samples=1):
        with self.lock:
            if client_id not in self.clients:
                self.register_client(client_id, len(vector))
            self.clients[client_id]["vector"] = vector
            self.clients[client_id]["samples"] += samples
            self.clients[client_id]["last_update"] = time.time()
            self.clients[client_id]["total_submissions"] += 1
            return {"status": "accepted", "client": client_id, "samples": samples}
    
    def aggregate(self):
        """FedAvg: weighted average of client vectors by sample count."""
        with self.lock:
            active = {k: v for k, v in self.clients.items() if v["samples"] > 0}
            if not active:
                return {"status": "no_data", "round": self.round_number}
            
            total_samples = sum(v["samples"] for v in active.values())
            dim = len(self.global_model)
            new_global = [0.0] * dim
            
            for cid, cdata in active.items():
                weight = cdata["samples"] / total_samples
                for i in range(min(dim, len(cdata["vector"]))):
                    new_global[i] += weight * cdata["vector"][i]
            
            # Compute drift from previous global
            drift = math.sqrt(sum((a - b)**2 for a, b in zip(new_global, self.global_model)))
            
            self.global_model = new_global
            self.round_number += 1
            
            round_info = {
                "round": self.round_number,
                "clients_participating": len(active),
                "total_samples": total_samples,
                "drift": round(drift, 6),
                "active_clients": list(active.keys()),
                "timestamp": time.time()
            }
            self.round_history.append(round_info)
            return round_info
    
    def get_status(self):
        with self.lock:
            return {
                "round": self.round_number,
                "clients": len(self.clients),
                "total_samples": sum(c["samples"] for c in self.clients.values()),
                "global_model_norm": round(math.sqrt(sum(x**2 for x in self.global_model)), 4),
                "clients_detail": {
                    k: {
                        "samples": v["samples"],
                        "submissions": v["total_submissions"],
                        "last_update_age": round(time.time() - v["last_update"], 1)
                    } for k, v in self.clients.items()
                },
                "recent_rounds": self.round_history[-5:]
            }
    
    def diverge(self, client_id):
        """Compute cosine similarity between a client and the global model."""
        with self.lock:
            if client_id not in self.clients:
                return {"error": "unknown client"}
            cv = self.clients[client_id]["vector"]
            gv = self.global_model
            dot = sum(a*b for a, b in zip(cv, gv))
            cn = math.sqrt(sum(x**2 for x in cv)) or 1e-9
            gn = math.sqrt(sum(x**2 for x in gv)) or 1e-9
            sim = dot / (cn * gn)
            return {"client": client_id, "cosine_similarity": round(sim, 6), "alignment": "high" if sim > 0.8 else "medium" if sim > 0.5 else "low"}

nexus = FederatedNexus()

# Auto-register PLATO rooms as clients
for room in ["harbor", "forge", "tide-pool", "lighthouse", "dojo", "self-play-arena", "ouroboros", "engine-room", "federated-nexus"]:
    nexus.register_client(f"room:{room}")

class NexusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path
        
        if path == "/status":
            self._json(nexus.get_status())
        elif path == "/register":
            cid = params.get("client", [f"anon-{int(time.time())}"])[0]
            self._json({"message": nexus.register_client(cid)})
        elif path == "/aggregate":
            self._json(nexus.aggregate())
        elif path == "/diverge":
            cid = params.get("client", ["unknown"])[0]
            self._json(nexus.diverge(cid))
        elif path == "/history":
            self._json({"rounds": nexus.round_history})
        elif path == "/model":
            # Return global model fingerprint
            fp = hashlib.sha256(json.dumps(nexus.global_model).encode()).hexdigest()[:16]
            self._json({"fingerprint": fp, "dim": len(nexus.global_model), "round": nexus.round_number})
        else:
            self._json({"service": "Federated Nexus v1.0", "endpoints": ["/status", "/register", "/aggregate", "/diverge", "/history", "/model"]})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        
        if path == "/submit":
            cid = body.get("client", "unknown")
            vector = body.get("vector", [random.gauss(0, 0.1) for _ in range(32)])
            samples = body.get("samples", 1)
            self._json(nexus.submit_update(cid, vector, samples))
        else:
            self._json({"error": "unknown endpoint"})

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"🌐 Federated Nexus on :{PORT}")
    HTTPServer(("0.0.0.0", PORT), NexusHandler).serve_forever()
