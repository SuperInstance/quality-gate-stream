"""
PLATO Room: testing
Tile: P2: Optimize Within Channels (Best Test Paths)
Domain: testing
"""

def test_deadband_zero_threshold_tolerance():
    """Test DeadbandRoom with zero threshold tolerance (should still function)."""
    room = DeadbandRoom(
        room_id="zero-threshold-test",
        max_cycles=10,
        p0_threshold=0.0,  # Zero tolerance
        p1_threshold=0.0,
        tile_store=Mock()
    )
    
    # Should not crash on initialization
    assert room.room_id == "zero-threshold-test"
    assert room.p0_threshold == 0.0
    
    # Test with simple actions
    actions = [{"score": 1.0}, {"score": 2.0}]
    result = room.process_actions(actions)
    
    # Should still produce valid output structure
    assert "phases" in result
    assert "optimized_path" in result

def test_p1_to_p0_regression():
    """Test that room can handle regression from P1 back to P0."""
    room = DeadbandRoom(
        room_id="regression-test",
        max_cycles=5,
        p0_threshold=0.5,
        p1_threshold=0.8,
        tile_store=Mock()
    )
    
    # Start with high-quality actions (should be P2)
    actions_high = [{"score": 0.9}, {"score": 0.95}]
    result1 = room.process_actions(actions_high)
    assert result1["current_phase"] == "P2"
    
    # Switch to very poor actions (should regress to P0)
    actions_low = [{"score": 0.1}, {"score": 0.2}]
    result2 = room.process_actions(actions_low)
    
    # Should detect regression and return to P0
    assert result2["current_phase"] == "P0"
    assert "regression_detected" in result2.get("metadata", {})

def test_mixed_validity_actions():
    """Test actions with mixed valid/invalid scores."""
    room = DeadbandRoom(
        room_id="mixed-validity-test",
        max_cycles=10,
        p0_threshold=0.3,
        p1_threshold=0.7,
        tile_store=Mock()
    )
    
    actions = [
        {"score": 0.9},        # Valid P2
        {"score": -0.1},       # Invalid (negative)
        {"score": 1.5},        # Invalid (>1.0)
        {"score": 0.5},        # Valid P1
        {"score": 0.1},        # Valid P0
        {"score": "invalid"},  # Wrong type
        None,                  # Missing action
    ]
    
    result = room.process_actions(actions)
    
    # Should filter invalid actions and process valid ones
    assert result["processed_count"] < len(actions)
    assert result["filtered_count"] > 0
    assert "validation_errors" in result.get("metadata", {})

