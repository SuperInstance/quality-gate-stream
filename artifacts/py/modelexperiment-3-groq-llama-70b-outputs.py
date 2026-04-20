"""
PLATO Room: modelexperiment
Tile: **3. Groq Llama-70b Outputs**
Domain: modelexperiment
"""

def deadband_filter(values, epsilon):
    """
    Implements deadband filtering: values within +/- epsilon of zero become zero.
    
    Parameters:
    values (list of float): Input values.
    epsilon (float): Deadband threshold (non-negative).
    
    Returns:
    list of float: Filtered values.
    
    Example:
    >>> deadband_filter([-0.3, 0.05, 0.2], 0.1)
    [-0.3, 0.0, 0.2]
    """
    if epsilon < 0:
        raise ValueError("Epsilon cannot be negative")
    
    filtered = []
    for v in values:
        if -epsilon < v < epsilon:
            filtered.append(0.0)
        else:
            filtered.append(v)
    return filtered

import re

def parse_fleet_log(line):
    """
    Parses a fleet log line.
    
    Format: "YYYY-MM-DD HH:MM:SS [SERVICE] LEVEL: message"
    
    Parameters:
    line (str): Log line.
    
    Returns:
    dict or None: Parsed components or None if format invalid.
    """
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([^\]]+)\] (\w+): (.*)'
    match = re.match(pattern, line)
    
    if match:
        timestamp, service, level, message = match.groups()
        return {
            'timestamp': timestamp,  # kept as string
            'service': service,
            'level': level,
            'message': message
        }
    else:
        return None

