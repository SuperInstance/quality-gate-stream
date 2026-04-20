"""
PLATO Room: modelexperiment
Tile: **2. Function 1: deadband_filter()**
Domain: modelexperiment
"""

from typing import List

def deadband_filter(values: List[float], deadband: float = 0.1) -> List[float]:
    """
    Apply the fleet's Deadband Protocol to a list of float values.
    
    P0: Remove values within ±deadband of zero (negative space).
    P1: Keep values outside the deadband (safe channels).
    P2: Not implemented here – pure filtering only.
    
    Args:
        values: Input list of floats.
        deadband: Absolute threshold around zero (default 0.1).
    
    Returns:
        Filtered list preserving original order.
    """
    if not values:
        return []
    
    filtered = []
    for v in values:
        if abs(v) > deadband:          # P1: safe channel
            filtered.append(v)
        # P0: values inside deadband are dropped (negative space)
    return filtered

from typing import List

def deadband_filter(values: List[float], deadband: float = 0.1) -> List[float]:
    """
    Implements the Deadband Protocol filtering.
    
    P0: Identify negative space (values within deadband of zero).
    P1: Extract safe channels (values outside deadband).
    P2: No optimization applied in this version.
    
    Parameters:
        values (List[float]): The input signal values.
        deadband (float): The deadband width (default 0.1).
    
    Returns:
        List[float]: Values outside the deadband, in original order.
    """
    if deadband < 0:
        raise ValueError("deadband must be non‑negative")
    
    result = []
    for val in values:
        if abs(val) > deadband:
            result.append(val)
    return result

