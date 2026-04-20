"""
PLATO Room: modelexperiment
Tile: **2. Function Implementations**
Domain: modelexperiment
"""

import numpy as np

def deadband_filter(values, deadband=(0.0, 1.0), outlier_sigma=3.0):
    if not values:
        return []
    
    # P0: Remove outliers
    arr = np.array(values)
    mean, std = np.mean(arr), np.std(arr)
    mask = (arr >= mean - outlier_sigma * std) & (arr <= mean + outlier_sigma * std)
    filtered = arr[mask].tolist()
    
    # P1: Clamp to deadband
    clamped = [max(deadband[0], min(deadband[1], v)) for v in filtered]
    
    # P2: Moving average (window=3)
    smoothed = []
    for i in range(len(clamped)):
        window = clamped[max(0, i-1):i+2]
        smoothed.append(sum(window) / len(window))
    
    return smoothed

def deadband_filter(values, deadband=(0.0, 1.0), outlier_sigma=3.0):
    import statistics
    
    if len(values) == 0:
        return []
    
    # P0: Remove outliers
    mean_val = statistics.mean(values)
    try:
        std_val = statistics.stdev(values)
    except statistics.StatisticsError:
        std_val = 0.0
    
    filtered = []
    for v in values:
        if abs(v - mean_val) <= outlier_sigma * std_val:
            filtered.append(v)
    
    # P1: Clamp to deadband
    clamped = []
    for v in filtered:
        if v < deadband[0]:
            clamped.append(deadband[0])
        elif v > deadband[1]:
            clamped.append(deadband[1])
        else:
            clamped.append(v)
    
    # P2: Moving average
    smoothed = []
    for i in range(len(clamped)):
        start = max(0, i - 1)
        end = min(len(clamped), i + 2)
        window = clamped[start:end]
        avg = sum(window) / len(window)
        smoothed.append(avg)
    
    return smoothed

