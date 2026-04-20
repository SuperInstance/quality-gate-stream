"""
PLATO Room: modelexperiment
Tile: **2. Function Generation**
Domain: modelexperiment
"""

def apply_deadband_protocol(sensor_readings, deadband_low, deadband_high, target):
    """
    Applies the Deadband Protocol (P0/P1/P2) to a list of sensor readings.
    
    Args:
        sensor_readings: List of float sensor values.
        deadband_low: Lower bound of the safe channel (P1).
        deadband_high: Upper bound of the safe channel (P1).
        target: The ideal value for P2 optimization.
    
    Returns:
        List of classification strings for each reading.
    """
    if not sensor_readings:
        return []
    
    classifications = []
    p1_readings = []  # Store indices and values of safe readings
    
    for i, reading in enumerate(sensor_readings):
        if reading < deadband_low:
            classifications.append("P0: Unsafe (below range)")
        elif reading > deadband_high:
            classifications.append("P0: Unsafe (above range)")
        else:
            classifications.append("P1: Safe channel")
            p1_readings.append((i, reading))
    
    # Find P2 optimal among P1 readings
    if p1_readings:
        # Find the reading in P1 closest to target
        optimal_idx, optimal_reading = min(p1_readings, key=lambda x: abs(x[1] - target))
        # Update its classification
        classifications[optimal_idx] = "P2: Optimal"
    
    return classifications

