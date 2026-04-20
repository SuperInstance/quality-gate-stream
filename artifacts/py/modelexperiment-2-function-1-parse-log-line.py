"""
PLATO Room: modelexperiment
Tile: **2. Function 1: `parse_log_line`**
Domain: modelexperiment
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a structured log line into a dictionary.

    Format: [TIMESTAMP] LEVEL: message | key1=value1 key2=value2

    Args:
        line: A log line string.

    Returns:
        A dictionary with keys: 'timestamp', 'level', 'message', 'extras'.
        Returns None if the line is malformed.
    """
    # Main regex to capture timestamp, level, message, and optional extras
    pattern = r'^\[([^\]]+)\]\s+([A-Z]+):\s+(.+?)(?:\s+\|\s+(.+))?$'
    match = re.match(pattern, line.strip())
    if not match:
        return None

    timestamp_str, level, message, extras_str = match.groups()

    # Parse timestamp (try ISO format, fallback to string)
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        timestamp = timestamp_str  # Keep as string if parsing fails

    # Parse extras if present
    extras = {}
    if extras_str:
        # Split by spaces, then by '='
        for pair in extras_str.split():
            if '=' in pair:
                key, value = pair.split('=', 1)
                extras[key] = value

    return {
        'timestamp': timestamp,
        'level': level,
        'message': message,
        'extras': extras
    }

