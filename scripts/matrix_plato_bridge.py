#!/usr/bin/env python3
"""
Matrix-PLATO Bridge — syncs PLATO tiles to Matrix rooms for fleet visibility.
Replaces Ship Protocol layers 1,3,4,5,6. Keeps layer 2 (bottles) for audit.

Usage:
  python3 matrix_plato_bridge.py [--sync] [--post-tiles] [--post-workspaces]
  
Runs as a one-shot or cron job.
"""

import json, urllib.request, urllib.parse, sys, os, time
from datetime import datetime

# Config
MATRIX_URL = os.environ.get("MATRIX_URL", "http://localhost:6167")
PLATO_URL = os.environ.get("PLATO_URL", "http://localhost:8847")
MATRIX_USER = "oracle1"
MATRIX_PASS = "fleet-oracle1-2026"
SERVER_NAME = "147.224.38.131"
STATE_FILE = "/tmp/matrix-plato-bridge-state.json"

# Room mapping: PLATO room → Matrix room
ROOM_MAP = {
    "fleet_orchestration": f"!z5oIJTqor4UUZliQp1:{SERVER_NAME}",
    "architecture": f"!wzPdHjulBK4E2V6jPH:{SERVER_NAME}",
    "general": f"!Keng30jlSNNpluCpa0:{SERVER_NAME}",
    "gpu-optimization": f"!or6aVWz5OGvuqA8haD:{SERVER_NAME}",
}

def matrix_login():
    """Login to Matrix and get access token."""
    data = json.dumps({
        "type": "m.login.password",
        "user": MATRIX_USER,
        "password": MATRIX_PASS
    }).encode()
    req = urllib.request.Request(
        f"{MATRIX_URL}/_matrix/client/v3/login",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["access_token"]

def matrix_send(token, room_id, text):
    """Send a message to a Matrix room."""
    txn_id = f"tx-{int(time.time())}-{os.getpid()}"
    data = json.dumps({"msgtype": "m.text", "body": text}).encode()
    req = urllib.request.Request(
        f"{MATRIX_URL}/_matrix/client/v3/rooms/{urllib.parse.quote(room_id, safe='')}/send/m.room.message/{txn_id}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp.get("event_id")

def plato_get(path):
    """GET from PLATO server."""
    req = urllib.request.Request(f"{PLATO_URL}{path}")
    return json.loads(urllib.request.urlopen(req).read())

def load_state():
    """Load bridge state (last sync timestamps)."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_sync": 0, "posted_tiles": []}

def save_state(state):
    """Save bridge state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def sync_tiles(token, since=0):
    """Sync recent PLATO tiles to Matrix rooms."""
    state = load_state()
    posted = 0
    
    for plato_room, matrix_room in ROOM_MAP.items():
        try:
            tiles = plato_get(f"/room/{plato_room}")
            if isinstance(tiles, dict):
                tiles = tiles.get("tiles", tiles.get(plato_room, {}).get("tiles", []))
            if not isinstance(tiles, list):
                tiles = []
            
            for tile in tiles:
                tile_hash = tile.get("hash", tile.get("id", ""))
                if tile_hash in state.get("posted_tiles", []):
                    continue
                
                q = tile.get("question", "")[:100]
                a = tile.get("answer", "")[:200]
                agent = tile.get("agent", "unknown")
                conf = tile.get("confidence", "?")
                
                msg = f"📚 Tile from {agent} (conf={conf}):\nQ: {q}\nA: {a}"
                try:
                    matrix_send(token, matrix_room, msg)
                    state.setdefault("posted_tiles", []).append(tile_hash)
                    posted += 1
                except Exception as e:
                    print(f"Error posting tile: {e}")
        except Exception as e:
            print(f"Error fetching room {plato_room}: {e}")
    
    state["last_sync"] = time.time()
    save_state(state)
    return posted

def post_workspaces(token):
    """Post current workspace states to Fleet Coordination room."""
    fleet_room = ROOM_MAP.get("fleet_orchestration", list(ROOM_MAP.values())[0])
    posted = 0
    
    try:
        workspaces = plato_get("/workspaces")
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("workspaces", [])
        
        for ws in workspaces:
            agent = ws.get("agent", "unknown")
            status = ws.get("status", "?")
            task = ws.get("active_task", "")[:80]
            updated = ws.get("updated", "?")[:19]
            
            msg = f"📊 {agent}: [{status}] {task} (updated {updated})"
            try:
                matrix_send(token, fleet_room, msg)
                posted += 1
            except Exception as e:
                print(f"Error posting workspace: {e}")
    except Exception as e:
        print(f"Error fetching workspaces: {e}")
    
    return posted

def main():
    token = matrix_login()
    
    total_posted = 0
    
    if "--post-tiles" in sys.argv or "--sync" in sys.argv:
        n = sync_tiles(token)
        total_posted += n
        print(f"Synced {n} tiles to Matrix")
    
    if "--post-workspaces" in sys.argv or "--sync" in sys.argv:
        n = post_workspaces(token)
        total_posted += n
        print(f"Posted {n} workspace updates to Matrix")
    
    if "--sync" not in sys.argv and "--post-tiles" not in sys.argv and "--post-workspaces" not in sys.argv:
        # Default: do everything
        n1 = sync_tiles(token)
        n2 = post_workspaces(token)
        total_posted = n1 + n2
        print(f"Synced {n1} tiles, {n2} workspaces")
    
    print(f"Total: {total_posted} messages posted to Matrix")
    return total_posted

if __name__ == "__main__":
    main()
