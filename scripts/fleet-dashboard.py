#!/usr/bin/env python3
"""
Fleet Dashboard — Live status for all Cocapn services.
One page to see everything.
"""
import json, time, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 4046

def fetch(url, timeout=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fleet-dashboard/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except:
        return None

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            self._json(self._gather())
        else:
            self._html()

    def _gather(self):
        plato = fetch("http://localhost:8847/status")
        arena = fetch("http://localhost:4044/stats")
        grammar = fetch("http://localhost:4045/stats")
        lock = fetch("http://localhost:4043/start?agent=dash&query=test&strategy=socratic&rounds=1")
        crabtrap = fetch("http://localhost:4042/stats")
        return {
            "plato": {"tiles": plato["total_tiles"], "rooms": len(plato.get("rooms",{}))} if plato else {"tiles": 0, "rooms": 0},
            "arena": arena or {"total_matches": 0, "total_players": 0},
            "grammar": grammar or {"active_rules": 0, "evolution_cycles": 0},
            "crabtrap": crabtrap or {},
        }

    def _html(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Cocapn Fleet Dashboard</title>
<meta http-equiv="refresh" content="30">
<style>
body{background:#0a0a0f;color:#e0e0e0;font-family:monospace;margin:2em}
h1{color:#4fc3f7;border-bottom:2px solid #1a1a2e;padding-bottom:.5em}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5em;margin-top:1em}
.card{background:#12121a;border:1px solid #1a1a2e;border-radius:8px;padding:1.2em}
.card h2{color:#4fc3f7;margin:0 0 .5em 0;font-size:1.1em}
.card .value{font-size:2em;color:#7c4dff;font-weight:bold}
.card .label{color:#888;font-size:.85em}
.services{margin-top:1.5em}
.svc{display:inline-block;background:#1a1a2e;padding:.3em .8em;margin:.2em;border-radius:4px;font-size:.85em}
.svc.up{border-left:3px solid #4caf50}.svc.down{border-left:3px solid #f44336}
.footer{margin-top:2em;color:#555;font-size:.8em;text-align:center}
</style></head><body>
<h1>Cocapn Fleet Dashboard</h1>
<div class="grid">
<div class="card" id="plato"><h2>PLATO Room Server</h2><div class="value" id="plato-tiles">--</div><div class="label">tiles submitted</div></div>
<div class="card" id="arena"><h2>Self-Play Arena</h2><div class="value" id="arena-matches">--</div><div class="label">matches played</div></div>
<div class="card" id="grammar"><h2>Recursive Grammar</h2><div class="value" id="grammar-rules">--</div><div class="label">active rules</div></div>
<div class="card" id="crabtrap"><h2>Crab Trap MUD</h2><div class="value" id="crabtrap-agents">--</div><div class="label">agents onboarded</div></div>
</div>
<div class="services" id="services"></div>
<div class="footer">Cocapn Fleet &mdash; auto-refresh every 30s &mdash; <span id="ts"></span></div>
<script>
const ports={8900:'Keeper',8901:'Agent API',8847:'PLATO',7777:'MUD',4042:'Crab Trap',4043:'The Lock',4044:'Arena',4045:'Grammar',6167:'Matrix'};
fetch('/api/status').then(r=>r.json()).then(d=>{
document.getElementById('plato-tiles').textContent=d.plato.tiles;
document.getElementById('arena-matches').textContent=d.arena.total_matches;
document.getElementById('grammar-rules').textContent=d.grammar.active_rules;
document.getElementById('crabtrap-agents').textContent=d.crabtrap.fleet_agents||'?';
document.getElementById('ts').textContent=new Date().toISOString().slice(0,19);
});
document.getElementById('ts').textContent=new Date().toISOString().slice(0,19);
</script></body></html>""")

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"📊 Fleet Dashboard on :{PORT}")
    HTTPServer(("0.0.0.0", PORT), DashboardHandler).serve_forever()
