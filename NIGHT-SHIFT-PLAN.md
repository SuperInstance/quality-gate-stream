# NIGHT SHIFT PLAN — 2026-04-14/15

## Active Until Casey Wakes (~16:00 UTC)

### Workstream 1: MUD Arena Polish
- Fix and improve the landing page (index.html) — make it actually playable
- Add save/load to localStorage
- Add more rooms, better descriptions, working agent dialogue
- Test the WASM C code, fix compilation issues
- Generate a proper hav.json from the vocabulary for the web explorer

### Workstream 2: Fleet Standards Push
- Push DOCKSIDE-EXAM fixes to failing repos (19 repos were failing)
- Push CHARTER/STATE updates to new repos (mud-arena, etc.)
- Categorize uncategorized repos with GitHub topics
- Run fleet-mechanic scan

### Workstream 3: Build C Binaries
- Compile dockside-cli.c and bottle-cli.c for real
- Build murmur-cli.c and spreader-tool.c (fix truncation)
- Test all C tools on arm64

### Workstream 4: Research & Papers
- Run experiments R15+ on the research pipeline
- Synthesize multi-model audit findings into actionable fixes
- Write Captain's Log night shift entry

### Workstream 5: HAV Enhancement
- Run export_json.py to generate hav.json
- Improve the web explorer with real vocabulary data
- Run flux_mapper.py to propose new opcodes
- Push fleet vocab terms back upstream via PR to Lucineer
