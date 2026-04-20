"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `constraint_snap`**
Domain: modelexperiment
"""

def constraint_snap(point, line_pt1, line_pt2, tolerance):
    """
    Snap point to line if within tolerance.
    
    Args:
        point: Tuple (x, y)
        line_pt1: Tuple (x1, y1)
        line_pt2: Tuple (x2, y2)
        tolerance: float
    
    Returns:
        Tuple (x, y) snapped or original
    """
    px, py = point
    x1, y1 = line_pt1
    x2, y2 = line_pt2
    
    # Vector from line_pt1 to line_pt2
    dx = x2 - x1
    dy = y2 - y1
    
    # Vector from line_pt1 to point
    vx = px - x1
    vy = py - y1
    
    # Dot product and squared length
    dot = vx * dx + vy * dy
    len_sq = dx * dx + dy * dy
    
    # Projection parameter (t)
    if len_sq == 0:
        return point  # line points are identical
    
    t = dot / len_sq
    
    # Clamp to line segment
    t = max(0, min(1, t))
    
    # Projection point
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    
    # Distance check
    dist = ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
    if dist <= tolerance:
        return (proj_x, proj_y)
    return point

def constraint_snap(point, line_pt1, line_pt2, tolerance):
    """
    Snap a point to a line segment if within tolerance.
    
    Args:
        point (tuple): (x, y) coordinates of point.
        line_pt1 (tuple): (x1, y1) first point of line segment.
        line_pt2 (tuple): (x2, y2) second point of line segment.
        tolerance (float): Maximum distance for snapping.
    
    Returns:
        tuple: Snapped point if within tolerance, else original point.
    """
    x, y = point
    x1, y1 = line_pt1
    x2, y2 = line_pt2
    
    # Line vector
    dx = x2 - x1
    dy = y2 - y1
    
    # Vector from line_pt1 to point
    vx = x - x1
    vy = y - y1
    
    # Length squared of line segment
    len_sq = dx * dx + dy * dy
    
    # If line segment is a point, return original if within tolerance
    if len_sq == 0:
        dist = ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        return (x1, y1) if dist <= tolerance else point
    
    # Projection parameter
    t = (vx * dx + vy * dy) / len_sq
    
    # Clamp to segment
    t = max(0, min(1, t))
    
    # Closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    # Distance to closest point
    dist = ((x - closest_x) ** 2 + (y - closest_y) ** 2) ** 0.5
    
    return (closest_x, closest_y) if dist <= tolerance else point

