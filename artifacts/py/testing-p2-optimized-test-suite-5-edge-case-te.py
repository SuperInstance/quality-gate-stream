"""
PLATO Room: testing
Tile: P2: Optimized Test Suite (5 Edge-Case Tests)
Domain: testing
"""

def test_protocol_rollback_on_invalid_p2_tile():
    """Test that submitting an invalid tile at P2 rolls back to P1 state."""
    room = DeadbandRoom()
    
    # Successfully complete P0 and P1
    room.process_tile({"phase": "P0", "content": "negative_space", "agent_id": "test_agent"})
    room.process_tile({"phase": "P1", "content": "safe_channel", "agent_id": "test_agent"})
    assert room.current_protocol_phase == "P1"
    
    # Submit invalid P2 tile (missing required optimization metrics)
    invalid_p2_tile = {
        "phase": "P2",
        "content": "optimization_attempt",
        "agent_id": "test_agent"
        # Missing "metrics" field required for P2
    }
    
    with pytest.raises(ValueError, match="P2 tiles require optimization metrics"):
        room.process_tile(invalid_p2_tile)
    
    # Verify protocol state rolled back to P1
    assert room.current_protocol_phase == "P1"
    assert len(room.rejected_tiles) == 1

def test_concurrent_tile_submission_ordering():
    """Test that tiles from multiple agents maintain submission order."""
    room = DeadbandRoom()
    
    # Simulate concurrent submissions with timestamps
    tiles = [
        {"phase": "P0", "content": "agent1_p0", "agent_id": "agent1", "timestamp": 1000},
        {"phase": "P0", "content": "agent2_p0", "agent_id": "agent2", "timestamp": 1001},
        {"phase": "P0", "content": "agent3_p0", "agent_id": "agent3", "timestamp": 1002},
    ]
    
    # Process in random order
    import random
    random.shuffle(tiles)
    
    for tile in tiles:
        room.process_tile(tile)
    
    # Verify tiles are stored in timestamp order, not submission order
    stored_timestamps = [t.get("timestamp") for t in room.processed_tiles]
    assert stored_timestamps == [1000, 1001, 1002]

def test_tile_storage_limit_enforcement():
    """Test that room enforces maximum tile storage limit."""
    room = DeadbandRoom(max_tiles=5)  # Small limit for testing
    
    # Fill to capacity
    for i in range(5):
        tile = {
            "phase": "P0",
            "content": f"tile_{i}",
            "agent_id": "test_agent"
        }
        room.process_tile(tile)
    
    assert len(room.processed_tiles) == 5
    
    # Attempt to exceed limit
    excess_tile = {
        "phase": "P0",
        "content": "excess_tile",
        "agent_id": "test_agent"
    }
    
    with pytest.raises(RuntimeError, match="Tile storage limit reached"):
        room.process_tile(excess_tile)
    
    # Verify count unchanged
    assert len(room.processed_tiles) == 5

