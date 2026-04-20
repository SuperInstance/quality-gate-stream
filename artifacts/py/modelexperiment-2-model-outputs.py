"""
PLATO Room: modelexperiment
Tile: **2. Model Outputs**
Domain: modelexperiment
"""

import re
from datetime import datetime
from typing import Dict, Optional

def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a structured log line format: 'YYYY-MM-DD HH:MM:SS LEVEL [MODULE] Message'
    Returns a dictionary with keys: timestamp, level, module, message.
    Returns None if line doesn't match expected format.
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[([^\]]+)\] (.+)$'
    match = re.match(pattern, line)
    if not match:
        return None
    return {
        'timestamp': match.group(1),
        'level': match.group(2),
        'module': match.group(3),
        'message': match.group(4)
    }

if __name__ == "__main__":
    # Example 1: Valid log line
    log1 = "2026-04-20 01:30:45 INFO [plato-torch] Training tile accepted"
    print(parse_log_line(log1))
    
    # Example 2: Another valid line
    log2 = "2026-04-20 02:15:00 ERROR [cudaclaw] GPU memory overflow"
    print(parse_log_line(log2))
    
    # Example 3: Invalid line
    log3 = "Bad format"
    print(parse_log_line(log3))

import re
from typing import Dict, Optional

def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parses a log line with format: '2026-04-20 01:30:45 INFO [module] message'
    Extracts timestamp, level, module, and message.
    """
    # Regex pattern: date time LEVEL [module] message
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
    # Test cases
    test1 = "2026-04-20 01:30:45 INFO [plato-torch] Tile submitted"
    print(parse_log_line(test1))
    
    test2 = "2026-04-20 02:00:00 WARN [holodeck-rust] NPC sentiment low"
    print(parse_log_line(test2))
    
    test3 = "Invalid line"
    print(parse_log_line(test3))

