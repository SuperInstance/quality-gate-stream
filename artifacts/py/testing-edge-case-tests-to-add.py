"""
PLATO Room: testing
Tile: Edge-Case Tests to Add
Domain: testing
"""

def test_empty_interaction_rejection(self):
    """P0: Empty or null interactions should be rejected as negative space."""
    room = DeadbandRoom()
    empty_interaction = Interaction(agent_id="test_agent", content="", timestamp=time.time())
    result = room.process_interaction(empty_interaction)
    self.assertFalse(result.accepted)
    self.assertEqual(result.reason, "P0: Empty content")

def test_max_length_enforcement(self):
    """P0: Interactions exceeding MAX_CONTENT_LENGTH should be rejected."""
    room = DeadbandRoom()
    oversized_content = "x" * (room.MAX_CONTENT_LENGTH + 100)
    interaction = Interaction(agent_id="test_agent", content=oversized_content, timestamp=time.time())
    result = room.process_interaction(interaction)
    self.assertFalse(result.accepted)
    self.assertIn("P0: Content length", result.reason)

def test_concurrent_agent_interactions(self):
    """P1: Room should handle concurrent interactions from same agent (safe channel)."""
    room = DeadbandRoom()
    agent_id = "concurrent_agent"
    
    # Simulate near-simultaneous interactions
    interaction1 = Interaction(agent_id=agent_id, content="First message", timestamp=time.time())
    interaction2 = Interaction(agent_id=agent_id, content="Second message", timestamp=time.time() + 0.001)
    
    # Both should be processed independently
    result1 = room.process_interaction(interaction1)
    result2 = room.process_interaction(interaction2)
    
    self.assertTrue(result1.accepted)
    self.assertTrue(result2.accepted)
    self.assertNotEqual(result1.tile_id, result2.tile_id)

def test_malformed_tile_validation(self):
    """P0: Tiles with missing required fields should fail validation."""
    room = DeadbandRoom()
    
    # Create tile missing required 'protocol_phase' field
    malformed_tile = {
        "agent_id": "test_agent",
        "content": "Valid content",
        "timestamp": time.time()
        # Missing: "protocol_phase"
    }
    
    with self.assertRaises(ValidationError) as context:
        room._validate_tile(malformed_tile)
    
    self.assertIn("Missing required field", str(context.exception))

