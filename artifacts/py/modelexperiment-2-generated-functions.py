"""
PLATO Room: modelexperiment
Tile: **2. Generated Functions**
Domain: modelexperiment
"""

from datetime import datetime
import re
from typing import Dict, Optional

def parse_log_line(log_line: str) -> Optional[Dict[str, str]]:
    """
    Parse a structured log line in format:
    'YYYY-MM-DD HH:MM:SS [LEVEL] component: message'

    Returns dict with keys: timestamp, level, component, message.
    Returns None if line doesn't match expected format.
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\w+): (.+)$'
    match = re.match(pattern, log_line.strip())
    if not match:
        return None
    return {
        'timestamp': match.group(1),
        'level': match.group(2),
        'component': match.group(3),
        'message': match.group(4)
    }

import re
from typing import Dict, Optional

def parse_log_line(log_line: str) -> Optional[Dict[str, str]]:
    """
    Parses a log line with format: "timestamp [level] component: message"
    Example: "2023-10-05 14:30:00 [ERROR] auth_service: Invalid credentials"
    """
    # Regex to capture timestamp, level, component, and message
    log_pattern = re.compile(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\w+): (.+)$'
    )
    match = log_pattern.match(log_line.strip())
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2),
            "component": match.group(3),
            "message": match.group(4)
        }
    return None

from typing import Any, Dict, List, Union

def validate_json_schema(
    data: Dict[str, Any], 
    schema: Dict[str, str]
) -> List[str]:
    """
    Validate JSON-like dict against a simple type schema.
    
    Schema format: {'field': 'type'} where type is 'str', 'int', 'float', 'bool', 'list'.
    Returns list of error messages. Empty list means valid.
    """
    errors = []
    for field, expected_type in schema.items():
        if field not in data:
            errors.append(f"Missing field: {field}")
            continue
        
        value = data[field]
        type_ok = False
        if expected_type == 'str':
            type_ok = isinstance(value, str)
        elif expected_type == 'int':
            type_ok = isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == 'float':
            type_ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == 'bool':
            type_ok = isinstance(value, bool)
        elif expected_type == 'list':
            type_ok = isinstance(value, list)
        else:
            errors.append(f"Unknown schema type for {field}: {expected_type}")
            continue
        
        if not type_ok:
            errors.append(f"Field '{field}' expected {expected_type}, got {type(value).__name__}")
    
    return errors

