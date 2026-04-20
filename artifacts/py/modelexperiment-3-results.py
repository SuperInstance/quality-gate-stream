"""
PLATO Room: modelexperiment
Tile: **3. Results**
Domain: modelexperiment
"""

import re
from datetime import datetime
from typing import Optional, Dict

def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a structured log line into a dictionary.
    
    Expected format: "YYYY-MM-DD HH:MM:SS LEVEL [MODULE] MESSAGE"
    
    Args:
        line: A log line string.
    
    Returns:
        Dictionary with keys: timestamp, level, module, message.
        Returns None if line does not match expected format.
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[([^\]]+)\] (.+)$'
    match = re.match(pattern, line.strip())
    if not match:
        return None
    return {
        'timestamp': match.group(1),
        'level': match.group(2),
        'module': match.group(3),
        'message': match.group(4)
    }

if __name__ == "__main__":
    test_line = "2026-04-19 22:00:00 INFO [network] Connection established"
    result = parse_log_line(test_line)
    print(result)
    # Output: {'timestamp': '2026-04-19 22:00:00', 'level': 'INFO', 'module': 'network', 'message': 'Connection established'}

import re
from typing import Dict, Optional

def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parses a log line with format: "YYYY-MM-DD HH:MM:SS LEVEL [MODULE] MESSAGE"
    Returns a dictionary with keys: timestamp, level, module, message.
    Returns None if the line doesn't match.
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[([^\]]+)\] (.+)$'
    match = re.match(pattern, line.strip())
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2),
            "module": match.group(3),
            "message": match.group(4)
        }
    return None

if __name__ == "__main__":
    # Example usage
    log_line = "2026-04-19 22:00:00 INFO [module] message"
    parsed = parse_log_line(log_line)
    print(parsed)

