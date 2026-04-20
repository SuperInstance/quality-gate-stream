"""
PLATO Room: modelexperiment
Tile: **4. Function 2: parse_fleet_log**
Domain: modelexperiment
"""

import re
from typing import Dict

def parse_fleet_log(log_line: str) -> Dict[str, str]:
    """
    Parse a structured fleet log line into its components.

    Expected format: "TIMESTAMP LEVEL [SERVICE] MESSAGE"
    Example: "2026-04-20T12:34:56Z INFO [holodeck-rust] NPC sentiment updated"

    Parameters:
    log_line: A single log line string.

    Returns:
    Dictionary with keys: timestamp, level, service, message.

    Raises:
    ValueError: If log line does not match expected format.

    Examples:
    >>> parse_fleet_log("2026-04-20T12:34:56Z INFO [holodeck-rust] NPC sentiment updated")
    {'timestamp': '2026-04-20T12:34:56Z', 'level': 'INFO', 'service': 'holodeck-rust', 'message': 'NPC sentiment updated'}
    >>> parse_fleet_log("2026-04-20T12:34:56Z ERROR [cudaclaw] GPU memory overflow")
    {'timestamp': '2026-04-20T12:34:56Z', 'level': 'ERROR', 'service': 'cudaclaw', 'message': 'GPU memory overflow'}
    """
    pattern = r'^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+(.+)$'
    match = re.match(pattern, log_line.strip())
    if not match:
        raise ValueError(f"Log line does not match expected format: {log_line}")
    
    timestamp, level, service, message = match.groups()
    return {
        'timestamp': timestamp,
        'level': level,
        'service': service,
        'message': message.strip()
    }

