"""
PLATO Room: testing
Tile: Action: Reading the Code
Domain: testing
"""

# plato-torch/src/presets/deadband_room.py
"""
DeadbandRoom - A training room that enforces the Deadband Protocol (P0, P1, P2).
Agents submit tiles (interaction data). The room validates them against protocol rules.
"""

class DeadbandRoom:
    def __init__(self, room_id: str, config: dict = None):
        self.room_id = room_id
        self.config = config or {}
        self.tiles = []  # List of validated tile dicts
        self.phase = "P0"  # Current protocol phase: P0, P1, or P2
        self.violations = 0

    def submit_tile(self, agent_id: str, tile_data: dict) -> dict:
        """
        Submit a training tile. Returns result dict with keys:
        - 'accepted': bool
        - 'reason': str
        - 'new_phase': str | None
        """
        # P0: Check for violations (negative space)
        if self._check_p0_violation(tile_data):
            self.violations += 1
            return {"accepted": False, "reason": "P0 violation", "new_phase": None}

        # P1: Check if tile is in a safe channel
        if not self._check_p1_safe(tile_data):
            return {"accepted": False, "reason": "Not in safe channel", "new_phase": None}

        # P2: Optimize - tile accepted
        self.tiles.append({
            "agent_id": agent_id,
            "data": tile_data,
            "timestamp": time.time()
        })
        # Phase transition logic
        new_phase = self._evaluate_phase_transition()
        return {"accepted": True, "reason": "Tile accepted", "new_phase": new_phase}

    def _check_p0_violation(self, tile_data: dict) -> bool:
        """Check for absolute claims, hallucinations, off-limits topics."""
        content = tile_data.get("content", "")
        # Example violation: absolute language
        absolute_indicators = ["always", "never", "guaranteed", "certainly"]
        for word in absolute_indicators:
            if word in content.lower():
                return True
        return False

    def _check_p1_safe(self, tile_data: dict) -> bool:
        """Check if tile references known fleet files, repos, or patterns."""
        # Safe if it references a fleet-knowledge/ file or a known repo
        content = tile_data.get("content", "")
        return ("fleet-knowledge/" in content) or ("plato-torch" in content)

    def _evaluate_phase_transition(self) -> str:
        """Move from P0->P1 after 5 tiles, P1->P2 after 10 more."""
        if self.phase == "P0" and len(self.tiles) >= 5:
            self.phase = "P1"
        elif self.phase == "P1" and len(self.tiles) >= 15:
            self.phase = "P2"
        return self.phase

