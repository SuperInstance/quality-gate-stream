"""
PLATO Room: testing
Tile: New Edge-Case Tests Written
Domain: testing
"""

def test_p0_violation_skipping_to_p2():
    """P0: Room must reject tiles that skip P0 and jump directly to P2 optimization."""
    room = DeadbandRoom()
    agent_id = "test_agent_1"
    
    # Tile that violates protocol by having P2 without P0/P1
    violating_tile = {
        "agent_id": agent_id,
        "cycle": 100,
        "phase": 4,
        "content": "Optimizing without mapping negative space",
        "protocol_step": "P2",  # Jumping directly to P2
        "p0_mapped": False,     # No P0 work done
        "p1_channels": []       # No P1 channels found
    }
    
    result = room.submit_tile(agent_id, violating_tile)
    assert not result["accepted"], "Room should reject protocol-violating tiles"
    assert "P0" in result.get("reason", ""), "Rejection should mention P0 violation"

def test_malformed_tile_structure():
    """P0: Room must handle tiles with missing required fields gracefully."""
    room = DeadbandRoom()
    agent_id = "test_agent_2"
    
    # Tile missing required 'content' field
    malformed_tile = {
        "agent_id": agent_id,
        "cycle": 101,
        "phase": 2
        # Missing 'content' field
    }
    
    result = room.submit_tile(agent_id, malformed_tile)
    assert not result["accepted"], "Room should reject malformed tiles"
    assert "missing" in result.get("reason", "").lower() or "invalid" in result.get("reason", "").lower()

def test_max_tiles_capacity():
    """P0: Room should enforce maximum tile capacity to prevent resource exhaustion."""
    room = DeadbandRoom()
    room.max_tiles = 10  # Small capacity for testing
    
    # Submit tiles until capacity reached
    for i in range(room.max_tiles + 5):
        agent_id = f"capacity_agent_{i}"
        valid_tile = {
            "agent_id": agent_id,
            "cycle": 200 + i,
            "phase": 1,
            "content": f"Test tile {i}",
            "protocol_step": "P0",
            "p0_mapped": True,
            "p1_channels": ["test_channel"]
        }
        
        result = room.submit_tile(agent_id, valid_tile)
        
        # Should reject after capacity reached
        if i >= room.max_tiles:
            assert not result["accepted"], f"Should reject tile {i} beyond capacity"
            assert "capacity" in result.get("reason", "").lower() or "full" in result.get("reason", "").lower()

