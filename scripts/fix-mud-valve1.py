#!/usr/bin/env python3
"""
MUD valve-1 Leak Patch
Removes or redacts valve-1's examine handler in engine-room.
Run this on the Oracle1 server, then restart MUD service.
"""
import json
import sys

WORLD_FILE = "/home/ubuntu/.openclaw/workspace/data/mud/world.json"

def patch_valve1():
    try:
        with open(WORLD_FILE, "r") as f:
            world = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read {WORLD_FILE}: {e}")
        return False
    
    # Find engine-room
    rooms = world.get("rooms", {})
    if "engine-room" not in rooms:
        print("WARNING: engine-room not found in world")
        return False
    
    engine_room = rooms["engine-room"]
    objects = engine_room.get("objects", [])
    
    # Find valve-1
    valve1 = None
    for obj in objects:
        if obj.get("name") == "valve-1":
            valve1 = obj
            break
    
    if not valve1:
        print("WARNING: valve-1 not found in engine-room")
        return False
    
    # Replace examine action with safe description
    valve1["actions"] = {
        "examine": {
            "type": "description",
            "text": "A standard pressure regulation valve. Fleet issue, rated for 300 PSI."
        }
    }
    
    # Remove any data-leaking properties
    for key in ["grammar_dump", "rules", "data_source", "endpoint"]:
        if key in valve1:
            del valve1[key]
    
    # Write back
    try:
        with open(WORLD_FILE, "w") as f:
            json.dump(world, f, indent=2)
        print(f"SUCCESS: Patched valve-1 in {WORLD_FILE}")
        print("NEXT: Restart MUD service (sudo systemctl restart mud or docker restart mud)")
        return True
    except Exception as e:
        print(f"ERROR: Could not write {WORLD_FILE}: {e}")
        return False

if __name__ == "__main__":
    print("=== MUD valve-1 Leak Patch ===")
    if patch_valve1():
        print("\nVerify after restart:")
        print("curl 'http://147.224.38.131:4042/interact?agent=test&action=examine&target=valve-1'")
        sys.exit(0)
    else:
        sys.exit(1)
