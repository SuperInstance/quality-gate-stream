#!/usr/bin/env python3
"""PLATO Demo Live Feed — connects PLATO server to demo consumers."""
import json, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PLATO_URL = "http://localhost:8847"
PORT = 4041

cache = {"tiles": [], "stats": {}, "rooms": {}, "last_fetch": 0}
cache_lock = threading.Lock()

def fetch_plato():
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"{PLATO_URL}/status", timeout=5)
        data = json.loads(resp.read())
        with cache_lock:
            cache["stats"] = {
                "total_tiles": data.get("tile_count", 0),
                "rooms": data.get("rooms", {}),
                "gate_stats": data.get("gate_stats", {}),
                "status": data.get("status", "active"),
            }
        resp = urllib.request.urlopen(f"{PLATO_URL}/export/plato-tile-spec", timeout=10)
        data = json.loads(resp.read())
        with cache_lock:
            cache["tiles"] = data.get("tiles", [])[:200]
            cache["last_fetch"] = time.time()
    except Exception as e:
        print(f"Fetch error: {e}")

def refresh_loop():
    while True:
        fetch_plato()
        time.sleep(30)

DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><title>Cocapn Fleet Live</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:monospace;background:#1e1e2e;color:#cdd6f4;padding:20px}
h1{color:#cba6f7;font-size:1.4em;margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px;margin-top:15px}
.card{background:#313244;border-radius:8px;padding:15px;border:1px solid #45475a}
.card h2{color:#89b4fa;font-size:1em;margin-bottom:8px}
.big{font-size:2em;color:#a6e3a1;font-weight:bold}
.label{color:#6c7086;font-size:0.8em}
.tiles{max-height:500px;overflow-y:auto;margin-top:15px}
.tile{background:#313244;border-radius:6px;padding:10px;margin-bottom:8px;border-left:3px solid #89b4fa}
.tile .q{color:#f9e2af;font-size:0.85em}
.tile .a{color:#cdd6f4;font-size:0.8em;max-height:60px;overflow:hidden;margin-top:4px}
.tile .meta{color:#6c7086;font-size:0.7em;margin-top:4px}
.bar{height:8px;background:#45475a;border-radius:4px;margin-top:6px}
.fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#a6e3a1,#89b4fa)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%}
.up{background:#a6e3a1}.down{background:#f38ba8}
.refresh{color:#6c7086;font-size:0.75em;float:right}
</style></head><body>
<h1>🔮 Cocapn Fleet — Live</h1>
<div class="refresh">Auto-refresh 30s | <span id="ts">-</span></div>
<div class="grid" id="stats"></div>
<div class="grid" id="rooms"></div>
<h1 style="margin-top:20px">Latest Tiles</h1>
<div class="tiles" id="tiles"></div>
<script>
async function refresh(){
  try{
    const s=await (await fetch('/api/stats')).json();
    const accepted=s.gate_stats?s.gate_stats.accepted:0;
    const rejected=s.gate_stats?s.gate_stats.rejected:0;
    const rate=((accepted/(accepted+rejected||1))*100).toFixed(1);
    document.getElementById('stats').innerHTML=
      '<div class="card"><h2>Total Tiles</h2><div class="big">'+(s.total_tiles||0)+'</div><div class="label">across '+Object.keys(s.rooms||{}).length+' rooms</div></div>'+
      '<div class="card"><h2>Gate Pass Rate</h2><div class="big">'+rate+'%</div><div class="label">'+accepted+' accepted, '+rejected+' rejected</div></div>'+
      '<div class="card"><h2>Status</h2><div class="big"><span class="dot '+(s.status==='active'?'up':'down')+'"></span> '+s.status+'</div></div>';
    let rooms='';const mx=Math.max(...Object.values(s.rooms||{}).map(r=>r.tile_count||0),1);
    for(const[n,i]of Object.entries(s.rooms||{})){
      rooms+='<div class="card"><h2>'+n+'</h2><div class="big">'+(i.tile_count||0)+'</div><div class="bar"><div class="fill" style="width:'+((i.tile_count||0)/mx*100)+'%"></div></div></div>';
    }
    document.getElementById('rooms').innerHTML=rooms;
    const t=await (await fetch('/api/tiles')).json();
    let h='';for(const tile of(t.tiles||[]).slice(0,40)){
      h+='<div class="tile"><div class="q">'+((tile.question||'')).substring(0,100)+'</div>'+
        '<div class="a">'+((tile.answer||'')).substring(0,200)+'</div>'+
        '<div class="meta">'+tile.domain+' | conf:'+tile.confidence+' | '+(tile.provenance?.source||'?')+'</div></div>';
    }
    document.getElementById('tiles').innerHTML=h;
    document.getElementById('ts').textContent=new Date().toLocaleTimeString();
  }catch(e){console.error(e)}
}
refresh();setInterval(refresh,30000);
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._html(DASHBOARD_HTML)
        elif path == "/api/stats":
            with cache_lock: self._json(cache["stats"])
        elif path == "/api/tiles":
            with cache_lock: self._json({"tiles": cache["tiles"][:50], "total": len(cache["tiles"])})
        elif path == "/api/rooms":
            with cache_lock: self._json(cache["stats"].get("rooms", {}))
        elif path == "/export/dcs":
            with cache_lock: self._json({"tiles": cache["tiles"][:50], "format": "dcs-v1"})
        elif path == "/export/plato":
            with cache_lock: self._json({"tiles": cache["tiles"][:50], "format": "plato-tile-spec"})
        else:
            self.send_error(404)

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"PLATO Demo Live on :{PORT}")
    print(f"Dashboard: http://localhost:{PORT}/")
    threading.Thread(target=refresh_loop, daemon=True).start()
    fetch_plato()
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
