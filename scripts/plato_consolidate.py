#!/usr/bin/env python3
"""
PLATO Room Consolidator — merge small rooms into parent rooms.

Finds rooms with <3 tiles that logically belong to larger rooms,
submits their tiles to the parent, and logs the merges.

Usage:
  python3 plato_consolidate.py scan
  python3 plato_consolidate.py merge --dry-run
  python3 plato_consolidate.py merge --execute
"""

import json, urllib.request, sys, os, re, time
from collections import defaultdict

PLATO_URL = "http://localhost:8847"
LOG_FILE = "/tmp/plato-consolidation-log.json"

def plato_get(path):
    req = urllib.request.Request(f"{PLATO_URL}{path}", headers={"User-Agent": "plato-consolidate/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def plato_post(path, data):
    req = urllib.request.Request(f"{PLATO_URL}{path}", method="POST",
                                  data=json.dumps(data).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

# Merge map: small room prefix → parent room
MERGE_RULES = {
    # deadband sub-rooms → deadband_protocol
    "deadband-protocol-core-architecture": "deadband_protocol",
    "deadband-protocol-edge-cases": "deadband_protocol",
    "deadband-protocol-pattern-matching": "deadband_protocol",
    "deadband-protocol-priority-tiers": "deadband_protocol",
    "deadband-protocol-result-class": "deadband_protocol",
    "deadband-protocol-security-domain": "deadband_protocol",
    
    # deepfar sub-rooms → deepfar (keep major versions)
    "deepfar-deepfar4.1.1": "deepfar-deepfar4",
    "deepfar-deepfar4.1.2": "deepfar-deepfar4",
    "deepfar-deepfar4.1.3": "deepfar-deepfar4",
    
    # edge sub-rooms → edge or edge_compute
    "edge-ai-optimization-updates": "edge",
    "edge-deployment-strategies": "edge",
    "edge-native-agentic-intelligence": "edge_compute",
    
    # energy sub-rooms → energy_flux
    "energy-harvesting": "energy_flux",
    "energy_&_performance": "energy_flux",
    "energy_harvesting": "energy_flux",
    
    # fleet sub-rooms → fleet or fleet_orchestration
    "fleet-activity-logging": "fleet",
    "fleet-coordination-protocols": "fleet_orchestration",
    "fleet-daily-dashboard": "fleet",
    "fleet-dispatch": "fleet_orchestration",
    "fleet-formation-centralized-coordinator": "fleet_formation_protocol",
    "fleet-coordination-protocols": "fleet_orchestration",
    "fleet-lore": "fleet",
    "fleet-narrative": "fleet",
    "fleet-ops": "fleet",
    "fleet-progress": "fleet",
    "fleet-recommendations": "fleet",
    "fleet-scalability": "fleet",
    "fleet-security": "fleet_security",
    "fleet-unified-theory": "fleet",
    
    # jc1 sub-rooms → jc1_context
    "jc1_direct": "jc1_context",
    "jc1_urgent": "jc1_context",
    
    # neural sub-rooms → neural
    "neural-networks": "neural",
    "neural-synapse-design": "neural",
    
    # room sub-rooms → room
    "room-design": "room",
    "room_design": "room",
    
    # grammar sub-rooms → grammar_evolution
    "grammar-dynamics": "grammar_evolution",
    "grammar-evolution": "grammar_evolution",
    
    # knowledge sub-rooms → knowledge_preservation
    "knowledge-isolation-design": "knowledge_preservation",
    "knowledge-management": "knowledge_preservation",
    "knowledge-management-domain": "knowledge_preservation",
    "knowledge-quality": "knowledge_preservation",
    "knowledge-tiles": "tile",
    
    # information → information-theory
    "information_thermodynamics": "information-thermodynamics",
    "information_theory": "information-theory",
    
    # memory → memory-palace
    "memory-vault": "memory-palace",
    "memory_technology": "memory-palace",
    
    # neural → neural
    "neuromorphic-computing": "neuromorphic_engineering",
    "neuromorphic_learning_hardware": "neuromorphic_engineering",
    "neuromorphic_memory_architecture": "neuromorphic_engineering",
    
    # tile sub-rooms → tile
    "tile-class-optimizations": "tile",
    "tile-domain-standards": "tile",
    "tile-identifier-generation": "tile",
    "tile-priority-scoring": "tile",
    "tile-spec-format": "tile",
    "tile-specification-domain": "tile",
    "tile-store-bugs": "tile",
    
    # thermal → thermal-mathematics
    "thermal-dynamics": "thermal-mathematics",
    "thermal-fluid_dynamics": "thermal-fluid-dynamics",
    "thermal_engineering": "thermal-mathematics",
    
    # prompt sub-rooms → prompt-review
    "prompt-laboratory": "prompt-review",
    "prompt-rag-integration": "prompt-review",
    
    # quantum → quantum-thermal-transport
    "quantum-nanoscale": "quantum-nanoscale-physics",
    "quantum-thermal": "quantum-thermal-transport",
    
    # rust sub-rooms → rust
    "rust-async-runtimes": "rust",
    "rust-crate-installation": "rust",
    "rust-crate-performance": "rust",
    "rust-error-handling": "rust",
    "rust-mud-architecture": "rust",
    
    # git-agent sub-rooms → git-agent-lab
    "git-agent-agent-lifecycle": "git-agent-lab",
    "git-agent-fleet-coordination": "git-agent-lab",
    "git-agent-project-structure": "git-agent-lab",
    "git-native-agents": "git-agent-lab",
}

def scan():
    """Scan for consolidation opportunities."""
    status = plato_get("/status")
    rooms = status.get("rooms", {})
    
    single_tile_rooms = [(k, v.get("tile_count", 0)) for k, v in rooms.items() if v.get("tile_count", 0) <= 2]
    single_tile_rooms.sort(key=lambda x: x[0])
    
    print(f"PLATO Room Consolidation Scan")
    print(f"  Total rooms: {len(rooms)}")
    print(f"  Single-tile rooms: {len(single_tile_rooms)}")
    print(f"  Merge rules defined: {len(MERGE_RULES)}")
    print()
    
    matched = 0
    unmatched = 0
    for room, count in single_tile_rooms:
        if room in MERGE_RULES:
            target = MERGE_RULES[room]
            target_count = rooms.get(target, {}).get("tile_count", "?")
            print(f"  ✓ {room} ({count}) → {target} ({target_count})")
            matched += 1
        else:
            unmatched += 1
    
    print(f"\n  Matched: {matched}, Unmatched: {unmatched}")

def merge(dry_run=True):
    """Execute merges."""
    status = plato_get("/status")
    rooms = status.get("rooms", {})
    
    merged_count = 0
    tiles_moved = 0
    errors = []
    
    for source_room, target_room in MERGE_RULES.items():
        source_count = rooms.get(source_room, {}).get("tile_count", 0)
        target_count = rooms.get(target_room, {}).get("tile_count", 0)
        
        if source_count == 0:
            continue
        
        # Get source tiles
        try:
            data = plato_get(f"/room/{source_room}")
            tiles = data.get("tiles", [])
        except:
            continue
        
        if not tiles:
            continue
        
        if dry_run:
            print(f"  [DRY] {source_room} ({len(tiles)} tiles) → {target_room} ({target_count} tiles)")
            merged_count += 1
            tiles_moved += len(tiles)
            continue
        
        # Submit each tile to the target room
        accepted = 0
        for tile in tiles:
            try:
                result = plato_post(f"/submit", {
                    "room": target_room,
                    **tile
                })
                if result.get("status") in ("accepted", "ok"):
                    accepted += 1
            except Exception as e:
                errors.append(f"{source_room}→{target_room}: {e}")
        
        if accepted > 0:
            print(f"  ✓ {source_room} ({accepted}/{len(tiles)} tiles) → {target_room}")
            merged_count += 1
            tiles_moved += accepted
    
    action = "WOULD merge" if dry_run else "Merged"
    print(f"\n  {action}: {merged_count} rooms, {tiles_moved} tiles moved")
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    {e}")
    
    # Save log
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": dry_run,
        "rooms_merged": merged_count,
        "tiles_moved": tiles_moved,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: plato_consolidate.py [scan|merge --dry-run|merge --execute]")
        return
    
    cmd = sys.argv[1]
    if cmd == "scan":
        scan()
    elif cmd == "merge":
        dry_run = "--execute" not in sys.argv
        merge(dry_run)
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
