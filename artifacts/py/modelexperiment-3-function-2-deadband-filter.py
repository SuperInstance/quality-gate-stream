"""
PLATO Room: modelexperiment
Tile: **3. Function 2: deadband_filter**
Domain: modelexperiment
"""

from typing import List

def deadband_filter(readings: List[float], deadband: float) -> List[float]:
    """
    Apply Deadband Protocol filtering to sensor readings.
    
    P0: Remove readings outside valid range [-100.0, 100.0] (overflow risk).
    P1: Keep only readings where absolute value > deadband (safe channels).
    P2: Return filtered list (optimization happens elsewhere).
    
    Args:
        readings: List of sensor readings.
        deadband: Minimum absolute value for P1 filtering.
    
    Returns:
        Filtered list of readings.
    """
    # P0: Map negative space - remove invalid readings
    valid_readings = []
    for value in readings:
        if -100.0 <= value <= 100.0:
            valid_readings.append(value)
    
    # P1: Find safe channels - only values outside deadband
    safe_readings = []
    for value in valid_readings:
        if abs(value) > deadband:
            safe_readings.append(value)
    
    # P2: Return filtered list (optimization within channels)
    return safe_readings

from typing import List

def deadband_filter(readings: List[float], deadband: float) -> List[float]:
    """
    Implements the Deadband Protocol (P0, P1, P2) for sensor data.
    
    P0 (Negative Space): Discard readings outside [-100, 100] to prevent overflow.
    P1 (Safe Channels): Keep only readings with |value| > deadband.
    P2 (Optimization): Return the filtered list.
    
    Args:
        readings: Input sensor readings.
        deadband: Deadband threshold (positive).
    
    Returns:
        Filtered readings that pass P0 and P1.
    """
    if deadband < 0:
        raise ValueError("Deadband must be non-negative")
    
    # P0: Eliminate overflow/underflow risks
    p0_filtered = [v for v in readings if -100.0 <= v <= 100.0]
    
    # P1: Select safe channels (outside deadband)
    p1_filtered = [v for v in p0_filtered if abs(v) > deadband]
    
    # P2: Return result
    return p1_filtered

