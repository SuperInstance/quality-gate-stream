"""
PLATO Room: modelexperiment
Tile: **3. DeepSeek-chat Implementation**
Domain: modelexperiment
"""

# Function 1: deadband_filter
def deadband_filter(values: list[float], deadband: float = 0.1) -> list[float]:
    """
    Apply deadband filtering to a list of float values.
    """
    if not values:
        return []
    
    result = []
    for val in values:
        if abs(val) <= deadband:
            result.append(0.0)
        else:
            result.append(val)
    return result

# Function 2: parse_fleet_log
import re

def parse_fleet_log(log_text: str) -> list[dict]:
    """
    Parse a fleet log string into structured events.
    """
    if not log_text or not log_text.strip():
        return []
    
    pattern = r'\[([^\]]+)\] (\w+): (.+)'
    events = []
    
    for line in log_text.strip().split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            timestamp, agent, message = match.groups()
            events.append({
                "timestamp": timestamp.strip(),
                "agent": agent.strip(),
                "message": message.strip()
            })
    
    return events

# Function 3: validate_tile
import uuid
from datetime import datetime

def validate_tile(tile: dict) -> tuple[bool, list[str]]:
    """
    Validate a training tile against fleet schema.
    """
    errors = []
    required_keys = ["id", "agent", "cycle", "content", "timestamp"]
    
    # Check required keys
    for key in required_keys:
        if key not in tile:
            errors.append(f"Missing required key: {key}")
    
    if errors:
        return False, errors
    
    # Validate id (UUID format)
    try:
        uuid.UUID(tile["id"])
    except ValueError:
        errors.append("Invalid UUID format for 'id'")
    
    # Validate agent (known agents from fleet context)
    known_agents = {"Alchemist", "Navigator", "Sentinel", "Scribe", "Tinker", 
                    "Scout", "Curator", "Mason", "Herald", "Scholar", 
                    "Weaver", "Archivist"}
    if tile["agent"] not in known_agents:
        errors.append(f"Unknown agent: {tile['agent']}")
    
    # Validate cycle (positive integer)
    if not isinstance(tile["cycle"], int) or tile["cycle"] <= 0:
        errors.append("Cycle must be positive integer")
    
    # Validate content (non-empty string)
    if not isinstance(tile["content"], str) or not tile["content"].strip():
        errors.append("Content must be non-empty string")
    
    # Validate timestamp (ISO 8601)
    try:
        datetime.fromisoformat(tile["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        errors.append("Invalid ISO 8601 timestamp")
    
    return len(errors) == 0, errors

