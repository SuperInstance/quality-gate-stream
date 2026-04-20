"""
PLATO Room: modelexperiment
Tile: **3. Function 2: Tile Validator**
Domain: modelexperiment
"""

import re
from datetime import datetime

def validate_tile(tile):
    """
    Validate a training tile for fleet submission.
    Returns (is_valid, errors).
    """
    required_keys = {"agent_id", "cycle", "phase", "content", "timestamp"}
    errors = []
    
    # Check all required keys present
    missing = required_keys - set(tile.keys())
    if missing:
        errors.append(f"Missing keys: {missing}")
    
    # Check content
    if "content" in tile:
        if not isinstance(tile["content"], str) or not tile["content"].strip():
            errors.append("Content must be non-empty string")
    
    # Check timestamp format (ISO 8601)
    if "timestamp" in tile:
        ts_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$'
        if not re.match(ts_pattern, tile["timestamp"]):
            errors.append("Timestamp must be ISO 8601 format")
    
    # Check cycle/phase are integers
    if "cycle" in tile and not isinstance(tile["cycle"], int):
        errors.append("Cycle must be integer")
    if "phase" in tile and not isinstance(tile["phase"], int):
        errors.append("Phase must be integer")
    
    return (len(errors) == 0, errors)

def validate_tile(tile):
    """
    Validates a training tile dictionary.
    """
    errors = []
    
    # Required fields check
    required = ['agent_id', 'cycle', 'phase', 'content', 'timestamp']
    for key in required:
        if key not in tile:
            errors.append(f"Missing required field: {key}")
    
    if 'content' in tile:
        if not tile['content'] or not isinstance(tile['content'], str):
            errors.append("Content must be a non-empty string")
    
    if 'timestamp' in tile:
        try:
            datetime.fromisoformat(tile['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Timestamp must be valid ISO 8601")
    
    return (len(errors) == 0, errors)

