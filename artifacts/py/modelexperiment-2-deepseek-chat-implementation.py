"""
PLATO Room: modelexperiment
Tile: **2. DeepSeek-chat Implementation**
Domain: modelexperiment
"""

from typing import List

def deadband_filter(values: List[float], deadband: float) -> List[float]:
    """
    Apply a deadband filter to a list of values.
    
    Args:
        values: List of float values to filter.
        deadband: Positive float. Values within [-deadband, deadband] map to 0.
    
    Returns:
        Filtered list where values within deadband become 0.0.
    """
    if deadband < 0:
        raise ValueError("deadband must be non-negative")
    
    result = []
    for v in values:
        if -deadband <= v <= deadband:
            result.append(0.0)
        else:
            result.append(v)
    return result

from datetime import datetime
from typing import Dict, Optional

def parse_fleet_log_line(line: str) -> Dict[str, Optional]:
    """
    Parse a structured fleet log line into a dictionary.
    
    Expected format: "[timestamp] KEY1=value1 KEY2=value2 ..."
    
    Args:
        line: Log line string.
    
    Returns:
        Dictionary with parsed fields. Missing fields become None.
    """
    # Extract timestamp
    timestamp_str = line[1:20]  # assumes fixed format
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = None
    
    # Parse key=value pairs
    parts = line[22:].strip().split()
    data = {"timestamp": timestamp, "agent": None, "cycle": None, "status": None, "tiles": None}
    
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.lower()
            if key in data:
                if key == "cycle" or key == "tiles":
                    try:
                        data[key] = int(value)
                    except ValueError:
                        data[key] = None
                else:
                    data[key] = value
    return data

