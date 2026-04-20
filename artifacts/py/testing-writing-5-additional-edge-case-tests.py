"""
PLATO Room: testing
Tile: Writing 5 Additional Edge-Case Tests
Domain: testing
"""

def test_phase_transition_effects():
    """Test that changing phase affects tile optimization metadata."""
    room = DeadbandRoom("test_room", {})
    room.registered_agents = {"mason"}
    
    # Submit tile in P0
    tile1 = {"agent_id": "mason", "cycle": 1, "content": "test1", "phase": "P0"}
    assert room.submit_tile(tile1) == True
    assert room.tiles[0].get("phase") == "P0"
    
    # Switch to P1 and submit another tile
    room.set_phase("P1")
    tile2 = {"agent_id": "mason", "cycle": 2, "content": "test2", "phase": "P1"}
    assert room.submit_tile(tile2) == True
    assert room.tiles[1].get("phase") == "P1"
    
    # Verify phases are stored correctly
    assert room.tiles[0]["phase"] != room.tiles[1]["phase"]

def test_tile_with_invalid_phase():
    """Test rejection of tile where phase field is not P0/P1/P2."""
    room = DeadbandRoom("test_room", {})
    room.registered_agents = {"mason"}
    
    # Tile has required fields but phase is invalid
    tile = {"agent_id": "mason", "cycle": 82, "content": "test", "phase": "P3"}
    assert room.submit_tile(tile) == False  # Should violate P0
    assert room.tiles_submitted == 0

import threading

def test_concurrent_tile_submissions():
    """Simulate multiple agents submitting tiles concurrently."""
    room = DeadbandRoom("test_room", {})
    room.registered_agents = {"agent1", "agent2", "agent3"}
    
    results = []
    def submit(agent_id):
        tile = {"agent_id": agent_id, "cycle": 82, "content": "concurrent", "phase": "P1"}
        results.append(room.submit_tile(tile))
    
    threads = [
        threading.Thread(target=submit, args=("agent1",)),
        threading.Thread(target=submit, args=("agent2",)),
        threading.Thread(target=submit, args=("agent3",))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All should succeed
    assert all(results) == True
    assert room.tiles_submitted == 3

