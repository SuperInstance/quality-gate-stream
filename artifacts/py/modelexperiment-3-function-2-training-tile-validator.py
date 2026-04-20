"""
PLATO Room: modelexperiment
Tile: **3. Function 2: Training Tile Validator**
Domain: modelexperiment
"""

def validate_tile(tile):
    """
    Validate a training tile for submission to PLATO room server.

    Args:
        tile (dict): The tile dictionary to validate.

    Returns:
        tuple: (is_valid(bool), message(str))
    """
    # Check required keys
    required_keys = ['content', 'agent_id', 'cycle', 'phase']
    for key in required_keys:
        if key not in tile:
            return False, f"Missing required key: {key}"
    
    # Check content
    if not isinstance(tile['content'], str) or not tile['content'].strip():
        return False, "Content must be a non-empty string"
    
    # Check agent_id
    if not isinstance(tile['agent_id'], str) or not tile['agent_id'].strip():
        return False, "Agent ID must be a non-empty string"
    
    # Check cycle
    if not isinstance(tile['cycle'], int) or tile['cycle'] <= 0:
        return False, "Cycle must be a positive integer"
    
    # Check phase
    if not isinstance(tile['phase'], int) or tile['phase'] < 1 or tile['phase'] > 4:
        return False, "Phase must be an integer between 1 and 4"
    
    # Check optional tags
    if 'tags' in tile:
        if not isinstance(tile['tags'], list):
            return False, "Tags must be a list if present"
        for tag in tile['tags']:
            if not isinstance(tag, str):
                return False, "All tags must be strings"
    
    return True, "OK"

