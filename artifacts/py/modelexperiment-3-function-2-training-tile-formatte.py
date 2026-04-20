"""
PLATO Room: modelexperiment
Tile: **3. Function 2 – Training‑Tile Formatter**
Domain: modelexperiment
"""

def format_training_tile(agent_id: str, cycle: int, phase: int, raw_content: str, tags: list[str]) -> dict:
    """
    Format agent output as a training tile.
    Raises ValueError if tags are invalid.
    """
    valid_tags = {'P0', 'P1', 'P2', 'nav', 'sentinel', 'scribe', 'tinker', 
                  'scout', 'curator', 'mason', 'alchemist', 'herald', 
                  'scholar', 'weaver', 'archivist'}
    
    for tag in tags:
        if tag not in valid_tags:
            raise ValueError(f"Invalid tag: {tag}. Must be one of {sorted(valid_tags)}")
    
    from datetime import datetime, timezone
    return {
        "agent_id": agent_id,
        "cycle": cycle,
        "phase": phase,
        "content": raw_content,
        "tags": tags,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

