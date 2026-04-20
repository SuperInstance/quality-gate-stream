"""
PLATO Room: testing
Tile: Edge-Case Tests to Write
Domain: testing
"""

def test_concurrent_p2_before_p0_violation():
    """Test that P2 optimization cannot proceed if P0 negative space is empty."""
    room = DeadbandRoom()
    # Attempt to add P2 tile without establishing P0
    with pytest.raises(ValueError, match="P0 must be established before P2"):
        room.process_tile({
            "phase": "P2",
            "content": "Optimize path",
            "priority": 2
        })

def test_safe_channel_overlaps_negative_space():
    """Test that safe channels cannot overlap with mapped negative space."""
    room = DeadbandRoom()
    # First establish P0 negative space
    room.process_tile({
        "phase": "P0",
        "negative_space": ["rock", "shoal", "vortex"],
        "priority": 0
    })
    
    # Attempt to define safe channel that includes negative space
    with pytest.raises(ValueError, match="Safe channel cannot contain negative space"):
        room.process_tile({
            "phase": "P1",
            "safe_channels": [{"path": "north", "hazards": ["rock"]}],  # Contains 'rock' from P0
            "priority": 1
        })

def test_state_recovery_after_corruption():
    """Test that room can recover from partially corrupted state."""
    room = DeadbandRoom()
    # Simulate corrupted state (missing required keys)
    room.state = {"negative_space": []}  # Missing safe_channels, optimized_paths
    
    # Room should rebuild missing state on next tile
    tile = {
        "phase": "P0",
        "negative_space": ["new_hazard"],
        "priority": 0
    }
    
    result = room.process_tile(tile)
    assert "safe_channels" in room.state
    assert "optimized_paths" in room.state
    assert room.state["negative_space"] == ["new_hazard"]

def test_tile_priority_inversion():
    """Test detection of tiles submitted out of priority sequence."""
    room = DeadbandRoom()
    # Establish P0
    room.process_tile({
        "phase": "P0",
        "negative_space": ["hazard1"],
        "priority": 0
    })
    
    # Establish P1
    room.process_tile({
        "phase": "P1",
        "safe_channels": [{"path": "safe1", "hazards": []}],
        "priority": 1
    })
    
    # Attempt to submit another P0 tile after P1 (should be allowed for updates)
    # But with lower priority value than current phase
    result = room.process_tile({
        "phase": "P0",
        "negative_space": ["hazard1", "hazard2"],  # Updating P0
        "priority": 0
    })
    
    # Should succeed - P0 updates are allowed even after P1 established
    assert "hazard2" in room.state["negative_space"]

