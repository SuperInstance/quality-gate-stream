"""
PLATO Room: modelexperiment
Tile: **4. Groq Llama-70b Implementation**
Domain: modelexperiment
"""

# Function 1: deadband_filter
def deadband_filter(values, deadband=0.1):
    """
    Apply deadband filtering to a list of float values.
    """
    filtered = []
    for v in values:
        if abs(v) <= deadband:
            filtered.append(0.0)
        else:
            filtered.append(v)
    return filtered

# Function 2: parse_fleet_log
import re

def parse_fleet_log(log_text):
    """
    Parse a fleet log string into structured events.
    """
    events = []
    # Regex pattern for: [timestamp] agent: message
    pattern = r'\[([^\]]+)\]\s*(\w+):\s*(.+)'
    
    lines = log_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            timestamp, agent, message = match.groups()
            events.append({
                'timestamp': timestamp,
                'agent': agent,
                'message': message
            })
    return events

# Function 3: validate_tile
import uuid
from datetime import datetime

def validate_tile(tile):
    """
    Validate a training tile against fleet schema.
    """
    errors = []
    
    # Check required fields
    required = ['id', 'agent', 'cycle', 'content', 'timestamp']
    for field in required:
        if field not in tile:
            errors.append(f'Missing field: {field}')
    
    if 'id' in tile:
        try:
            uuid.UUID(tile['id'])
        except:
            errors.append('Invalid UUID for id')
    
    if 'agent' in tile:
        valid_agents = ['Alchemist', 'Navigator', 'Sentinel', 'Scribe', 
                       'Tinker', 'Scout', 'Curator', 'Mason', 'Herald', 
                       'Scholar', 'Weaver', 'Archivist']
        if tile['agent'] not in valid_agents:
            errors.append(f'Invalid agent: {tile["agent"]}')
    
    if 'cycle' in tile:
        if not isinstance(tile['cycle'], int) or tile['cycle'] < 1:
            errors.append('Cycle must be positive integer')
    
    if 'content' in tile:
        if not isinstance(tile['content'], str) or len(tile['content'].strip()) == 0:
            errors.append('Content must be non-empty string')
    
    if 'timestamp' in tile:
        try:
            # Try parsing ISO format
            datetime.fromisoformat(tile['timestamp'].replace('Z', '+00:00'))
        except:
            errors.append('Invalid ISO 8601 timestamp')
    
    valid = len(errors) == 0
    return valid, errors

