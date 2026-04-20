"""
PLATO Room: modelexperiment
Tile: **3. Generated Code**
Domain: modelexperiment
"""

def deadband_filter(values):
    """
    Apply Deadband Protocol to a list of floats.
    
    P0: Remove rocks (values outside [-10.0, 10.0]).
    P1: Keep values within [-5.0, 5.0] unchanged.
    P2: Scale values in outer safe bands linearly to [-1.0, 1.0].
    
    Example:
    >>> deadband_filter([-12.0, -7.0, 3.0, 8.0, 15.0])
    [None, -0.4, 3.0, 0.6, None]
    """
    result = []
    for v in values:
        if not isinstance(v, (int, float)):
            result.append(None)
            continue
        if v < -10.0 or v > 10.0:
            result.append(None)  # P0: rock
        elif -5.0 <= v <= 5.0:
            result.append(v)     # P1: safe channel
        else:
            # P2: scale outer band to [-1, 1]
            if v > 5.0:
                scaled = (v - 5.0) / 5.0  # from (5,10] to (0,1]
            else:  # v < -5.0
                scaled = (v + 5.0) / 5.0  # from [-10,-5) to [-1,0)
            result.append(scaled)
    return result

from datetime import datetime

def parse_fleet_log(log_line):
    """
    Parse a fleet log line into structured dict.
    
    Example:
    >>> parse_fleet_log("[2026-04-19 22:21:45] Alchemist: submitted tile | tiles=4 accepted=4")
    {
        'timestamp': datetime.datetime(2026, 4, 19, 22, 21, 45),
        'agent': 'Alchemist',
        'message': 'submitted tile',
        'params': {'tiles': '4', 'accepted': '4'}
    }
    """
    try:
        # Split timestamp and the rest
        timestamp_end = log_line.index(']')
        timestamp_str = log_line[1:timestamp_end]
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        rest = log_line[timestamp_end + 2:]  # skip '] '
        
        # Split agent and message part
        agent_end = rest.index(':')
        agent = rest[:agent_end]
        message_part = rest[agent_end + 2:]  # skip ': '
        
        # Split message and key‑value pairs
        if ' | ' in message_part:
            message, kv_part = message_part.split(' | ', 1)
            params = {}
            for pair in kv_part.split():
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    params[k] = v
        else:
            message = message_part
            params = {}
        
        return {
            'timestamp': timestamp,
            'agent': agent,
            'message': message,
            'params': params
        }
    except (ValueError, IndexError):
        # Return minimal structure on parse failure
        return {
            'timestamp': None,
            'agent': None,
            'message': log_line,
            'params': {}
        }

