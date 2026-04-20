"""
PLATO Room: modelexperiment
Tile: **3. Groq Llama-70b Implementation**
Domain: modelexperiment
"""

def deadband_filter(values, deadband):
    """
    Deadband filter: values within +/- deadband of zero become zero.
    """
    result = []
    for v in values:
        if abs(v) <= deadband:
            result.append(0.0)
        else:
            result.append(v)
    return result

import re
from datetime import datetime

def parse_fleet_log_line(line):
    # Regex to match the log format
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] AGENT=(\w+) CYCLE=(\d+) STATUS=(\w+) TILES=(\d+)'
    match = re.match(pattern, line)
    
    if match:
        timestamp_str, agent, cycle, status, tiles = match.groups()
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return {
            "timestamp": timestamp,
            "agent": agent,
            "cycle": int(cycle),
            "status": status,
            "tiles": int(tiles)
        }
    else:
        # Try to parse partially
        data = {"timestamp": None, "agent": None, "cycle": None, "status": None, "tiles": None}
        # Simple extraction for other formats
        parts = line.split()
        for part in parts:
            if '=' in part:
                key, val = part.split('=', 1)
                if key == "AGENT":
                    data["agent"] = val
                elif key == "CYCLE":
                    try:
                        data["cycle"] = int(val)
                    except:
                        pass
                elif key == "STATUS":
                    data["status"] = val
                elif key == "TILES":
                    try:
                        data["tiles"] = int(val)
                    except:
                        pass
        return data

