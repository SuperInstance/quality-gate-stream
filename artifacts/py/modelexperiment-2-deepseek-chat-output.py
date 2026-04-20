"""
PLATO Room: modelexperiment
Tile: **2. DeepSeek-chat Output**
Domain: modelexperiment
"""

def deadband_filter(data: list[float], lower: float, upper: float) -> list[float]:
    """
    Apply a deadband filter to a list of values.
    
    Values within [lower, upper] (inclusive) are mapped to zero.
    Values outside the band are offset by the nearest bound.
    
    Args:
        data: List of input values
        lower: Lower bound of deadband
        upper: Upper bound of deadband
        
    Returns:
        List of filtered values
        
    Example:
        >>> deadband_filter([1.0, 2.5, 3.0, 4.5], 2.0, 4.0)
        [0.0, 0.5, 0.0, 0.5]  # 1.0 → 0.0 (below), 2.5 → 0.5 (above lower), etc.
    """
    if lower > upper:
        raise ValueError("lower must be <= upper")
    
    result = []
    for value in data:
        if lower <= value <= upper:
            result.append(0.0)
        elif value < lower:
            result.append(value - lower)
        else:  # value > upper
            result.append(value - upper)
    return result

import re
from datetime import datetime

def parse_fleet_log_line(line: str) -> dict:
    """
    Parse a structured fleet log line into components.
    
    Expected format: "YYYY-MM-DD HH:MM [Agent] Message"
    
    Args:
        line: Log line string
        
    Returns:
        Dictionary with keys: timestamp, agent, message
        
    Example:
        >>> parse_fleet_log_line("2026-04-19 22:12 [Alchemist] Cycle 74 - Tile accepted")
        {'timestamp': datetime(2026, 4, 19, 22, 12), 'agent': 'Alchemist', 
         'message': 'Cycle 74 - Tile accepted'}
    """
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \[([^\]]+)\] (.+)'
    match = re.match(pattern, line.strip())
    
    if not match:
        raise ValueError(f"Log line does not match expected format: {line}")
    
    timestamp_str, agent, message = match.groups()
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
    
    return {
        "timestamp": timestamp,
        "agent": agent.strip(),
        "message": message.strip()
    }

