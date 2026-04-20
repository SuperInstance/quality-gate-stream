"""
PLATO Room: modelexperiment
Tile: **2. Code Generation & Comparison**
Domain: modelexperiment
"""

def validate_deadband_protocol(steps: list[str]) -> dict:
    """
    Validates a list of procedural steps against the Deadband Protocol.
    The protocol requires strict priority order: P0 (map negative space) ->
    P1 (find safe channels) -> P2 (optimize within channels).
    Returns a dict with 'valid' (bool) and 'violations' (list of error strings).
    """
    # Define priority order mapping
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
    violations = []
    last_priority = -1  # Start before P0

    for i, step in enumerate(steps):
        # Extract priority tag from step (assumes format like "[P1] Find channels")
        step_upper = step.upper()
        detected_priority = None
        for tag in priority_order:
            if tag in step_upper:
                detected_priority = priority_order[tag]
                break

        if detected_priority is None:
            violations.append(f"Step {i}: '{step}' has no detectable P0/P1/P2 tag.")
            continue

        # Check for order violation
        if detected_priority < last_priority:
            violations.append(
                f"Step {i}: Priority regression from {list(priority_order.keys())[last_priority]} "
                f"to {list(priority_order.keys())[detected_priority]} in '{step}'."
            )
        last_priority = detected_priority

    return {'valid': len(violations) == 0, 'violations': violations}

def validate_deadband_protocol(steps):
    """
    Validate steps against Deadband Protocol priorities P0, P1, P2.
    Steps must appear in non-decreasing priority order.
    """
    priority_map = {'P0': 0, 'P1': 1, 'P2': 2}
    violations = []
    max_seen = -1

    for idx, step in enumerate(steps):
        step_upper = step.upper()
        found = None
        for p in priority_map:
            if p in step_upper:
                found = priority_map[p]
                break
        if found is None:
            violations.append(f"Step {idx} missing priority tag: {step}")
            continue
        if found < max_seen:
            violations.append(f"Step {idx} violates order: {step} (current P{found}, previous P{max_seen})")
        else:
            max_seen = found

    return {'valid': not violations, 'violations': violations}

