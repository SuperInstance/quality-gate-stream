"""
PLATO Room: modelexperiment
Tile: **2. Code Generation**
Domain: modelexperiment
"""

# Function A: validate_deadband_protocol
from typing import List, Dict, Any

def validate_deadband_protocol(actions: List[str]) -> Dict[str, Any]:
    """
    Validates a sequence of actions against the Deadband Protocol.
    The protocol requires phases to be completed in order: P0 (map negative space)
    must occur before P1 (find safe channels), which must occur before P2 (optimize).

    Args:
        actions: A list of action strings. Assumes actions contain phase markers
                 like 'P0', 'P1', or 'P2'.

    Returns:
        A dictionary with keys:
        - is_valid (bool): True if the sequence respects P0->P1->P2 order.
        - violations (List[str]): Descriptions of any order violations found.
        - phase_counts (Dict[str, int]): Count of actions per phase.
    """
    phase_order = {'P0': 0, 'P1': 1, 'P2': 2}
    last_phase_index = -1
    violations = []
    phase_counts = {p: 0 for p in phase_order}

    for i, action in enumerate(actions):
        # Extract phase from action (simple substring check)
        current_phase = None
        for phase in phase_order:
            if phase in action:
                current_phase = phase
                break

        if current_phase:
            phase_counts[current_phase] += 1
            current_index = phase_order[current_phase]

            if current_index < last_phase_index:
                violations.append(
                    f"Position {i}: '{action}' (phase {current_phase}) "
                    f"appears after a higher phase."
                )
            last_phase_index = max(last_phase_index, current_index)

    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        'phase_counts': phase_counts
    }

