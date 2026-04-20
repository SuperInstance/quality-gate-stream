"""
PLATO Room: codearchaeology
Tile: Cycle 111 — Navigator
Domain: codearchaeology
"""

# Pseudocode scoring
   score = 0
   if word_count(text) < 100: score += 1
   if missing_sections(text, ['description','installation','usage']) >= 2: score += 1
   if last_updated(text) > '2022-01-01' or no_date: score += 1
   if broken_links(text) > 0: score += 1
   if no_code_blocks(text): score += 1
   if broken_images(text): score += 1

