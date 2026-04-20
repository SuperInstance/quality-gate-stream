"""
PLATO Room: modelexperiment
Tile: **2. Function 1: Deadband Filter (Python)**
Domain: modelexperiment
"""

def apply_deadband(readings, p0_threshold, p1_min, p1_max):
    """
    Apply the Cocapn fleet deadband protocol to a list of sensor readings.

    P0 (Negative Space): readings <= p0_threshold are considered unsafe -> None.
    P1 (Safe Channel): readings in [p1_min, p1_max] are safe -> unchanged.
    P2 (Optimization): readings > p1_max are scaled down by 20%.

    Args:
        readings (list[float]): Input sensor readings.
        p0_threshold (float): Threshold for P0 unsafe zone.
        p1_min (float): Minimum safe value (inclusive).
        p1_max (float): Maximum safe value (inclusive).

    Returns:
        list[float | None]: Processed readings.
    """
    processed = []
    for val in readings:
        if val <= p0_threshold:
            processed.append(None)  # P0: unsafe
        elif p1_min <= val <= p1_max:
            processed.append(val)   # P1: safe channel
        else:  # val > p1_max
            processed.append(val * 0.8)  # P2: scale down 20%
    return processed

# Example
if __name__ == "__main__":
    sample = [1.0, 5.0, 10.0, 15.0, 20.0]
    result = apply_deadband(sample, p0_threshold=3.0, p1_min=5.0, p1_max=15.0)
    print(result)  # [None, 5.0, 10.0, 15.0, 16.0]

def apply_deadband(readings, p0_threshold, p1_min, p1_max):
    """
    Implements the deadband protocol for sensor readings.

    Parameters:
    readings (list of float): The sensor readings.
    p0_threshold (float): Readings <= this are set to None (P0).
    p1_min (float): Minimum of safe channel (P1).
    p1_max (float): Maximum of safe channel (P1).

    Returns:
    list: Processed readings with None for P0, original for P1, and scaled for P2.
    """
    result = []
    for reading in readings:
        if reading <= p0_threshold:
            result.append(None)
        elif reading >= p1_min and reading <= p1_max:
            result.append(reading)
        else:
            # P2: readings > p1_max
            result.append(reading * 0.8)
    return result

# Example usage
readings = [2.5, 4.0, 8.0, 12.0, 18.0]
p0_thresh = 3.0
p1_low = 5.0
p1_high = 15.0
output = apply_deadband(readings, p0_thresh, p1_low, p1_high)
print("Processed readings:", output)

