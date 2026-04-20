"""
PLATO Room: documentation
Tile: API / Usage
Domain: documentation
"""

from fleet_simulator import SimulationEngine
    engine = SimulationEngine(scenario_path="my_scenario.yaml")
    engine.run_for_cycles(50)
    tiles = engine.get_tiles()

