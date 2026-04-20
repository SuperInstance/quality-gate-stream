"""
PLATO Room: testing
Tile: Edge-Case Tests
Domain: testing
"""

def test_protocol_phase_skip_violation():
    """Test that skipping from P0 directly to P2 raises appropriate error."""
    room = DeadbandRoom()
    
    # Start with P0 mapping
    room.state = {
        'phase': 'P0',
        'negative_space': ['invalid_action_1', 'invalid_action_2'],
        'safe_channels': [],
        'optimized_path': None
    }
    
    # Attempt to skip to P2 optimization without P1
    with pytest.raises(ProtocolViolationError) as exc_info:
        room._apply_deadband_protocol('P2', {'action': 'optimize_prematurely'})
    
    assert "Cannot skip from P0 to P2" in str(exc_info.value)
    assert room.state['phase'] == 'P0'  # State should remain unchanged

def test_malformed_tile_structure():
    """Test processing tiles with missing required fields."""
    room = DeadbandRoom()
    
    # Tile missing 'content' field
    invalid_tile_1 = {
        'agent_id': 'test_agent',
        'timestamp': '2026-04-19T21:45:00Z'
        # Missing 'content' field
    }
    
    # Tile with wrong data type for content
    invalid_tile_2 = {
        'agent_id': 'test_agent',
        'timestamp': '2026-04-19T21:45:00Z',
        'content': 12345  # Should be string or dict
    }
    
    with pytest.raises(InvalidTileError) as exc_info:
        room.process_tile(invalid_tile_1)
    assert "Missing required field" in str(exc_info.value)
    
    with pytest.raises(InvalidTileError) as exc_info:
        room.process_tile(invalid_tile_2)
    assert "Invalid content type" in str(exc_info.value)

def test_state_persistence_across_phases():
    """Test that negative_space from P0 persists through P1 and P2."""
    room = DeadbandRoom()
    
    # P0: Map negative space
    p0_negative_space = ['rock_1', 'rock_2', 'hazard_zone']
    room._apply_deadband_protocol('P0', {'negative_space': p0_negative_space})
    
    # P1: Find safe channels (should preserve negative space)
    room._apply_deadband_protocol('P1', {'safe_channels': ['channel_a', 'channel_b']})
    
    # P2: Optimize path (should preserve both)
    room._apply_deadband_protocol('P2', {'optimized_path': ['channel_a', 'point_1', 'point_2']})
    
    # Verify all phases' data persists
    assert room.state['negative_space'] == p0_negative_space
    assert room.state['safe_channels'] == ['channel_a', 'channel_b']
    assert room.state['optimized_path'] == ['channel_a', 'point_1', 'point_2']
    assert room.state['phase'] == 'P2'

