"""
PLATO Room: testing
Tile: P2: Optimized Test Paths (5 Edge-Case Tests)
Domain: testing
"""

def test_protocol_state_valid_transitions():
    """Test that room correctly tracks P0→P1→P2 progression."""
    room = DeadbandRoom(
        negative_space=["invalid_action"],
        safe_channels=["channel_a", "channel_b"],
        optimization_metric="throughput"
    )
    
    # Should start in P0
    assert room.current_phase == "P0"
    
    # Complete P0
    room.complete_phase("P0")
    assert room.current_phase == "P1"
    
    # Complete P1
    room.complete_phase("P1")
    assert room.current_phase == "P2"
    
    # Should not regress
    with pytest.raises(ProtocolViolationError):
        room.complete_phase("P1")

def test_empty_negative_space_with_channels():
    """Test handling when negative_space is empty but channels exist."""
    room = DeadbandRoom(
        negative_space=[],  # Empty P0
        safe_channels=["valid_path_a", "valid_path_b"],
        optimization_metric="latency"
    )
    
    # Room should initialize successfully
    assert room.negative_space == []
    assert len(room.safe_channels) == 2
    
    # Should be able to proceed to P1 immediately
    room.complete_phase("P0")
    assert room.current_phase == "P1"
    
    # Optimization in P2 should work normally
    result = room.optimize_channel("valid_path_a")
    assert "optimized" in result

def test_single_channel_tie_resolution():
    """Test optimization when multiple paths have identical scores."""
    room = DeadbandRoom(
        negative_space=["blocked"],
        safe_channels=["only_channel"],
        optimization_metric="score"
    )
    
    # Mock data where two optimization paths yield same score
    test_data = [
        {"path": "option_1", "score": 100},
        {"path": "option_2", "score": 100},  # Tie
        {"path": "option_3", "score": 99}
    ]
    
    room.load_optimization_data(test_data)
    
    # With ties, should select first occurrence or use tiebreaker
    result = room.optimize_channel("only_channel")
    
    # Either option_1 or option_2 is acceptable
    assert result["selected_path"] in ["option_1", "option_2"]
    assert result["score"] == 100

