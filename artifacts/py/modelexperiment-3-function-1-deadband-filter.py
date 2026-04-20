"""
PLATO Room: modelexperiment
Tile: **3. Function 1: deadband_filter**
Domain: modelexperiment
"""

from typing import List

def deadband_filter(values: List[float], lower: float, upper: float) -> List[float]:
    """
    Apply Deadband Protocol filtering: keep only values within [lower, upper] (P1 safe channel).

    Parameters:
    values: List of float sensor readings.
    lower: Lower bound of safe channel (inclusive).
    upper: Upper bound of safe channel (inclusive).

    Returns:
    Filtered list containing only values within the safe channel.

    Examples:
    >>> deadband_filter([1.0, 2.0, 3.0, 4.0], 2.0, 3.5)
    [2.0, 3.0]
    >>> deadband_filter([], 0.0, 1.0)
    []
    >>> deadband_filter([float('nan'), 2.0], 1.0, 3.0)
    [2.0]  # NaN is excluded as P0
    """
    if lower > upper:
        raise ValueError("Lower bound cannot be greater than upper bound")
    
    result = []
    for v in values:
        # Skip NaN values (treated as P0 negative space)
        if v != v:  # NaN check
            continue
        if lower <= v <= upper:
            result.append(v)
    return result

