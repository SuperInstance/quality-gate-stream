"""
PLATO Room: testing
Tile: 5 Additional Edge-Case Tests for DeadbandRoom
Domain: testing
"""

def test_priority_boundary_values():
    """Test that priority values outside 0-2 are rejected with appropriate error."""
    room = DeadbandRoom()
    
    # Test negative priority
    with pytest.raises(ValueError, match="Priority must be between 0 and 2"):
        room.submit_tile(priority=-1, content={"test": "data"})
    
    # Test priority > 2
    with pytest.raises(ValueError, match="Priority must be between 0 and 2"):
        room.submit_tile(priority=3, content={"test": "data"})
    
    # Test valid boundaries (0, 1, 2 should work)
    for priority in [0, 1, 2]:
        result = room.submit_tile(priority=priority, content={"test": f"data_{priority}"})
        assert result["success"] is True
        assert result["priority"] == priority

def test_concurrent_tile_submission():
    """Test that concurrent tile submissions don't corrupt room state."""
    room = DeadbandRoom()
    
    def submit_tile_thread(priority, content):
        return room.submit_tile(priority=priority, content=content)
    
    # Create multiple threads submitting tiles simultaneously
    threads = []
    results = []
    
    for i in range(10):
        t = threading.Thread(
            target=lambda i=i: results.append(
                submit_tile_thread(priority=i % 3, content={"thread": i})
            )
        )
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Verify all submissions were successful
    assert len(results) == 10
    for result in results:
        assert result["success"] is True
    
    # Verify room state consistency
    assert len(room.get_tiles()) == 10
    assert room.get_stats()["total_tiles"] == 10

def test_malformed_tile_content():
    """Test that malformed tile content is handled gracefully."""
    room = DeadbandRoom()
    
    # Test with non-dict content
    with pytest.raises(TypeError, match="Tile content must be a dictionary"):
        room.submit_tile(priority=0, content="not a dict")
    
    # Test with empty dict (should be allowed)
    result = room.submit_tile(priority=1, content={})
    assert result["success"] is True
    
    # Test with extremely large content
    large_content = {"data": "x" * 1000000}  # 1MB string
    result = room.submit_tile(priority=2, content=large_content)
    assert result["success"] is True
    
    # Test with nested structures that might cause serialization issues
    complex_content = {
        "nested": {"deep": {"deeper": [1, 2, 3]}},
        "timestamp": datetime.now()
    }
    result = room.submit_tile(priority=0, content=complex_content)
    assert result["success"] is True

