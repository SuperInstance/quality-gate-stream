#!/usr/bin/env python3
"""
Matrix Bridge v2 — auto-posts fleet activity to Matrix rooms.
Monitors PLATO workspace changes, beachcomb findings, and git commits.

Rooms:
  Fleet Coordination — agent status changes, task assignments
  PLATO Tiles — new high-quality tiles
  Ten Forward — casual agent chatter
  GPU Optimization — JC1 specific updates
"""

import json, urllib.request, os, time, hashlib

PLATO_URL = "http://localhost:8847"
MATRIX_URL = os.environ.get("MATRIX_URL", "http://localhost:6167")
STATE_FILE = "/tmp/matrix-bridge-v2-state.json"

# Matrix room IDs (from Conduwuit)
ROOMS = {
    "fleet-coord": "!z5oIJTqor4UUZliQp1",
    "plato-tiles": "!wzPdHjulBK4E2V6jPH",
    "ten-forward": "!Keng30jlSNNpluCpa0",
    "gpu-opt": "!or6aVWz5OGvuqA8haD",
}

def http_get(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "matrix-bridge-v2"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def matrix_send(room_id, message):
    """Send a message to a Matrix room via the Conduwuit admin API."""
    try:
        txn_id = hashlib.md5(f"{room_id}{time.time()}".encode()).hexdigest()[:16]
        url = f"{MATRIX_URL}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}"
        # Use the PLATO server's internal registration token
        data = {
            "msgtype": "m.text",
            "body": message,
        }
        req = urllib.request.Request(url, method="PUT",
                                      data=json.dumps(data).encode(),
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"last_check": None, "last_tile_count": 0, "notified": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_plato_growth(state):
    """Check if PLATO grew and notify."""
    status = http_get(f"{PLATO_URL}/status")
    if not status:
        return state
    
    rooms = status.get("rooms", {})
    total = sum(r.get("tile_count", 0) for r in rooms.values())
    last = state.get("last_tile_count", 0)
    
    if total > last and last > 0:
        delta = total - last
        if delta >= 10:  # Only notify on significant growth
            msg = f"📊 PLATO grew by {delta} tiles — now at {total} across {len(rooms)} rooms"
            result = matrix_send(ROOMS["plato-tiles"], msg)
            state["notified"][f"plato-{total}"] = True
    
    state["last_tile_count"] = total
    return state

def check_workspace_changes(state):
    """Check agent workspace boards for changes."""
    for agent in ["oracle1", "jetsonclaw1", "forgemaster", "ccc"]:
        ws = http_get(f"{PLATO_URL}/workspace/{agent}")
        if not ws:
            continue
        
        key = f"ws-{agent}"
        current = json.dumps(ws, sort_keys=True)
        last = state.get(key, "")
        
        if current != last and last:  # Changed
            task = ws.get("active_task", "idle")[:60]
            status = ws.get("status", "?")
            msg = f"🔄 {agent}: {status} — {task}"
            result = matrix_send(ROOMS["fleet-coord"], msg)
        
        state[key] = current
    return state

def check_beachcomb(state):
    """Check beachcomb findings."""
    try:
        with open("/tmp/beachcomb-data/findings.json") as f:
            findings = json.load(f)
    except:
        return state
    
    last_ts = state.get("last_beachcomb_ts", 0)
    new = [f for f in findings if f.get("timestamp", 0) > last_ts]
    
    if new:
        commits = [f for f in new if f["type"] == "commit"]
        if commits:
            lines = [f"⚓ {len(commits)} new commits:"]
            for c in commits[:5]:
                lines.append(f"  {c['repo'].split('/')[1]}: {c['message'][:50]} ({c['author']})")
            matrix_send(ROOMS["fleet-coord"], "\n".join(lines))
        
        state["last_beachcomb_ts"] = max(f.get("timestamp", 0) for f in new)
    return state

def run_once():
    state = load_state()
    state = check_plato_growth(state)
    state = check_workspace_changes(state)
    state = check_beachcomb(state)
    state["last_check"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_state(state)
    return state

def main():
    import sys
    once = "--once" in sys.argv
    loop = 300
    
    for i, arg in enumerate(sys.argv):
        if arg == "--loop" and i + 1 < len(sys.argv):
            loop = int(sys.argv[i + 1])
    
    if once:
        run_once()
        print("Bridge v2 check complete")
        return
    
    print(f"🌉 Matrix Bridge v2 running (every {loop}s)")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(loop)

if __name__ == "__main__":
    main()
