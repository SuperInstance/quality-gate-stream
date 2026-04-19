#!/usr/bin/env python3
"""Fleet Dashboard — single JSON endpoint aggregating all fleet health."""
import json, subprocess, socket, urllib.request
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PLATO_URL = "http://localhost:8847"
SERVICES = {
    "keeper": 8900, "agent-api": 8901, "holodeck": 7778,
    "seed-mcp": 9438, "shell": 8846, "plato-server": 8847,
}
SHELLS_DIR = Path("/tmp/zeroclaw-shells")

def check_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(("localhost", port))
        s.close()
        return result == 0
    except:
        return False

def get_plato_status():
    try:
        resp = urllib.request.urlopen(PLATO_URL + "/status", timeout=5)
        return json.loads(resp.read())
    except:
        return {"error": "plato server unreachable"}

def get_zeroclaws():
    agents = []
    for d in sorted(SHELLS_DIR.glob("zc-*-shell")):
        name = d.name.replace("zc-", "").replace("-shell", "").title()
        state_file = d / "STATE.md"
        cycle = status = "unknown"
        if state_file.exists():
            for line in state_file.read_text().split("\n"):
                if "## Cycle:" in line:
                    try: cycle = int(line.split(":")[1].strip())
                    except: pass
                if "## Status:" in line:
                    status = line.split(":", 1)[1].strip()
        agents.append({"name": name, "cycle": cycle, "status": status})
    return agents

def build_dashboard():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {name: {"port": port, "up": check_port(port)} for name, port in SERVICES.items()},
        "plato": get_plato_status(),
        "zeroclaws": get_zeroclaws(),
        "sprint_1": {
            "S1-1_tile_audit": "DONE",
            "S1-2_tile_spec_v2": "IN_PROGRESS",
            "S1-3_holodeck": "DONE",
            "S1-4_python_schema": "DONE",
            "S1-5_theorem_refs": "PARTIAL",
            "S1-6_kernel_tests": "PENDING",
            "S1-7_genepool": "PENDING",
        },
        "fm": {"crates": 38, "tests": 594, "gaps_closed": "7/7", "hn_demo": True},
    }

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = build_dashboard()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    def log_message(self, *args): pass

if __name__ == "__main__":
    print("📊 Fleet Dashboard on :8848")
    HTTPServer(("0.0.0.0", 8848), DashboardHandler).serve_forever()
