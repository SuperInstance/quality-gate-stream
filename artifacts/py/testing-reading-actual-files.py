"""
PLATO Room: testing
Tile: Reading Actual Files
Domain: testing
"""

# deadband_room.py - DeadbandRoom preset for plato-torch
import torch
from typing import Dict, List, Optional
from .base_room import BaseRoom

class DeadbandRoom(BaseRoom):
    """A training room that enforces the Deadband Protocol (P0, P1, P2)."""
    
    def __init__(self, room_id: str, config: Dict):
        super().__init__(room_id, config)
        self.current_phase = "P0"  # Start with negative space mapping
        self.tiles_submitted = 0
        self.safe_channels = []
        self.optimization_paths = []
    
    def submit_tile(self, tile: Dict) -> bool:
        """Submit a training tile. Returns True if accepted."""
        # P0: Reject tiles that violate negative space
        if self._violates_p0(tile):
            return False
        
        # P1: Check if tile is in a safe channel
        if not self._in_safe_channel(tile):
            return False
        
        # P2: Optimize and store
        optimized = self._optimize_p2(tile)
        self.tiles.append(optimized)
        self.tiles_submitted += 1
        return True
    
    def _violates_p0(self, tile: Dict) -> bool:
        """Check if tile violates P0 constraints."""
        # Example: tile missing required fields
        required = ["agent_id", "cycle", "content"]
        for field in required:
            if field not in tile:
                return True
        # Additional P0 rules
        if tile.get("phase") not in ["P0", "P1", "P2"]:
            return True
        return False
    
    def _in_safe_channel(self, tile: Dict) -> bool:
        """Check if tile is in a known safe channel."""
        # Simplified: safe if agent_id is registered
        return tile.get("agent_id") in self.registered_agents
    
    def _optimize_p2(self, tile: Dict) -> Dict:
        """Apply P2 optimization to tile."""
        # Add metadata
        tile["optimized_at"] = torch.tensor([self.tiles_submitted])
        tile["phase"] = self.current_phase
        return tile
    
    def set_phase(self, phase: str):
        """Change the current Deadband Protocol phase."""
        if phase in ["P0", "P1", "P2"]:
            self.current_phase = phase
        else:
            raise ValueError(f"Invalid phase: {phase}")

