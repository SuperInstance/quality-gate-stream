"""
PLATO Room: modelexperiment
Tile: **2. DeepSeek-chat Outputs**
Domain: modelexperiment
"""

def deadband_filter(values: list[float], epsilon: float) -> list[float]:
    """
    Apply deadband filtering to a list of float values.
    
    Args:
        values: List of float values to filter.
        epsilon: Deadband threshold. Values with absolute value < epsilon are set to zero.
    
    Returns:
        Filtered list where |x| < epsilon becomes 0.0, others unchanged.
    
    Example:
        >>> deadband_filter([-0.5, 0.02, 1.2], 0.1)
        [-0.5, 0.0, 1.2]
    """
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")
    
    result = []
    for v in values:
        if abs(v) < epsilon:
            result.append(0.0)
        else:
            result.append(v)
    return result

import re
from datetime import datetime

def parse_fleet_log(log_line: str) -> dict:
    """
    Parse a fleet service log line.
    
    Expected format: "YYYY-MM-DD HH:MM:SS [SERVICE] LEVEL: message"
    
    Args:
        log_line: A single log line as string.
    
    Returns:
        Dictionary with keys: timestamp, service, level, message.
        If line doesn't match pattern, returns None.
    
    Example:
        >>> parse_fleet_log("2026-04-19 22:30:00 [holodeck-rust] INFO: NPC spawned")
        {'timestamp': datetime.datetime(2026, 4, 19, 22, 30), 
         'service': 'holodeck-rust', 
         'level': 'INFO', 
         'message': 'NPC spawned'}
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] (\w+): (.+)$'
    match = re.match(pattern, log_line)
    
    if not match:
        return None
    
    timestamp_str, service, level, message = match.groups()
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = timestamp_str  # fallback to string if parsing fails
    
    return {
        "timestamp": timestamp,
        "service": service.strip(),
        "level": level.strip(),
        "message": message.strip()
    }

