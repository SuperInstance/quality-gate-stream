"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `find_safe_channels`**
Domain: modelexperiment
"""

from typing import List, Tuple, Set

def find_safe_channels(negative_space: List[Tuple[int, int]], 
                       search_bounds: Tuple[int, int, int, int]) -> List[int]:
    """
    Find safe vertical channels (x-coordinates) within bounds that avoid negative space.

    P1 of Deadband Protocol: Find safe channels (where you CAN be).

    Args:
        negative_space: List of (x, y) coordinates to avoid.
        search_bounds: (x_min, x_max, y_min, y_max) defining rectangular search area.

    Returns:
        List of x-coordinates representing safe vertical channels.

    Example:
        >>> find_safe_channels([(1, 5), (2, 3)], (0, 5, 0, 10))
        [0, 3, 4, 5]  # x=1 and x=2 are blocked
    """
    x_min, x_max, y_min, y_max = search_bounds
    
    # Convert negative space to a set for O(1) lookups
    blocked_set = set(negative_space)
    
    # Determine which x-values have any blocked point within the vertical range
    blocked_x = set()
    for x, y in blocked_set:
        if x_min <= x <= x_max and y_min <= y <= y_max:
            blocked_x.add(x)
    
    # Safe channels are all x in range that are not blocked
    safe_channels = [x for x in range(x_min, x_max + 1) if x not in blocked_x]
    return safe_channels

