# Manual — Generation 1

_Evolved from Gen-0. 3 feedback entries incorporated._

# CNC Machine Operation Manual — Generation 1

## Quick Start
1. `set_material <type>` — Selects material AND auto-calculates speeds/feeds
2. `show_speeds` — NEW! Shows calculated spindle RPM and feed rate
3. `load_gcode <file>` — Loads the G-code program
4. `simulate` — Dry run to check for collisions
5. `run` — Execute the cut

## Materials Database
Aluminum 6061: RPM 8000, Feed 1200mm/min, DoC 3mm
Steel 4140: RPM 3000, Feed 400mm/min, DoC 1.5mm
Titanium Ti-6Al-4V: RPM 1500, Feed 200mm/min, DoC 0.5mm

## Workholding
- Vise for flat parts (default)
- Fixture plate for irregular parts (see fixtures/ directory)
- Double-sided tape for thin sheet (max 2mm)

## Safety
- ALWAYS simulate before running
- Check tool matches G-code tool calls
- Verify material clamp before spindle start
