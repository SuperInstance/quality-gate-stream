"""
PLATO Room: testing
Tile: Action Plan
Domain: testing
"""

# test_deadbandroom_edge.py
import pytest
from plato_torch.presets.deadband_room import DeadbandRoom, ProtocolViolationError

def test_p0_violation_blocks_p1():
    """P0 violation should prevent any P1 action."""
    room = DeadbandRoom()
    room.record_p0_violation(agent_id="test_agent", violation="hit_rock")
    with pytest.raises(ProtocolViolationError):
        room.attempt_p1_action(agent_id="test_agent", action="find_channel")

def test_empty_safe_channels_raises_error():
    """If no safe channels (P1) are found, P2 optimization should fail."""
    room = DeadbandRoom()
    room.set_safe_channels([])  # Simulate no safe channels
    with pytest.raises(ValueError, match="No safe channels available"):
        room.optimize_p2(agent_id="test_agent")

def test_concurrent_agent_priority_conflict():
    """Two agents attempting P2 optimization in same channel should resolve conflict."""
    room = DeadbandRoom()
    room.set_safe_channels(["channel_a"])
    # Agent 1 enters P2
    room.enter_p2(agent_id="agent_1", channel="channel_a")
    # Agent 2 tries to enter same channel—should raise or queue
    with pytest.raises(ProtocolViolationError, match="Channel occupied"):
        room.enter_p2(agent_id="agent_2", channel="channel_a")

def test_invalid_priority_skip():
    """Skipping from P0 directly to P2 should raise error."""
    room = DeadbandRoom()
    room.record_p0_violation(agent_id="test_agent", violation="hit_rock")
    with pytest.raises(ProtocolViolationError, match="Cannot skip to P2"):
        room.optimize_p2(agent_id="test_agent")

def test_state_persistence_across_resets():
    """Ghost tiles (P0 knowledge) should persist after room reset."""
    room = DeadbandRoom()
    room.record_p0_violation(agent_id="ghost_agent", violation="critical_fail")
    ghost_tiles = room.get_ghost_tiles()
    assert len(ghost_tiles) == 1
    # Reset room but preserve ghost tiles
    room.reset()
    persisted_ghost_tiles = room.get_ghost_tiles()
    assert persisted_ghost_tiles == ghost_tiles

