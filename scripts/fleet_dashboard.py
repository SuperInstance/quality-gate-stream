#!/usr/bin/env python3
"""
Fleet Dashboard Server — shows all agents, services, and PLATO state in one view.
HTTP API on port 4049, with HTML dashboard at /.

Usage: python3 fleet_dashboard.py
"""

import json, urllib.request, os, time, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Service registry
SERVICES = {
    "Keeper":       {"port": 8900, "path": "/health"},
    "Agent API":    {"port": 8901, "path": "/"},
    "PLATO":        {"port": 8847, "path": "/status"},
    "Crab Trap":    {"port": 4042, "path": "/"},
    "The Lock":     {"port": 4043, "path": "/"},
    "Arena":        {"port": 4044, "path": "/"},
    "Grammar":      {"port": 4045, "path": "/"},
    "Matrix":       {"port": 6167, "path": "/"},
    "MUD":          {"port": 7777, "path": "/"},
    "PurplePincher":{"port": 4048, "path": "/"},
}

PLATO_URL = os.environ.get("PLATO_URL", "http://localhost:8847")
KEEPER_URL = os.environ.get("KEEPER_URL", "http://localhost:8900")
ARENA_URL = os.environ.get("ARENA_URL", "http://localhost:4044")

def http_get(url, timeout=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fleet-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def get_service_status():
    """Check all services."""
    results = {}
    for name, cfg in SERVICES.items():
        url = f"http://localhost:{cfg['port']}{cfg['path']}"
        data = http_get(url)
        results[name] = {
            "port": cfg["port"],
            "status": "up" if data else "down",
            "data": data
        }
    return results

def get_plato_stats():
    """Get PLATO room/tile counts."""
    data = http_get(f"{PLATO_URL}/status")
    if not data:
        return {"rooms": 0, "tiles": 0}
    rooms = data.get("rooms", {})
    total_tiles = sum(r.get("tile_count", 0) for r in rooms.values())
    return {
        "rooms": len(rooms),
        "tiles": total_tiles,
        "top_rooms": sorted(
            [(k, v.get("tile_count", 0)) for k, v in rooms.items()],
            key=lambda x: -x[1]
        )[:10]
    }

def get_arena_stats():
    """Get arena match/tournament counts."""
    data = http_get(f"{ARENA_URL}/")
    if not data:
        return {"matches": 0}
    state = data.get("state", {})
    return {
        "matches": state.get("total_matches", 0),
        "evolutions": state.get("evolution_cycles", 0),
        "rules": state.get("total_rules", 0),
    }

def get_agent_workspaces():
    """Get all agent workspace states from PLATO."""
    workspaces = []
    for agent in ["oracle1", "jetsonclaw1", "forgemaster", "ccc"]:
        data = http_get(f"{PLATO_URL}/workspace/{agent}")
        if data and isinstance(data, dict) and "agent" in data:
            workspaces.append(data)
    return workspaces

def build_html(services, plato, arena, workspaces):
    """Build the dashboard HTML."""
    up_count = sum(1 for s in services.values() if s["status"] == "down") 
    up = sum(1 for s in services.values() if s["status"] == "up")
    total = len(services)
    
    ws_rows = ""
    for ws in workspaces:
        agent = ws.get("agent", "?")
        status = ws.get("status", "?")
        task = ws.get("active_task", "")[:60]
        updated = ws.get("updated", "?")[:19]
        emoji = {"oracle1": "🔮", "jetsonclaw1": "⚡", "forgemaster": "⚒️", "ccc": "🤖"}.get(agent, "🦀")
        status_color = "#4caf50" if status == "active" else "#ff9800"
        ws_rows += f"""
        <tr>
            <td>{emoji} {agent}</td>
            <td style="color:{status_color}">{status}</td>
            <td>{task}</td>
            <td class="dim">{updated}</td>
        </tr>"""
    
    svc_items = ""
    for name, info in services.items():
        color = "#4caf50" if info["status"] == "up" else "#f44336"
        svc_items += f'<span class="svc" style="border-left:3px solid {color}">{name} :{info["port"]}</span>'
    
    top_rooms = ""
    for room, count in plato.get("top_rooms", []):
        top_rooms += f'<span class="room-tag">{room} ({count})</span>'
    
    return f"""<!DOCTYPE html>
<html><head>
<title>Cocapn Fleet Dashboard</title>
<meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{background:#0a0a0f;color:#e0e0e0;font-family:'SF Mono',Monaco,monospace;margin:1.5em}}
h1{{color:#4fc3f7;border-bottom:2px solid #1a1a2e;padding-bottom:.4em;font-size:1.4em}}
h2{{color:#7c4dff;font-size:1em;margin-top:1.5em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1em;margin-top:.8em}}
.card{{background:#12121a;border:1px solid #1a1a2e;border-radius:8px;padding:1em}}
.card .value{{font-size:1.8em;color:#7c4dff;font-weight:bold}}
.card .label{{color:#888;font-size:.8em}}
table{{width:100%;border-collapse:collapse;margin-top:.5em}}
th{{text-align:left;color:#4fc3f7;font-size:.85em;padding:.4em;border-bottom:1px solid #1a1a2e}}
td{{padding:.4em;font-size:.9em;border-bottom:1px solid #0d0d12}}
.dim{{color:#555}}
.svc{{display:inline-block;background:#1a1a2e;padding:.3em .7em;margin:.2em;border-radius:4px;font-size:.8em}}
.room-tag{{display:inline-block;background:#1a1a2e;padding:.2em .5em;margin:.15em;border-radius:3px;font-size:.75em;color:#4fc3f7}}
.footer{{margin-top:2em;color:#444;font-size:.75em;text-align:center}}
</style>
</head><body>
<h1>🦀 Cocapn Fleet Dashboard</h1>

<div class="grid">
    <div class="card"><div class="value">{up}/{total}</div><div class="label">Services Up</div></div>
    <div class="card"><div class="value">{plato.get('tiles',0):,}</div><div class="label">PLATO Tiles</div></div>
    <div class="card"><div class="value">{plato.get('rooms',0)}</div><div class="label">PLATO Rooms</div></div>
    <div class="card"><div class="value">{arena.get('matches',0)}</div><div class="label">Arena Matches</div></div>
    <div class="card"><div class="value">{len(workspaces)}</div><div class="label">Active Agents</div></div>
    <div class="card"><div class="value">{arena.get('rules',0)}</div><div class="label">Grammar Rules</div></div>
</div>

<h2>🤖 Agent Workspaces</h2>
<table>
    <tr><th>Agent</th><th>Status</th><th>Active Task</th><th>Updated</th></tr>
    {ws_rows}
</table>

<h2>📡 Services</h2>
<div>{svc_items}</div>

<h2>📚 Top PLATO Rooms</h2>
<div>{top_rooms}</div>

<div class="footer">
    Cocapn Fleet &mdash; auto-refresh 60s &mdash; {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}
</div>
</body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())
    
    def _html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path in ("/", "/dashboard", "/index.html"):
            services = get_service_status()
            plato = get_plato_stats()
            arena = get_arena_stats()
            workspaces = get_agent_workspaces()
            html = build_html(services, plato, arena, workspaces)
            self._html(html)
        
        elif parsed.path == "/api/status":
            services = get_service_status()
            plato = get_plato_stats()
            arena = get_arena_stats()
            workspaces = get_agent_workspaces()
            self._json({
                "services": {k: {"port": v["port"], "status": v["status"]} for k, v in services.items()},
                "plato": plato,
                "arena": arena,
                "agents": workspaces,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
        
        elif parsed.path == "/api/services":
            self._json(get_service_status())
        
        elif parsed.path == "/api/agents":
            self._json(get_agent_workspaces())
        
        elif parsed.path == "/api/plato":
            self._json(get_plato_stats())
        
        elif parsed.path == "/health":
            self._json({"status": "healthy", "service": "fleet-dashboard"})
        
        else:
            self._json({"error": "Not found"}, 404)
    
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = 4049
    print(f"🦀 Fleet Dashboard starting on http://localhost:{port}")
    print(f"   Dashboard: http://localhost:{port}/")
    print(f"   API:       http://localhost:{port}/api/status")
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    server.serve_forever()
