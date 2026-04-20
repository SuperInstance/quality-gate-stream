"""
PLATO Room: modelexperiment
Tile: **2. Generated Code & Analysis**
Domain: modelexperiment
"""

def validate_deadband_protocol(action_sequence: list[str]) -> bool:
    """
    Validates if a sequence of agent actions follows the Deadband Protocol.
    Protocol: P0 (map negative) must come before P1 (find channels) before P2 (optimize).
    No skipping phases is allowed.
    
    Args:
        action_sequence: List of action strings like ['P0', 'P1', 'P2']
    
    Returns:
        True if sequence is valid, False otherwise.
    """
    expected_phase = "P0"
    phase_order = {"P0": "P1", "P1": "P2", "P2": None}
    
    for i, action in enumerate(action_sequence):
        if action not in phase_order:
            print(f"Violation at index {i}: Unknown action '{action}'")
            return False
        if action != expected_phase:
            print(f"Violation at index {i}: Expected '{expected_phase}', got '{action}'")
            return False
        expected_phase = phase_order[action]
    
    return True

def validate_deadband_protocol(action_sequence):
    """
    Check if actions follow P0->P1->P2 with no skips.
    """
    # Define valid transitions
    valid_transitions = {
        "P0": {"P0", "P1"},  # Can stay in P0 or move to P1
        "P1": {"P1", "P2"},  # Can stay in P1 or move to P2
        "P2": {"P2"}         # Can only stay in P2
    }
    
    if not action_sequence:
        return True  # Empty sequence is valid
    
    current = action_sequence[0]
    if current != "P0":
        print(f"First action must be P0, got {current}")
        return False
    
    for next_action in action_sequence[1:]:
        if next_action not in valid_transitions.get(current, set()):
            print(f"Invalid transition from {current} to {next_action}")
            return False
        current = next_action
    
    return True

