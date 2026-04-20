"""
PLATO Room: modelexperiment
Tile: **2. Model Outputs & Analysis**
Domain: modelexperiment
"""

def deadband_filter(decisions, p0_threshold, p1_min, p1_max):
    """
    Apply the Cocapn fleet Deadband Protocol to a list of decision scores.

    Parameters:
    decisions (list of float): Input decision scores.
    p0_threshold (float): P0 threshold. Values with abs(value) <= p0_threshold are set to 0.0.
    p1_min (float): Lower bound of the P1 safe channel.
    p1_max (float): Upper bound of the P1 safe channel.

    Returns:
    list of float: Filtered decisions after applying P0 and P1 rules.

    Example:
    >>> deadband_filter([-0.1, 0.05, 1.5, 2.5, -2.0], 0.1, 0.5, 2.0)
    [0.0, 0.0, 1.5, 2.0, -2.0]
    """
    filtered = []
    for d in decisions:
        # P0: Map negative space
        if abs(d) <= p0_threshold:
            filtered.append(0.0)
            continue
        # P1: Find safe channel
        if d < p1_min:
            filtered.append(p1_min)
        elif d > p1_max:
            filtered.append(p1_max)
        else:
            filtered.append(d)
    return filtered

def deadband_filter(decisions, p0_threshold, p1_min, p1_max):
    """
    Apply the Deadband Protocol (P0 and P1) to a list of decisions.

    Args:
        decisions: List of float decision values.
        p0_threshold: Threshold for P0 (negative space). Decisions with |value| <= p0_threshold become 0.
        p1_min: Minimum safe channel bound for P1.
        p1_max: Maximum safe channel bound for P1.

    Returns:
        List of filtered decisions.

    Example:
        >>> deadband_filter([-0.2, 0.05, 1.2, 3.0], 0.1, 0.5, 2.0)
        [-0.5, 0.0, 1.2, 2.0]
    """
    result = []
    for d in decisions:
        # P0: eliminate negative space
        if abs(d) <= p0_threshold:
            result.append(0.0)
            continue

        # P1: constrain to safe channel
        if d < p1_min:
            d = p1_min
        elif d > p1_max:
            d = p1_max
        result.append(d)
    return result

