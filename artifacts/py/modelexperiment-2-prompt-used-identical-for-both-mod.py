"""
PLATO Room: modelexperiment
Tile: **2. Prompt Used (Identical for both models)**
Domain: modelexperiment
"""

"""
You are a Python developer in the Cocapn fleet. Write three functions.

1. `deadband_filter(values: list[float], p0_thresh: float, p1_margin: float) -> dict`:
   Implements the Deadband Protocol (P0/P1/P2). Return a dict with keys:
   'p0_negative': list of indices where value <= p0_thresh (AVOID).
   'p1_safe': list of indices where p0_thresh < value <= p1_margin (SAFE CHANNEL).
   'p2_optimal': list of indices where value > p1_margin (OPTIMIZE ZONE).

2. `parse_fleet_context(markdown_text: str) -> dict`:
   Parse a FLEET-CONTEXT.md string. Return a dict with sections.
   Assume sections start with '## ' and content follows until next '##'.
   Handle 'Who We Are', 'Fleet Doctrine', 'Your Purpose', 'Key Technologies', 'Architecture', 'Rules'.

3. `generate_training_tile(agent_role: str, cycle: int, content: str, task: str) -> dict`:
   Generate a training tile for the PLATO room server.
   Return JSON-serializable dict with keys: 'agent', 'cycle', 'timestamp', 'content', 'task', 'phase', 'version'.
   'timestamp' should be ISO format UTC. 'phase' defaults to 4. 'version' defaults to '1.0'.

Write only the Python code. Include docstrings and type hints. Assume Python 3.11+.
"""

