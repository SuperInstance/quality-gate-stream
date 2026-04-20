"""
PLATO Room: testing
Tile: P2: 5 Additional Edge-Case Tests
Domain: testing
"""

def test_submit_empty_tile_returns_error():
    """P0: Empty tile content should be rejected before storage."""
    room = DeadbandRoom()
    agent_id = "test_agent_1"
    
    result = room.submit_tile(agent_id, "")
    
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()
    # Verify no tile was actually stored
    assert len(room.tile_store.tiles) == 0

def test_detect_protocol_skip_from_p0_to_p2():
    """P0: Attempting to optimize (P2) without finding channels (P1) should fail."""
    room = DeadbandRoom()
    agent_id = "test_agent_2"
    
    # Start with P0 analysis
    room.process_phase(agent_id, "P0", "Found rocks to avoid")
    
    # Attempt to jump directly to P2
    result = room.process_phase(agent_id, "P2", "Optimizing path")
    
    assert result["status"] == "error"
    assert "P1" in result["message"]  # Should mention missing P1
    assert room.get_agent_phase(agent_id) == "P0"  # Should remain at P0

def test_tile_length_limit_enforced():
    """P1: Very large tiles should be truncated or rejected based on room policy."""
    room = DeadbandRoom()
    agent_id = "test_agent_3"
    
    # Create tile exceeding reasonable limit (1MB simulated)
    large_content = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
    
    result = room.submit_tile(agent_id, large_content)
    
    # Policy could be either rejection or truncation
    assert result["status"] in ["error", "warning"]
    if result["status"] == "error":
        assert "too large" in result["message"].lower()
    else:
        assert "truncated" in result["message"].lower()

def test_recover_from_corrupted_agent_memory():
    """P1: Room should handle corrupted agent state gracefully."""
    room = DeadbandRoom()
    agent_id = "test_agent_4"
    
    # Simulate corrupted memory - invalid phase value
    room.agent_memory[agent_id] = {"phase": "INVALID_PHASE", "history": []}
    
    # Attempt normal operation
    result = room.process_phase(agent_id, "P0", "Starting over")
    
    # Should either reset agent or return error
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        assert room.get_agent_phase(agent_id) == "P0"
    else:
        assert "corrupt" in result["message"].lower() or "invalid" in result["message"].lower()

