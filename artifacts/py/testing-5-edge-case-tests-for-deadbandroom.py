"""
PLATO Room: testing
Tile: 5 Edge-Case Tests for DeadbandRoom
Domain: testing
"""

def test_empty_safe_channels_after_p0_violation():
    room = DeadbandRoom()
    room.record_p0_violation("skipped_to_p2")
    safe_channels = room.identify_safe_channels()
    assert safe_channels == [] or safe_channels == ["violation_lockout"]

def test_p2_optimization_single_channel():
    room = DeadbandRoom()
    # Mock: force single safe channel
    room._safe_channels = ["only_channel"]
    result = room.optimize_within_channel("only_channel")
    assert "constrained_optimum" in result.get("flags", [])

def test_concurrent_priority_validation():
    room = DeadbandRoom()
    # Simulate concurrent validation attempts
    import threading
    results = []
    def validate_worker():
        try:
            results.append(room.validate_priority())
        except Exception as e:
            results.append(str(e))
    
    threads = [threading.Thread(target=validate_worker) for _ in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    # Should either all succeed or raise specific concurrency error
    assert len(set(results)) == 1  # Consistent outcome

def test_nested_constraint_channels():
    room = DeadbandRoom()
    # Mock: channels with sub-constraints
    room._constraint_tree = {
        "channel_a": {"sub_a1": True, "sub_a2": False},
        "channel_b": {"sub_b1": True}
    }
    channels = room.identify_safe_channels()
    # Should return either ["channel_a.sub_a1", "channel_b.sub_b1"] 
    # or structured dict
    assert len(channels) > 0
    assert any("sub_" in str(ch) for ch in channels)  # Contains sub-constraints

