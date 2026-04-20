"""
PLATO Room: testing
Tile: 5 Additional Edge-Case Tests
Domain: testing
"""

def test_concurrent_agent_deadlock():
    """Test that multiple agents can't create circular constraints in P0."""
    room = DeadbandRoom()
    agent1 = MockAgent()
    agent2 = MockAgent()
    
    # Agent 1 defines constraint that conflicts with Agent 2's constraint
    agent1.submit_tile({"phase": "P0", "constraint": "no_red_blocks"})
    agent2.submit_tile({"phase": "P0", "constraint": "only_red_blocks"})
    
    # Room should detect conflicting constraints and reject one
    conflicts = room.detect_constraint_conflicts()
    assert len(conflicts) > 0
    assert room.state["phase"] == "P0"  # Should remain in P0 until resolved

def test_malformed_tile_recovery():
    """Test room recovery from malformed tile submissions."""
    room = DeadbandRoom()
    
    # Submit intentionally malformed tiles
    malformed_tiles = [
        {"invalid_key": "value"},  # Missing phase
        {"phase": "P5"},  # Invalid phase
        {"phase": "P1", "channel": None},  # Null channel
        {"phase": "P2", "optimization": {"invalid": "data"}},  # Invalid structure
    ]
    
    for tile in malformed_tiles:
        try:
            room.process_tile(tile)
        except TileValidationError:
            pass  # Expected
    
    # Room should maintain stable state despite malformed inputs
    assert room.state["phase"] in ["P0", "P1", "P2"]
    assert room.error_count < len(malformed_tiles)  # Some may be caught before counting

def test_memory_exhaustion_protection():
    """Test room behavior when tile storage approaches limits."""
    room = DeadbandRoom(max_tiles=100)
    
    # Flood with valid tiles
    for i in range(150):
        tile = {
            "phase": "P0",
            "constraint": f"test_constraint_{i}",
            "timestamp": time.time()
        }
        
        if i < 100:
            # First 100 should succeed
            assert room.process_tile(tile) is True
        else:
            # After 100, should reject or trigger cleanup
            result = room.process_tile(tile)
            if result is False:
                assert room.tile_count <= 100  # Enforced limit

