"""
PLATO Room: modelexperiment
Tile: **4. Function 2: validate_tile_json**
Domain: modelexperiment
"""

from typing import Any, Dict

def validate_tile_json(tile: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a training tile dictionary against a schema.
    
    The schema should be a dict where keys are expected tile keys,
    and values are the expected types (as Python type objects).
    
    Args:
        tile: The tile dictionary to validate.
        schema: Schema dictionary mapping keys to types.
    
    Returns:
        True if tile matches schema, False otherwise.
    
    Example:
        >>> schema = {"id": str, "cycle": int, "content": str}
        >>> tile = {"id": "tile_001", "cycle": 50, "content": "test"}
        >>> validate_tile_json(tile, schema)
        True
        >>> tile2 = {"id": "tile_002", "cycle": "fifty"}
        >>> validate_tile_json(tile2, schema)
        False
    """
    if not isinstance(tile, dict) or not isinstance(schema, dict):
        return False
    
    for key, expected_type in schema.items():
        if key not in tile:
            return False
        if not isinstance(tile[key], expected_type):
            return False
    
    # Allow extra keys in tile (open-world assumption)
    return True

from typing import Dict, Any

def validate_tile_json(tile: Dict[str, Any], schema: Dict[str, type]) -> bool:
    """
    Validate a tile JSON-like dictionary against a type schema.
    
    Parameters:
        tile (Dict[str, Any]): The tile data.
        schema (Dict[str, type]): Schema mapping field names to expected types.
    
    Returns:
        bool: True if validation passes, False otherwise.
    
    Example:
        >>> schema = {"agent": str, "cycle": int, "score": float}
        >>> tile = {"agent": "alchemist", "cycle": 51, "score": 0.95}
        >>> validate_tile_json(tile, schema)
        True
        >>> tile2 = {"agent": "alchemist", "cycle": "51"}
        >>> validate_tile_json(tile2, schema)
        False
    """
    # Check inputs are dicts
    if not (isinstance(tile, dict) and isinstance(schema, dict)):
        return False
    
    # Check each schema key
    for field, field_type in schema.items():
        if field not in tile:
            return False
        if not isinstance(tile[field], field_type):
            return False
    
    # Extra fields in tile are allowed (open schema)
    return True

