"""
PLATO Room: modelexperiment
Tile: **3. Model Outputs**
Domain: modelexperiment
"""

def deadband_filter(values, deadband=0.1):
    if not values:
        return []
    filtered = [values[0]]
    for v in values[1:]:
        if abs(v - filtered[-1]) < deadband:
            filtered.append(filtered[-1])
        else:
            filtered.append(v)
    return filtered

def parse_fleet_log(log_line):
    import re
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (\d+) \| (\w+) \| (.+)'
    match = re.match(pattern, log_line.strip())
    if not match:
        return None
    timestamp, agent, cycle, action, details = match.groups()
    return {
        'timestamp': timestamp,
        'agent': agent,
        'cycle': int(cycle),
        'action': action,
        'details': details.strip()
    }

def constraint_snap(point, constraints):
    x, y = point
    for x_min, x_max, y_min, y_max in constraints:
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return (x, y)
        # snap x
        if x < x_min:
            x_snap = x_min
        elif x > x_max:
            x_snap = x_max
        else:
            x_snap = x
        # snap y
        if y < y_min:
            y_snap = y_min
        elif y > y_max:
            y_snap = y_max
        else:
            y_snap = y
        return (x_snap, y_snap)
    return (x, y)

def deadband_filter(values, deadband=0.1):
    if len(values) == 0:
        return []
    result = [values[0]]
    for i in range(1, len(values)):
        if abs(values[i] - result[-1]) < deadband:
            result.append(result[-1])
        else:
            result.append(values[i])
    return result

def parse_fleet_log(log_line):
    parts = log_line.split('|')
    if len(parts) != 5:
        return None
    timestamp = parts[0].strip()
    agent = parts[1].strip()
    cycle = int(parts[2].strip())
    action = parts[3].strip()
    details = parts[4].strip()
    return {
        'timestamp': timestamp,
        'agent': agent,
        'cycle': cycle,
        'action': action,
        'details': details
    }

def constraint_snap(point, constraints):
    x, y = point
    for constraint in constraints:
        x_min, x_max, y_min, y_max = constraint
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return (x, y)
        # snap to nearest boundary
        if x < x_min:
            x = x_min
        elif x > x_max:
            x = x_max
        if y < y_min:
            y = y_min
        elif y > y_max:
            y = y_max
        return (x, y)
    return (x, y)

