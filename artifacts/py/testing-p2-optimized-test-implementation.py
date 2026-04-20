"""
PLATO Room: testing
Tile: P2: Optimized Test Implementation
Domain: testing
"""

def test_p0_empty_constraints():
    """Test P0 phase with empty constraint set (no negative space)."""
    room = DeadbandRoom(room_id="test_empty_constraints")
    agent = MockAgent()
    
    # Empty constraints should still complete P0 successfully
    result = room.execute_phase(agent, phase="P0", constraints=[])
    assert result["status"] == "complete"
    assert result["constraints_mapped"] == 0
    assert "P1" in result["next_phase"]

def test_p1_overlapping_channels():
    """Test P1 with multiple overlapping safe channels."""
    room = DeadbandRoom(room_id="test_overlap")
    agent = MockAgent()
    
    # Complete P0 first
    room.execute_phase(agent, phase="P0", constraints=["rock", "wall"])
    
    # Define overlapping safe channels
    channels = [
        {"x": (0, 10), "y": (0, 10)},
        {"x": (5, 15), "y": (5, 15)},
        {"x": (8, 12), "y": (8, 12)}
    ]
    
    result = room.execute_phase(agent, phase="P1", safe_channels=channels)
    assert result["status"] == "complete"
    assert len(result["valid_channels"]) > 1
    assert "overlap_zone" in result

def test_p1_zero_width_channel():
    """Test P1 with a channel that has zero width in one dimension."""
    room = DeadbandRoom(room_id="test_zero_width")
    agent = MockAgent()
    
    room.execute_phase(agent, phase="P0", constraints=["cliff"])
    
    # Channel with zero width in y dimension
    channels = [{"x": (0, 10), "y": (5, 5)}]  # y range has zero width
    
    result = room.execute_phase(agent, phase="P1", safe_channels=channels)
    # Should either reject or handle as degenerate case
    assert result["status"] in ["complete", "degenerate"]
    if result["status"] == "degenerate":
        assert "zero_width" in result["flags"]

def test_protocol_reset():
    """Test agent can reset from P2 back to P0 with new constraints."""
    room = DeadbandRoom(room_id="test_reset")
    agent = MockAgent()
    
    # Complete full protocol
    room.execute_phase(agent, phase="P0", constraints=["rock"])
    room.execute_phase(agent, phase="P1", safe_channels=[{"x": (0, 10), "y": (0, 10)}])
    room.execute_phase(agent, phase="P2", optimization_target="speed")
    
    # Reset to P0 with new constraints
    result = room.execute_phase(agent, phase="P0", constraints=["rock", "pit", "wall"])
    assert result["status"] == "complete"
    assert result["constraints_mapped"] == 3
    assert room.get_agent_phase(agent) == "P0"

