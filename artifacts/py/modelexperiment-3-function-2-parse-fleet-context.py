"""
PLATO Room: modelexperiment
Tile: **3. Function 2: `parse_fleet_context`**
Domain: modelexperiment
"""

from typing import Dict, List, Optional

def parse_fleet_context(markdown_text: str) -> Dict[str, Optional[str | List[str]]]:
    """
    Parse key structured data from a fleet context markdown file.

    Extracts:
        - fleet_name: Single string.
        - senior_agents: List of three agent names.
        - purposes: List of three purpose statements.

    Args:
        markdown_text: Full text of the markdown file.

    Returns:
        Dictionary with keys 'fleet_name', 'senior_agents', 'purposes'.
        Values are None if section is not found.
    """
    lines = markdown_text.split('\n')
    result = {
        'fleet_name': None,
        'senior_agents': None,
        'purposes': None
    }

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Find fleet name (line after "Who We Are")
        if line_stripped.lower().startswith('## who we are'):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    result['fleet_name'] = next_line
        # Find senior agents (bulleted list after "Three senior agents:")
        if 'senior agents' in line_stripped.lower():
            agents = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('-'):
                agent_name = lines[j].strip().lstrip('-').strip()
                agents.append(agent_name)
                j += 1
            if agents:
                result['senior_agents'] = agents
        # Find purposes (numbered list after "Your Purpose")
        if line_stripped.lower().startswith('## your purpose'):
            purposes = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                purpose = lines[j].strip().split('.', 1)[-1].strip()
                purposes.append(purpose)
                j += 1
            if purposes:
                # Take only first three as specified
                result['purposes'] = purposes[:3]

    return result

