#!/usr/bin/env python3
"""
CurriculumEngine Runner — run curriculum for a specific agent.
Generates training tiles from PLATO rooms and delivers them.

Usage:
  python3 run_curriculum.py --agent ccc --dry-run
  python3 run_curriculum.py --agent ccc --execute
"""

import json, urllib.request, sys, os, time

PLATO_URL = "http://localhost:8847"

def plato_get(path):
    req = urllib.request.Request(f"{PLATO_URL}{path}", headers={"User-Agent": "curriculum"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def plato_post(path, data):
    req = urllib.request.Request(f"{PLATO_URL}{path}", method="POST",
                                  data=json.dumps(data).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

# Agent curricula: which rooms to train on at each stage
CURRICULA = {
    "ccc": {
        "name": "CCC Fleet Face",
        "stages": [
            {
                "name": "Orientation",
                "rooms": ["fleet", "cocapn"],
                "goal": "Understand fleet structure, agent roles, and Cocapn identity",
                "min_tiles": 5,
            },
            {
                "name": "Exploration",
                "rooms": ["fleet_orchestration", "plato"],
                "goal": "Learn coordination patterns, PLATO system, and tile-based knowledge",
                "min_tiles": 10,
            },
            {
                "name": "Application",
                "rooms": ["fleet_formation_protocol", "deadband_protocol", "keeper-beacon"],
                "goal": "Apply coordination and safety patterns to fleet operations",
                "min_tiles": 8,
            },
            {
                "name": "Synthesis",
                "rooms": ["neural", "energy_flux", "edge_compute"],
                "goal": "Cross-domain synthesis — connect architecture patterns across subsystems",
                "min_tiles": 5,
            },
            {
                "name": "Mastery",
                "rooms": ["fleet_security", "knowledge_preservation"],
                "goal": "Master security and knowledge preservation for fleet operations",
                "min_tiles": 5,
            },
        ],
        "target_room": "ccc_context",
    },
    "jetsonclaw1": {
        "name": "JetsonClaw1 Edge Operator",
        "stages": [
            {
                "name": "Orientation",
                "rooms": ["edge", "edge_compute"],
                "goal": "Understand edge deployment, GPU optimization, and Jetson architecture",
                "min_tiles": 5,
            },
            {
                "name": "Exploration",
                "rooms": ["gpu-optimization", "neural"],
                "goal": "Learn GPU benchmarking, model optimization, and neural architecture",
                "min_tiles": 10,
            },
        ],
        "target_room": "jc1_context",
    },
}

def run_curriculum(agent, execute=False):
    """Run curriculum for an agent."""
    if agent not in CURRICULA:
        print(f"No curriculum defined for {agent}")
        return
    
    curriculum = CURRICULA[agent]
    target_room = curriculum["target_room"]
    
    print(f"🎓 Curriculum: {curriculum['name']}")
    print(f"   Target room: {target_room}")
    print(f"   Stages: {len(curriculum['stages'])}")
    print()
    
    total_delivered = 0
    
    for i, stage in enumerate(curriculum["stages"], 1):
        print(f"  Stage {i}: {stage['name']}")
        print(f"    Goal: {stage['goal']}")
        print(f"    Source rooms: {', '.join(stage['rooms'])}")
        
        # Gather tiles from source rooms
        stage_tiles = []
        for room in stage["rooms"]:
            data = plato_get(f"/room/{room}")
            if data and "tiles" in data:
                # Pick top tiles by confidence
                tiles = sorted(data["tiles"], key=lambda t: float(t.get("confidence", 0.5)), reverse=True)
                stage_tiles.extend(tiles[:stage["min_tiles"]])
        
        if not stage_tiles:
            print(f"    ⚠ No tiles found, skipping")
            continue
        
        # Deduplicate by question
        seen = set()
        unique = []
        for t in stage_tiles:
            q = t.get("question", "")
            if q not in seen:
                seen.add(q)
                unique.append(t)
        stage_tiles = unique[:stage["min_tiles"] * 2]  # Cap per stage
        
        print(f"    Tiles to deliver: {len(stage_tiles)}")
        
        if execute:
            delivered = 0
            for tile in stage_tiles:
                try:
                    result = plato_post("/submit", {"room": target_room, **tile})
                    if result.get("status") in ("accepted", "ok"):
                        delivered += 1
                except:
                    pass
            print(f"    ✓ Delivered: {delivered}/{len(stage_tiles)}")
            total_delivered += delivered
        else:
            print(f"    [DRY] Would deliver {len(stage_tiles)} tiles")
            for t in stage_tiles[:3]:
                print(f"      - {t.get('question', '')[:70]}")
            if len(stage_tiles) > 3:
                print(f"      ... and {len(stage_tiles)-3} more")
        
        print()
    
    print(f"  Total: {'would deliver' if not execute else 'delivered'} {total_delivered if execute else 'N/A'} tiles")

def main():
    args = sys.argv[1:]
    if "--agent" not in args:
        print("Usage: run_curriculum.py --agent <name> [--execute]")
        return
    
    agent = args[args.index("--agent") + 1]
    execute = "--execute" in args
    run_curriculum(agent, execute)

if __name__ == "__main__":
    main()
