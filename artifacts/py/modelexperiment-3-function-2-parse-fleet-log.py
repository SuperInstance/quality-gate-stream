"""
PLATO Room: modelexperiment
Tile: **3. Function 2: parse_fleet_log()**
Domain: modelexperiment
"""

import re
from typing import Dict, Any

def parse_fleet_log(log_text: str) -> Dict[str, Any]:
    """
    Parse a fleet log line into structured fields.
    
    Expected format:
    "YYYY‑MM‑DD HH:MM UTC | CYCLE N | AGENT Name | STATUS status | TILES N | CPU X% | MEM YGB"
    
    Missing fields become None.
    """
    # Default dict
    result = {
        "timestamp": None,
        "cycle": None,
        "agent": None,
        "status": None,
        "tiles": None,
        "cpu": None,
        "mem": None
    }
    
    if not log_text or '|' not in log_text:
        return result
    
    parts = [p.strip() for p in log_text.split('|')]
    
    for part in parts:
        if 'UTC' in part:
            result["timestamp"] = part.strip()
        elif part.startswith('CYCLE'):
            try:
                result["cycle"] = int(part.split()[1])
            except (IndexError, ValueError):
                pass
        elif part.startswith('AGENT'):
            result["agent"] = part.split(maxsplit=1)[1] if len(part.split()) > 1 else None
        elif part.startswith('STATUS'):
            result["status"] = part.split(maxsplit=1)[1].lower() if len(part.split()) > 1 else None
        elif part.startswith('TILES'):
            try:
                result["tiles"] = int(part.split()[1])
            except (IndexError, ValueError):
                pass
        elif part.startswith('CPU'):
            # extract number, remove '%'
            match = re.search(r'([0-9.]+)%', part)
            if match:
                try:
                    result["cpu"] = float(match.group(1))
                except ValueError:
                    pass
        elif part.startswith('MEM'):
            # extract number, assume GB
            match = re.search(r'([0-9.]+)GB', part)
            if match:
                try:
                    result["mem"] = float(match.group(1))
                except ValueError:
                    pass
    
    return result

