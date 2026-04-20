"""
PLATO Room: modelexperiment
Tile: **2. Simulated Model Outputs & Analysis**
Domain: modelexperiment
"""

def validate_deadband_protocol(steps: list[str]) -> tuple[bool, str]:
        valid_sequence = ['P0', 'P1', 'P2']
        expected_index = 0
        
        for i, step in enumerate(steps):
            if step not in valid_sequence:
                return (False, f"Error: Invalid step '{step}' at position {i}. Must be 'P0', 'P1', or 'P2'.")
            if step != valid_sequence[expected_index]:
                return (False, f"Error: Unexpected '{step}' at position {i}. Expected '{valid_sequence[expected_index]}'.")
            expected_index += 1
        
        if expected_index < len(valid_sequence):
            return (False, f"Error: Sequence incomplete. Missing '{valid_sequence[expected_index]}'.")
        
        return (True, "")

def validate_deadband_protocol(steps):
        order = {'P0': 0, 'P1': 1, 'P2': 2}
        last_index = -1
        for step in steps:
            if step not in order:
                return False, f"Invalid step {step}"
            current_index = order[step]
            if current_index != last_index + 1:
                return False, f"Protocol violation: {step} out of sequence"
            last_index = current_index
        return True, ""

