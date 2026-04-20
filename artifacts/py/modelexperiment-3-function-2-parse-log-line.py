"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `parse_log_line`**
Domain: modelexperiment
"""

import re
from typing import Dict, Any
from datetime import datetime

def parse_log_line(line: str) -> Dict[str, Any]:
    """
    Parse a structured fleet service log line into its constituent parts.

    Expected format:
        TIMESTAMP [SERVICE] [LEVEL] COMPONENT - MESSAGE key=value key2=value2

    Args:
        line: A log line string.

    Returns:
        A dictionary with keys: 'timestamp', 'service', 'level', 'component',
        'message', 'kv_pairs'. If the line doesn't match, returns an empty dict.
        'timestamp' is returned as a datetime object.
        'kv_pairs' is a dictionary of extracted key-value pairs (strings).
    """
    # Regex pattern matching the log format
    pattern = r'^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+([^\s\-]+)\s+\-\s+([^=]+)(?:\s+(.+))?$'
    match = re.match(pattern, line.strip())
    if not match:
        return {}

    timestamp_str, service, level, component, message, kv_string = match.groups()

    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        timestamp = timestamp_str  # fallback to string if parsing fails

    # Parse key-value pairs
    kv_pairs = {}
    if kv_string:
        # Split by spaces, then each part by '='
        for pair in kv_string.split():
            if '=' in pair:
                k, v = pair.split('=', 1)
                kv_pairs[k] = v

    return {
        'timestamp': timestamp,
        'service': service,
        'level': level,
        'component': component,
        'message': message.strip(),
        'kv_pairs': kv_pairs
    }

