"""
PLATO Room: modelexperiment
Tile: **2. Generated Code**
Domain: modelexperiment
"""

def deadband_filter(data, lower, upper):
    """
    Apply deadband filter to a sequence of values.
    
    Args:
        data: List of numeric values
        lower: Lower deadband threshold
        upper: Upper deadband threshold
        
    Returns:
        List of filtered values
    """
    if not data:
        return []
    
    filtered = [0.0]  # Initial output
    for i in range(1, len(data)):
        current = data[i]
        if lower <= current <= upper:
            # Within deadband, use previous output
            filtered.append(filtered[i-1])
        else:
            # Outside deadband, pass through
            filtered.append(current)
    
    return filtered

def parse_fleet_log_line(line):
    """
    Parse structured fleet log line.
    
    Format: [TIMESTAMP] SERVICE:LEVEL: message
    
    Args:
        line: String log line
        
    Returns:
        Dict with timestamp, service, level, message
    """
    import re
    
    pattern = r'^\[(.*?)\]\s+(\w+):(\w+):\s+(.+)$'
    match = re.match(pattern, line.strip())
    
    if not match:
        raise ValueError(f"Invalid log format: {line}")
    
    return {
        'timestamp': match.group(1),
        'service': match.group(2),
        'level': match.group(3).lower(),
        'message': match.group(4)
    }

def constraint_snap(point, line_start, line_end, tolerance):
    """
    Snap point to nearest point on line segment if within tolerance.
    
    Args:
        point: (x, y) tuple
        line_start: (x1, y1) tuple
        line_end: (x2, y2) tuple
        tolerance: Maximum distance for snapping
        
    Returns:
        (x, y) tuple - snapped point or original
    """
    import math
    
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Vector math for projection
    dx = x2 - x1
    dy = y2 - y1
    line_len_sq = dx*dx + dy*dy
    
    if line_len_sq == 0:
        # Line segment is a point
        dist = math.sqrt((px-x1)**2 + (py-y1)**2)
        return (x1, y1) if dist <= tolerance else point
    
    # Projection parameter
    t = ((px - x1) * dx + (py - y1) * dy) / line_len_sq
    t = max(0, min(1, t))  # Clamp to segment
    
    # Nearest point on segment
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    
    # Check distance
    dist = math.sqrt((px - nearest_x)**2 + (py - nearest_y)**2)
    
    return (nearest_x, nearest_y) if dist <= tolerance else point

