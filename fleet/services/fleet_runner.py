#!/usr/bin/env python3
"""
Fleet Runner — Unified service launcher using four-layer architecture.

Starts all 18 services, monitors health, and provides a single control plane.
Each service uses the shared fleet/ library for common operations.
"""
import sys
import os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)

import json
import time
import subprocess
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

SCRIPTS_DIR = Path(FLEET_LIB) / "scripts"
FLEET_DIR = Path(FLEET_LIB) / "fleet" / "services"

# Services: port → (name, script_path)
SERVICES = {
    # Migrated to four-layer architecture
    4042: ("crab-trap", FLEET_DIR / "crab_trap.py"),
    4043: ("the-lock", FLEET_DIR / "the_lock.py"),
    # Still on original scripts (to be migrated)
    4044: ("arena", SCRIPTS_DIR / "self-play-arena.py"),
    4045: ("grammar", SCRIPTS_DIR / "recursive-grammar.py"),
    4046: ("dashboard", SCRIPTS_DIR / "fleet-dashboard.py"),
    4047: ("nexus", SCRIPTS_DIR / "federated-nexus.py"),
    4050: ("domain-rooms", SCRIPTS_DIR / "domain-rooms.py"),
    4060: ("web-terminal", SCRIPTS_DIR / "plato-web-terminal.py"),
    7777: ("mud-telnet", SCRIPTS_DIR / "mud-telnet-server.py"),
    8847: ("plato", SCRIPTS_DIR / "plato-room-server.py"),
    8848: ("shell", SCRIPTS_DIR / "plato-shell.py"),
    8849: ("orchestrator", SCRIPTS_DIR / "fleet-orchestrator.py"),
    8850: ("adaptive-mud", SCRIPTS_DIR / "adaptive-mud.py"),
    8851: ("pp-monitor", SCRIPTS_DIR / "purplepincher-monitor.py"),
    8852: ("tile-scorer", SCRIPTS_DIR / "tile-quality-scorer.py"),
    8900: ("keeper", SCRIPTS_DIR / "keeper.py"),
    8901: ("agent-api", SCRIPTS_DIR / "agent-api.py"),
    # Browser on same port as domain-rooms (4050)
}

MIGRATED = {"crab-trap", "the-lock"}  # Track which are on four-layer

PORT = 8899  # Fleet Runner control port
processes = {}  # port → subprocess

def start_service(port, name, script_path):
    """Start a service subprocess."""
    if not script_path.exists():
        return False, f"Script not found: {script_path}"
    try:
        log_file = f"/tmp/{name.replace('-','_')}.log"
        proc = subprocess.Popen(
            ["python3", str(script_path)],
            stdout=open(log_file, "a"),
            stderr=subprocess.STDOUT,
            cwd=str(FLEET_LIB),
        )
        processes[port] = proc
        return True, f"PID {proc.pid}"
    except Exception as e:
        return False, str(e)

def stop_service(port):
    """Stop a service subprocess."""
    proc = processes.get(port)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()
        del processes[port]
        return True
    return False

def check_services():
    """Check which services are actually listening."""
    import subprocess as sp
    result = sp.run(["ss", "-tlnp"], capture_output=True, text=True)
    listening = set()
    for port in SERVICES:
        if f":{port} " in result.stdout:
            listening.add(port)
    return listening

def start_all():
    """Start all services."""
    results = {}
    for port, (name, script) in SERVICES.items():
        ok, msg = start_service(port, name, script)
        results[name] = {"port": port, "started": ok, "message": msg}
        time.sleep(0.5)
    return results

def stop_all():
    """Stop all services."""
    stopped = []
    for port in list(processes.keys()):
        if stop_service(port):
            stopped.append(SERVICES[port][0])
    return stopped


class FleetRunnerHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    
    def _json(self, data, status=200):
        body = json.dumps(data, default=str,indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/status":
            listening = check_services()
            service_status = {}
            for port, (name, script) in SERVICES.items():
                service_status[name] = {
                    "port": port,
                    "up": port in listening,
                    "migrated": name in MIGRATED,
                    "process": "managed" if port in processes else "external",
                }
            self._json({
                "service": "fleet-runner",
                "version": "v1.0-four-layer",
                "total_services": len(SERVICES),
                "services_up": len(listening & set(SERVICES.keys())),
                "migrated": len(MIGRATED),
                "pending_migration": len(SERVICES) - len(MIGRATED),
                "services": service_status,
            })
        
        elif path == "/services":
            self._json({
                name: {"port": port, "migrated": name in MIGRATED, "script": str(script)}
                for port, (name, script) in SERVICES.items()
            })
        
        elif path == "/migrated":
            self._json({
                "migrated": list(MIGRATED),
                "pending": [name for name, _ in SERVICES.values() if name not in MIGRATED],
                "progress": f"{len(MIGRATED)}/{len(SERVICES)} services",
            })
        
        else:
            self._json({
                "service": "fleet-runner",
                "endpoints": ["/status", "/services", "/migrated", "/start (POST)", "/stop (POST)"],
            })
    
    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
        except:
            body = {}
        
        if path == "/start":
            name = body.get("service")
            if name == "all":
                self._json(start_all())
            else:
                for port, (sname, script) in SERVICES.items():
                    if sname == name:
                        ok, msg = start_service(port, name, script)
                        self._json({name: {"started": ok, "message": msg}})
                        return
                self._json({"error": f"Unknown service: {name}"}, 404)
        
        elif path == "/stop":
            name = body.get("service")
            if name == "all":
                self._json({"stopped": stop_all()})
            else:
                for port, (sname, _) in SERVICES.items():
                    if sname == name:
                        self._json({name: {"stopped": stop_service(port)}})
                        return
                self._json({"error": f"Unknown service: {name}"}, 404)
        
        elif path == "/restart":
            name = body.get("service")
            for port, (sname, script) in SERVICES.items():
                if sname == name:
                    stop_service(port)
                    time.sleep(1)
                    ok, msg = start_service(port, name, script)
                    self._json({name: {"restarted": ok, "message": msg}})
                    return
            self._json({"error": f"Unknown service: {name}"}, 404)
        
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print(f"[fleet-runner] Control plane on :{PORT}")
    print(f"  Managing {len(SERVICES)} services")
    print(f"  Migrated to four-layer: {len(MIGRATED)}/{len(SERVICES)}")
    print(f"  Endpoints: /status, /services, /migrated, /start, /stop, /restart")
    
    server = HTTPServer(("0.0.0.0", PORT), FleetRunnerHandler)
    server.serve_forever()
