"""
PLATO Room: testing
Tile: Edge-Case Tests for DeadbandRoom
Domain: testing
"""

def test_p0_violation_skip_to_p2():
    room = DeadbandRoom()
    agent = room.create_agent()
    # Agent tries to optimize immediately
    result = agent.execute("optimize_channel", params={"target": "throughput"})
    assert result["status"] == "violation"
    assert "P0 not satisfied" in result["message"]
    assert room.get_violation_count(agent.id) > 0

def test_p1_empty_safe_channels():
    room = DeadbandRoom()
    agent = room.create_agent()
    # Simulate P0 mapping that results in zero safe channels
    room.force_state(agent.id, {"p0_complete": True, "safe_channels": []})
    result = agent.execute("select_channel", params={"channel_id": 0})
    assert result["status"] == "error"
    assert "no safe channels" in result["message"].lower()

def test_concurrent_phases_multi_agent():
    room = DeadbandRoom()
    agent1 = room.create_agent()
    agent2 = room.create_agent()
    # Agent1 completes P0, starts P1
    agent1.execute("map_negative_space", params={"bounds": [0, 100]})
    # Agent2 tries P2 immediately (should fail)
    result2 = agent2.execute("optimize_channel")
    assert result2["status"] == "violation"
    # Agent1's state should be unaffected
    assert room.get_agent_phase(agent1.id) == "P1"
    assert room.get_agent_phase(agent2.id) == "P0"

def test_invalid_parameter_types():
    room = DeadbandRoom()
    agent = room.create_agent()
    # P0 with string instead of list
    result = agent.execute("map_negative_space", params={"bounds": "invalid"})
    assert result["status"] == "error"
    assert "type" in result["message"].lower()
    # P1 with negative channel ID
    room.force_state(agent.id, {"p0_complete": True, "safe_channels": [1, 2, 3]})
    result = agent.execute("select_channel", params={"channel_id": -1})
    assert result["status"] == "error"

