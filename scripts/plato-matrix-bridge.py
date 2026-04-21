#!/usr/bin/env python3
"""
PLATO → Matrix Bridge

Polls PLATO Room Server for new tiles and posts them to Matrix #cocapn-build.
Every 60 seconds, checks for new tiles and posts a summary.

This IS the CCC ask: real-time tile visibility across the fleet.
"""
import json, time, urllib.request, hashlib
from pathlib import Path

PLATO_URL = "http://localhost:8847"
MATRIX_URL = "http://localhost:6167"
MATRIX_TOKEN = "cZpdJNoUymtMLcHPbAoMY8GpsNv4Qie7"
MATRIX_ROOM = "!hHMkCC5dMMToEm4pyI:147.224.38.131"

STATE_FILE = Path(__file__).parent.parent / "data" / "plato-matrix-bridge.json"
POLL_INTERVAL = 60  # seconds
BATCH_SIZE = 10  # max tiles to post per cycle

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tile_count": 0, "last_rooms": {}, "posted_count": 0}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def plato_status():
    try:
        req = urllib.request.Request(f"{PLATO_URL}/status", headers={"User-Agent": "plato-bridge/1.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        return None

def matrix_post(body):
    try:
        ts = f"plato-tile-{int(time.time())}-{hashlib.md5(body.encode()).hexdigest()[:6]}"
        data = json.dumps({"msgtype": "m.text", "body": body}).encode()
        req = urllib.request.Request(
            f"{MATRIX_URL}/_matrix/client/v3/rooms/{MATRIX_ROOM}/send/m.room.message/{ts}",
            data=data,
            headers={
                "Authorization": f"Bearer {MATRIX_TOKEN}",
                "Content-Type": "application/json",
            },
            method="PUT",
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        print(f"  Matrix post failed: {e}")
        return None

def run():
    print("🌉 PLATO → Matrix Bridge starting...")
    state = load_state()
    
    while True:
        try:
            status = plato_status()
            if not status:
                print(f"  PLATO unreachable, retrying in {POLL_INTERVAL}s")
                time.sleep(POLL_INTERVAL)
                continue
            
            total = status["total_tiles"]
            rooms = status.get("rooms", {})
            
            if total > state["last_tile_count"]:
                new_count = total - state["last_tile_count"]
                
                # Find which rooms grew
                room_changes = []
                for room_name, room_info in rooms.items():
                    old_count = state["last_rooms"].get(room_name, {}).get("tile_count", 0)
                    new_tiles = room_info["tile_count"] - old_count
                    if new_tiles > 0:
                        room_changes.append((room_name, new_tiles, room_info["tile_count"]))
                
                # Sort by new tiles desc
                room_changes.sort(key=lambda x: -x[1])
                
                # Post summary
                top = room_changes[:BATCH_SIZE]
                lines = [f"🧱 {new_count} new PLATO tiles (total: {total})"]
                for name, new, total_r in top:
                    lines.append(f"  • {name}: +{new} ({total_r} total)")
                
                if len(room_changes) > BATCH_SIZE:
                    lines.append(f"  ... +{len(room_changes) - BATCH_SIZE} more rooms")
                
                msg = "\n".join(lines)
                result = matrix_post(msg)
                
                if result and "event_id" in result:
                    state["posted_count"] += 1
                    print(f"  Posted: {msg[:100]}...")
                else:
                    print(f"  Failed to post")
                
                state["last_tile_count"] = total
                state["last_rooms"] = {name: {"tile_count": info["tile_count"]} for name, info in rooms.items()}
                save_state(state)
            else:
                print(f"  No new tiles ({total} total)")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run()
