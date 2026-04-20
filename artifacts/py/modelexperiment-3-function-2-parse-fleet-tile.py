"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `parse_fleet_tile`**
Domain: modelexperiment
"""

def parse_fleet_tile(tile_text):
    """
    Parse a fleet training tile string into a metadata dictionary.
    """
    result = {
        "cycle": None,
        "role": None,
        "phase": None,
        "task": None,
        "content": None
    }
    
    lines = tile_text.strip().split('\n')
    
    # Parse first line for cycle and role
    if lines and lines[0].startswith('# Cycle'):
        first_line = lines[0]
        # Expected format: "# Cycle 135 — Alchemist"
        parts = first_line.split('—')
        if len(parts) == 2:
            cycle_part = parts[0].replace('# Cycle', '').strip()
            result["cycle"] = int(cycle_part) if cycle_part.isdigit() else None
            result["role"] = parts[1].strip()
    
    # Parse subsequent lines for phase and task
    for i, line in enumerate(lines[1:], start=1):
        line_stripped = line.strip()
        if line_stripped.startswith('**Phase:**'):
            phase_part = line_stripped.replace('**Phase:**', '').strip()
            result["phase"] = int(phase_part) if phase_part.isdigit() else None
        elif line_stripped.startswith('**Task:**'):
            result["task"] = line_stripped.replace('**Task:**', '').strip()
        elif line_stripped == '---':
            # Content is everything after this line
            result["content"] = '\n'.join(lines[i+1:]).strip()
            break
    
    return result

