"""
PLATO Room: modelexperiment
Tile: **3. Groq Llama-70b Output**
Domain: modelexperiment
"""

def deadband_filter(data, lower, upper):
    """
    Deadband filter: values in [lower, upper] become zero, 
    others are shifted by nearest bound.
    """
    if lower > upper:
        lower, upper = upper, lower  # Auto-correct bounds
    
    result = []
    for val in data:
        if val >= lower and val <= upper:
            result.append(0.0)
        elif val < lower:
            result.append(val - lower)
        else:
            result.append(val - upper)
    return result

import re

def parse_fleet_log_line(line):
    # Pattern: date time [agent] message
    match = re.search(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) \[([^\]]+)\] (.+)', line)
    if match:
        date, time, agent, message = match.groups()
        return {
            'date': date,
            'time': time,
            'agent': agent,
            'message': message
        }
    else:
        return None

import numpy as np

def constraint_snap(point, line_start, line_end, tolerance):
    point = np.array(point)
    A = np.array(line_start)
    B = np.array(line_end)
    
    AB = B - A
    t = np.dot(point - A, AB) / np.dot(AB, AB)
    t = np.clip(t, 0, 1)
    nearest = A + t * AB
    
    if np.linalg.norm(nearest - point) <= tolerance:
        return tuple(nearest)
    else:
        return tuple(point)

