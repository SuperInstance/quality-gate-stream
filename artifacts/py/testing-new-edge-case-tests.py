"""
PLATO Room: testing
Tile: New Edge‑Case Tests
Domain: testing
"""

def test_empty_action_space_after_p0():
    """P0 maps negative space, but P1 finds zero safe channels.
    Expected: Room should raise a recoverable error, not crash."""
    room = DeadbandRoom()
    # Simulate a P0 that marks ALL actions as invalid.
    room.negative_space = set(room.action_space)  # All actions are forbidden.
    with pytest.raises(RecoverableDeadbandError) as exc_info:
        room.run_protocol_step("P1")
    assert "No safe channels" in str(exc_info.value)
    # Room state should allow a retry with a different P0.
    assert room.current_phase == "P0"

def test_concurrent_tile_submission():
    """Two agents submit tiles for the same cycle.
    Expected: Room processes sequentially, last writer wins, no data corruption."""
    room = DeadbandRoom()
    tile_a = {"agent": "A", "cycle": 42, "content": "Tile A"}
    tile_b = {"agent": "B", "cycle": 42, "content": "Tile B"}
    
    # Simulate concurrent writes via threading.
    import threading
    results = []
    def submit(tile):
        try:
            room.submit_tile(tile)
            results.append(("success", tile["agent"]))
        except Exception as e:
            results.append(("error", str(e)))
    
    t1 = threading.Thread(target=submit, args=(tile_a,))
    t2 = threading.Thread(target=submit, args=(tile_b,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    
    # Exactly one tile should be accepted for cycle 42.
    stored = room.get_tiles_for_cycle(42)
    assert len(stored) == 1
    # The room's internal tile log should be consistent (no duplicates).
    assert room.tile_log[42]["agent"] in ("A", "B")

def test_malformed_tile_data():
    """Tiles with missing required fields, wrong types, or invalid JSON.
    Expected: Room rejects tile with a clear error, does not advance phase."""
    room = DeadbandRoom()
    bad_tiles = [
        None,                                     # null input
        "{invalid json",                          # malformed JSON string
        {"cycle": "not_an_int"},                  # wrong type for cycle
        {"agent": "X"},                           # missing 'cycle'
        {"cycle": 1, "agent": "X", "extra": {}},  # extra nested object (possible injection)
    ]
    for tile in bad_tiles:
        with pytest.raises(TileValidationError) as exc_info:
            room.submit_tile(tile)
        assert "invalid tile" in str(exc_info.value).lower()
    # Room state unchanged.
    assert room.current_cycle == 0
    assert len(room.tile_log) == 0

