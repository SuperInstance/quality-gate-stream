"""
PLATO Room: testing
Tile: P2: Optimized Test Additions
Domain: testing
"""

def test_deadband_room_boundary_thresholds():
    """Test initialization with threshold values at system limits."""
    # Zero thresholds should be valid (no deadband)
    room = DeadbandRoom(
        p0_threshold=0.0,
        p1_threshold=0.0,
        p2_threshold=0.0,
        max_tiles=100
    )
    assert room.p0_threshold == 0.0
    assert room.p1_threshold == 0.0
    assert room.p2_threshold == 0.0
    
    # Very large thresholds (near float max)
    room = DeadbandRoom(
        p0_threshold=1e6,
        p1_threshold=1e6,
        p2_threshold=1e6,
        max_tiles=100
    )
    assert room.p0_threshold == 1e6

def test_protocol_phase_transition_conditions():
    """Test edge cases when moving between P0, P1, P2 phases."""
    room = DeadbandRoom(
        p0_threshold=0.1,
        p1_threshold=0.3,
        p2_threshold=0.5,
        max_tiles=100
    )
    
    # Start in P0
    assert room.current_phase == "P0"
    
    # Attempt P1 with insufficient confidence (below threshold)
    room._confidence = 0.05  # Below P0 threshold
    result = room.execute_protocol_step("P1")
    assert result["status"] == "blocked"
    assert "below P0 threshold" in result["message"]
    
    # Valid transition P0→P1
    room._confidence = 0.2  # Above P0, below P1
    result = room.execute_protocol_step("P1")
    assert result["status"] == "success"
    assert room.current_phase == "P1"

def test_tile_submission_at_capacity():
    """Test behavior when submitting tiles at max_tiles limit."""
    room = DeadbandRoom(
        p0_threshold=0.1,
        p1_threshold=0.3,
        p2_threshold=0.5,
        max_tiles=3  # Small limit for testing
    )
    
    # Fill to capacity
    for i in range(3):
        tile = {"id": f"tile_{i}", "content": f"test_{i}"}
        result = room.submit_tile(tile)
        assert result["status"] == "accepted"
    
    # Attempt to exceed capacity
    tile = {"id": "tile_overflow", "content": "should_fail"}
    result = room.submit_tile(tile)
    assert result["status"] == "rejected"
    assert "capacity" in result["message"].lower()
    
    # Verify existing tiles preserved
    assert len(room.tiles) == 3

