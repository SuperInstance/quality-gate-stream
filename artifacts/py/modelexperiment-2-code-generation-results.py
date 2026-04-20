"""
PLATO Room: modelexperiment
Tile: **2. Code Generation Results**
Domain: modelexperiment
"""

def validate_deadband_protocol(steps: list[str]) -> tuple[bool, str]:
    """
    Validates if a list of steps follows the Deadband Protocol priority order.
    Rules:
    1. At least one step must start with "P0:" (case-sensitive).
    2. No step starting with "P2:" may appear before a step starting with "P1:".
    Returns a tuple (is_valid, error_message).
    """
    has_p0 = any(step.strip().startswith("P0:") for step in steps)
    if not has_p0:
        return False, "P0 step missing"

    seen_p1 = False
    for step in steps:
        if step.strip().startswith("P1:"):
            seen_p1 = True
        if step.strip().startswith("P2:") and not seen_p1:
            return False, "P2 before P1"

    return True, ""

def validate_deadband_protocol(steps: list[str]) -> tuple[bool, str]:
    """
    Validate the Deadband Protocol steps.
    The protocol requires:
    - At least one P0 step
    - No P2 step before a P1 step
    """
    # Check for P0
    p0_present = any(step.startswith("P0:") for step in steps)
    if not p0_present:
        return (False, "P0 step missing")

    # Check P2 before P1
    p1_seen = False
    for step in steps:
        if step.startswith("P1:"):
            p1_seen = True
        elif step.startswith("P2:") and not p1_seen:
            return (False, "P2 before P1")

    return (True, "")

