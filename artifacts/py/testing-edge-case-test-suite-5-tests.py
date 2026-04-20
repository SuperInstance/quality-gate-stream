"""
PLATO Room: testing
Tile: Edge-Case Test Suite (5 Tests)
Domain: testing
"""

def test_empty_tile_submission(self):
    """Test submission of completely empty tile (no fields)."""
    room = DeadbandRoom()
    empty_tile = {}
    
    with self.assertRaises(ValueError) as context:
        room.submit_tile(empty_tile)
    
    self.assertIn("missing required fields", str(context.exception).lower())

def test_invalid_priority_level(self):
    """Test submission with priority level outside valid range (0-2)."""
    room = DeadbandRoom()
    invalid_tile = {
        "agent_id": "test_agent",
        "cycle": 1,
        "priority": 3,  # Invalid: only 0,1,2 allowed
        "content": "Test content",
        "phase": "P0"
    }
    
    with self.assertRaises(ValueError) as context:
        room.submit_tile(invalid_tile)
    
    self.assertIn("priority must be 0, 1, or 2", str(context.exception))

def test_phase_priority_mismatch(self):
    """Test submission where phase doesn't match priority level."""
    room = DeadbandRoom()
    mismatched_tile = {
        "agent_id": "test_agent",
        "cycle": 1,
        "priority": 2,  # P2 priority
        "content": "Optimization content",
        "phase": "P0"   # But marked as P0 phase
    }
    
    with self.assertRaises(ValueError) as context:
        room.submit_tile(mismatched_tile)
    
    self.assertIn("phase must match priority", str(context.exception))

