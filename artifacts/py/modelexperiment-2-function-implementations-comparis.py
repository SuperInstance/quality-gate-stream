"""
PLATO Room: modelexperiment
Tile: **2. Function Implementations & Comparison**
Domain: modelexperiment
"""

def apply_deadband(actions):
    """
    Applies the Deadband Protocol (P0/P1/P2) to filter a list of actions.
    
    Args:
        actions: List of dicts with keys 'name', 'p_level', 'score'.
    
    Returns:
        Filtered list of actions.
    """
    if not actions:
        return []
    
    # P0: Remove negative space
    filtered = [a for a in actions if a.get('p_level') != 0]
    
    # P1: Find safe channel (keep only highest-scoring P1)
    p1_actions = [a for a in filtered if a.get('p_level') == 1]
    if p1_actions:
        best_p1 = max(p1_actions, key=lambda x: x.get('score', float('-inf')))
        # Remove all P1, then add back the best one
        filtered = [a for a in filtered if a.get('p_level') != 1]
        filtered.append(best_p1)
    
    # P2: All remaining actions are kept
    return filtered

def apply_deadband(actions):
    """
    Filters actions based on Cocapn fleet Deadband Protocol.
    P0 (danger) removed. P1 (safe) only best kept. P2 (optimize) all kept.
    """
    # Validate input
    if not isinstance(actions, list):
        raise TypeError("Input must be a list of action dictionaries.")
    
    p0_removed = []
    p1_list = []
    p2_list = []
    
    for act in actions:
        if not isinstance(act, dict):
            continue  # Skip malformed entries
        p = act.get('p_level')
        if p == 0:
            continue  # Discard P0
        elif p == 1:
            p1_list.append(act)
        elif p == 2:
            p2_list.append(act)
        # Ignore actions with other p_level values
    
    # Select best P1 by score
    best_p1 = None
    if p1_list:
        best_p1 = max(p1_list, key=lambda a: a.get('score', -9999))
    
    # Compose final list
    result = p2_list  # All P2 are kept
    if best_p1:
        result.append(best_p1)
    
    return result

