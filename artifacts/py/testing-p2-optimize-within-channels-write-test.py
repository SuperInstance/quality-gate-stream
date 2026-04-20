"""
PLATO Room: testing
Tile: P2: Optimize Within Channels (Write Tests)
Domain: testing
"""

def test_skip_to_p2_violation():
    room = DeadbandRoom()
    agent_id = room.register_agent("test_agent")
    # Agent tries to perform a P2 optimization action without completing P0 and P1
    result = room.submit_action(agent_id, {"phase": "P2", "action": "optimize_path"})
    assert result["status"] == "rejected"
    assert "P0 not completed" in result["message"]

def test_empty_p0_map():
    room = DeadbandRoom()
    agent_id = room.register_agent("test_agent")
    result = room.submit_action(agent_id, {"phase": "P0", "constraints": []})
    assert result["status"] == "invalid"
    assert "at least one constraint" in result["message"]

def test_p1_overlaps_p0():
    room = DeadbandRoom()
    agent_id = room.register_agent("test_agent")
    # First, submit P0 constraints
    room.submit_action(agent_id, {"phase": "P0", "constraints": ["avoid_rock_x"]})
    # Then submit P1 safe channels that include the forbidden area
    result = room.submit_action(agent_id, {"phase": "P1", "channels": ["channel_near_rock_x"]})
    assert result["status"] == "inconsistent"
    assert "overlaps with P0" in result["message"]

def test_p1_channel_limit():
    room = DeadbandRoom()
    agent_id = room.register_agent("test_agent")
    room.submit_action(agent_id, {"phase": "P0", "constraints": ["avoid_rock_y"]})
    # Generate excessive channels
    channels = [f"channel_{i}" for i in range(10000)]
    result = room.submit_action(agent_id, {"phase": "P1", "channels": channels})
    assert result["status"] == "rejected"
    assert "exceeds limit" in result["message"]

