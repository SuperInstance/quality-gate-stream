"""
PLATO Room: modelexperiment
Tile: **2. Function 1: `validate_deadband_protocol`**
Domain: modelexperiment
"""

def validate_deadband_protocol(steps: list[str]) -> tuple[bool, str]:
    valid_steps = {"P0", "P1", "P2"}
    seen_p1 = False
    seen_p2 = False
    
    for i, step in enumerate(steps):
        if step not in valid_steps:
            return False, f"Invalid step: {step}"
        
        if step == "P0":
            if seen_p1 or seen_p2:
                return False, f"Priority violation: P0 found after P1 or P2 at index {i}"
        elif step == "P1":
            seen_p1 = True
            if seen_p2:
                return False, f"Priority violation: P1 found after P2 at index {i}"
        elif step == "P2":
            seen_p2 = True
    
    return True, ""

def validate_deadband_protocol(steps: list[str]) -> tuple[bool, str]:
    allowed = {"P0", "P1", "P2"}
    p1_started = False
    p2_started = False
    
    for idx, step in enumerate(steps):
        if step not in allowed:
            return False, f"Invalid step: {step}"
        
        if step == "P0":
            if p1_started or p2_started:
                return False, f"Priority violation: P0 appears after P1/P2 at position {idx}"
        elif step == "P1":
            if p2_started:
                return False, f"Priority violation: P1 appears after P2 at position {idx}"
            p1_started = True
        elif step == "P2":
            p2_started = True
    
    return True, ""

