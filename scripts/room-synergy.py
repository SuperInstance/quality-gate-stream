#!/usr/bin/env python3
"""
Cross-Room Synergy Detection — Find connections between rooms.
"""
import json
from pathlib import Path
from collections import defaultdict
import urllib.request

PLATO_URL = "http://localhost:8847"

def get_all_rooms():
    resp = urllib.request.urlopen(PLATO_URL + "/rooms", timeout=10)
    return json.loads(resp.read())

def get_room_tiles(room_name):
    try:
        resp = urllib.request.urlopen(PLATO_URL + "/room/" + room_name, timeout=10)
        data = json.loads(resp.read())
        return data.get("tiles", [])
    except:
        return []

def compute_synergy():
    rooms = get_all_rooms()
    room_names = list(rooms.keys())
    
    room_tags = defaultdict(lambda: defaultdict(int))
    room_sources = defaultdict(set)
    
    for name in room_names:
        tiles = get_room_tiles(name)
        for tile in tiles:
            for tag in tile.get("tags", []):
                room_tags[name][tag] += 1
            src = tile.get("source", "")
            if src:
                room_sources[name].add(src.split(":")[1] if ":" in src else src)
    
    synergies = []
    for i, r1 in enumerate(room_names):
        for r2 in room_names[i+1:]:
            shared_tags = set(room_tags[r1].keys()) & set(room_tags[r2].keys())
            if shared_tags:
                total_shared = sum(min(room_tags[r1][t], room_tags[r2][t]) for t in shared_tags)
                if total_shared >= 3:
                    synergies.append({
                        "room1": r1, "room2": r2,
                        "shared_tags": list(shared_tags),
                        "shared_strength": total_shared,
                    })
    
    synergies.sort(key=lambda x: -x["shared_strength"])
    
    source_synergies = []
    for i, r1 in enumerate(room_names):
        for r2 in room_names[i+1:]:
            shared_sources = room_sources[r1] & room_sources[r2]
            if shared_sources:
                source_synergies.append({"room1": r1, "room2": r2, "shared_agents": list(shared_sources)})
    
    return {"tag_synergies": synergies[:10], "source_synergies": source_synergies[:10], "total_rooms": len(room_names)}

if __name__ == "__main__":
    result = compute_synergy()
    
    print("LINK CROSS-ROOM SYNERGY REPORT")
    print("  " + str(result["total_rooms"]) + " rooms analyzed")
    print()
    
    if result["tag_synergies"]:
        print("  TAG OVERLAPS:")
        for s in result["tag_synergies"]:
            print("    " + s["room1"] + " <-> " + s["room2"] + ": strength=" + str(s["shared_strength"]) + " tags=" + str(s["shared_tags"][:5]))
    
    if result["source_synergies"]:
        print("\n  AGENT OVERLAPS:")
        for s in result["source_synergies"]:
            print("    " + s["room1"] + " <-> " + s["room2"] + ": agents=" + str(s["shared_agents"]))
    
    Path("/tmp/plato-server-data/synergy.json").write_text(json.dumps(result, indent=2))
    print("\n  Saved to synergy.json")
