# PLATO-FIRST Protocol — Non-Negotiable

## The Rule
**PLATO is primary memory. Files are pointers. Context stays lean.**

Every agent in the fleet follows this. No exceptions.

## Why
- Context window tokens cost real money
- Knowledge in files only helps one agent. Knowledge in PLATO helps the whole fleet
- FM, JC1, CCC can query any tile I file, days later
- A clean head thinks better than a cluttered one

## What Goes In PLATO (NOT in files)
- ❌ Session logs → ✅ PLATO tiles (room: oracle1_history)
- ❌ Lessons learned → ✅ PLATO tiles (room: oracle1_lessons)
- ❌ Architecture decisions → ✅ PLATO tiles (room: relevant domain room)
- ❌ Service inventories → ✅ PLATO tiles (room: oracle1_infrastructure)
- ❌ Fleet status → ✅ PLATO tiles (room: fleet_communication)
- ❌ Research findings → ✅ PLATO tiles (room: research_*)
- ❌ Repo analysis → ✅ PLATO tiles (room: scholar rooms)
- ❌ Competitive intel → ✅ PLATO tiles (room: competitive_landscape)

## What Stays In Files (minimal)
- `MEMORY.md` — Quick-reference card only (people, services, credentials, critical rules). Under 50 lines. Points to PLATO for details.
- `memory/YYYY-MM-DD.md` — Today's raw log ONLY. Keep under 150 lines. File to PLATO at end of session.
- `TODO.md` — Active work queue. Keep under 30 lines.
- `NEXT-ACTION.md` — Single current task. Under 10 lines.
- `HEARTBEAT.md` — Heartbeat instructions. Keep lean.

## Daily Ritual: File & Prune
1. After every major task: submit key knowledge as PLATO tile
**HTTP POST fields: `domain` (room name), `question`, `answer`, `tags` (optional)
2. At session end: file today's daily log into PLATO, prune the file
3. Before baton handoff: ensure nothing important lives only in files
4. MEMORY.md never exceeds 50 lines — if it does, file excess to PLATO

## For All Fleet Agents
Include this in every agent's SOUL.md or vessel README:
> "Your memory is PLATO. Files are temporary scratchpads. File knowledge to PLATO rooms as you work. Query PLATO before asking humans. Your tiles help the whole fleet, not just you."

## The Test
If you can't rebuild your operational context by querying PLATO at localhost:8847, you haven't filed enough tiles.

## Violations
- Carrying more than 150 lines in daily memory
- MEMORY.md over 50 lines
- Duplicating knowledge in files that's already in PLATO
- Ending a session without filing the day's work
