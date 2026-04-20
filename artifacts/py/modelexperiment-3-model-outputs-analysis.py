"""
PLATO Room: modelexperiment
Tile: **3. Model Outputs & Analysis**
Domain: modelexperiment
"""

def deadband_filter(readings: list[float], deadband: float = 0.1) -> list[float]:
    """
    Apply the Cocapn Fleet Deadband Protocol to a time-series of sensor readings.
    P0 (Negative Space): Ignore/zero values that are within +/- `deadband` of zero (noise).
    P1 (Safe Channels): For values outside the deadband, pass them through.
    P2 (Optimize): Not applied in this simple filter.
    Returns a filtered list where values within [-deadband, +deadband] are set to 0.0.
    """
    if not isinstance(readings, list):
        raise TypeError("readings must be a list")
    if not isinstance(deadband, (int, float)) or deadband < 0:
        raise ValueError("deadband must be a non-negative number")

    filtered = []
    for value in readings:
        if not isinstance(value, (int, float)):
            # Could raise an error, but for robustness, skip or set to 0.
            filtered.append(0.0)
            continue
        if -deadband <= value <= deadband:
            filtered.append(0.0)
        else:
            filtered.append(float(value))
    return filtered

import re
from datetime import datetime

def parse_fleet_log(log_line: str) -> dict:
    """
    Parse a standardized fleet log line.
    Expected format: 'YYYY-MM-DD HH:MM:SS | AGENT | CYCLE | STATUS | MESSAGE'
    Example: '2026-04-20 01:41:00 | Alchemist | 152 | ACTIVE | Starting model comparison.'
    Returns a dictionary with keys: timestamp, agent, cycle, status, message.
    Returns None if the line cannot be parsed.
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| ([^|]+) \| (\d+) \| ([^|]+) \| (.+)$'
    match = re.match(pattern, log_line.strip())
    if not match:
        return None

    timestamp_str, agent, cycle_str, status, message = match.groups()
    try:
        # Validate timestamp format by parsing
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    try:
        cycle = int(cycle_str)
    except ValueError:
        return None

    return {
        "timestamp": timestamp_str,  # Keep as string for simplicity
        "agent": agent.strip(),
        "cycle": cycle,
        "status": status.strip(),
        "message": message.strip()
    }

