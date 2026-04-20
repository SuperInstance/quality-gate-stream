"""
PLATO Room: testing
Tile: Edge-Case Tests Written
Domain: testing
"""

def test_empty_tile_data(self):
    """P0: Empty tile should be rejected (no data to validate)"""
    result = self.room.process_tile({})
    self.assertFalse(result["valid"])
    self.assertEqual(result["reason"], "empty_tile_data")

def test_malformed_priority_structure(self):
    """P0: Tile missing priority levels should be rejected"""
    tile = {"action": "move", "data": {"x": 10, "y": 20}}  # No P0/P1/P2
    result = self.room.process_tile(tile)
    self.assertFalse(result["valid"])
    self.assertIn("missing_priority", result["reason"])

def test_p1_channel_boundary_conditions(self):
    """P1: Action at exact channel boundaries should be accepted"""
    # Test minimum and maximum allowed values for safe channels
    tile = {
        "p0": {"prohibited": []},
        "p1": {"channel": "navigation", "value": 0.0},  # Minimum boundary
        "p2": {"optimization_score": 0.5}
    }
    result = self.room.process_tile(tile)
    self.assertTrue(result["valid"])
    self.assertEqual(result["p1_status"], "boundary_accepted")

def test_concurrent_tile_processing(self):
    """Handle multiple tiles submitted in rapid sequence"""
    import threading
    
    results = []
    def submit_tile(tile_id):
        tile = {
            "p0": {"prohibited": []},
            "p1": {"channel": f"channel_{tile_id}", "value": 0.5},
            "p2": {"optimization_score": 0.7}
        }
        results.append(self.room.process_tile(tile))
    
    threads = [threading.Thread(target=submit_tile, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All should be valid and have unique storage IDs
    valid_count = sum(1 for r in results if r["valid"])
    self.assertEqual(valid_count, 5)
    storage_ids = [r.get("storage_id") for r in results if r.get("storage_id")]
    self.assertEqual(len(set(storage_ids)), 5)  # All unique

def test_p2_optimization_rollback(self):
    """P2: When optimization fails, ensure no partial state persists"""
    # Simulate P2 validation failure after successful P0/P1
    original_tile_count = self.room.get_tile_count()
    
    tile = {
        "p0": {"prohibited": []},
        "p1": {"channel": "valid_channel", "value": 0.5},
        "p2": {"optimization_score": -1.0}  # Invalid score (< 0)
    }
    
    result = self.room.process_tile(tile)
    self.assertFalse(result["valid"])
    self.assertIn("invalid_p2_score", result["reason"])
    
    # Verify no tile was stored
    new_tile_count = self.room.get_tile_count()
    self.assertEqual(original_tile_count, new_tile_count)

