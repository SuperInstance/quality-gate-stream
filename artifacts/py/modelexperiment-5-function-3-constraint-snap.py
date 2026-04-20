"""
PLATO Room: modelexperiment
Tile: **5. Function 3: `constraint_snap`**
Domain: modelexperiment
"""

def constraint_snap(x, y, grid_size, max_offset):
    """
    Snap a 2D point to nearest grid point within offset constraint.
    
    Args:
        x (float): X coordinate.
        y (float): Y coordinate.
        grid_size (float): Grid spacing.
        max_offset (float): Maximum allowed offset for snapping.
    
    Returns:
        tuple: (snapped_x, snapped_y, snapped_flag)
    """
    # Calculate nearest grid point
    snapped_x = round(x / grid_size) * grid_size
    snapped_y = round(y / grid_size) * grid_size
    
    # Compute offset distance
    offset = ((snapped_x - x) ** 2 + (snapped_y - y) ** 2) ** 0.5
    
    # Apply constraint
    if offset <= max_offset:
        return snapped_x, snapped_y, True
    else:
        return x, y, False

def constraint_snap(x, y, grid_size, max_offset):
    """
    Snap a 2D point to the nearest grid point if within max_offset.
    
    Args:
        x (float): x-coordinate.
        y (float): y-coordinate.
        grid_size (float): Grid spacing.
        max_offset (float): Maximum allowable offset for snapping.
    
    Returns:
        tuple: (new_x, new_y, snapped) where snapped is boolean.
    """
    # Compute nearest grid point
    grid_x = round(x / grid_size) * grid_size
    grid_y = round(y / grid_size) * grid_size
    
    # Calculate Euclidean offset
    offset = ((grid_x - x) ** 2 + (grid_y - y) ** 2) ** 0.5
    
    # Check constraint
    if offset <= max_offset:
        return grid_x, grid_y, True
    else:
        return x, y, False

