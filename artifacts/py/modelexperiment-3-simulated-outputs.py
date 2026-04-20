"""
PLATO Room: modelexperiment
Tile: **3. Simulated Outputs**
Domain: modelexperiment
"""

# Function 1
def apply_deadband_protocol(readings: list[float]) -> list[float | None]:
    """
    Apply P0/P1/P2 Deadband Protocol to a list of readings.
    P0: Remove <= 0 (map to None).
    P1: Keep only in safe channel [0.1, 0.9].
    P2: Scale by 2.0.
    """
    result = []
    for val in readings:
        if val <= 0:  # P0: negative space
            result.append(None)
        elif 0.1 <= val <= 0.9:  # P1: safe channel
            result.append(val * 2.0)  # P2: optimize
        else:
            result.append(None)
    return result

# Function 2
import uuid

def validate_training_tile(tile: dict) -> tuple[bool, list[str]]:
    """
    Validate a training tile against fleet standards.
    """
    errors = []
    
    # Required fields
    required = ["id", "agent", "cycle", "content", "tags"]
    for field in required:
        if field not in tile:
            errors.append(f"Missing required field: {field}")
    
    # Validate id as UUID
    if "id" in tile:
        try:
            uuid.UUID(tile["id"])
        except ValueError:
            errors.append("Field 'id' must be a valid UUID string")
    
    # Validate agent non-empty string
    if "agent" in tile and not isinstance(tile["agent"], str):
        errors.append("Field 'agent' must be a string")
    elif "agent" in tile and len(tile["agent"].strip()) == 0:
        errors.append("Field 'agent' cannot be empty")
    
    # Validate cycle positive int
    if "cycle" in tile:
        if not isinstance(tile["cycle"], int):
            errors.append("Field 'cycle' must be an integer")
        elif tile["cycle"] < 0:
            errors.append("Field 'cycle' must be non-negative")
    
    # Validate content non-empty string
    if "content" in tile and not isinstance(tile["content"], str):
        errors.append("Field 'content' must be a string")
    elif "content" in tile and len(tile["content"].strip()) == 0:
        errors.append("Field 'content' cannot be empty")
    
    # Validate tags list of strings
    if "tags" in tile:
        if not isinstance(tile["tags"], list):
            errors.append("Field 'tags' must be a list")
        else:
            for i, tag in enumerate(tile["tags"]):
                if not isinstance(tag, str):
                    errors.append(f"Tag at index {i} must be a string")
    
    return (len(errors) == 0, errors)

# Function 3
import os

def resolve_fleet_path(relative_path: str) -> str:
    """
    Resolve a relative path within the fleet repo.
    Repo root: /home/fleet
    Prevent escape attempts.
    """
    root = "/home/fleet"
    # Normalize path
    normalized = os.path.normpath(os.path.join(root, relative_path))
    # Ensure it stays under root
    if not normalized.startswith(root):
        raise ValueError(f"Path escape attempt: {relative_path}")
    return normalized

