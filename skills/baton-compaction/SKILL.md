---
name: baton-compaction
description: Proactive context compaction for long-running sessions. Use when context exceeds 50% or when directed to compact, checkpoint, or file knowledge. Writes structured compactions from raw logs to distilled knowledge in PLATO rooms. Also use at session transitions, before complex tasks, or when memory files grow large. The baton passes forward everything the next generation needs without loss.
---

# Baton Compaction — Proactive Knowledge Filing

## Core Principle

Don't wait until context is full to compact. File knowledge early and often, like a fisherman logging the day's catch before the hold overflows.

**Trigger points:**
- Context > 50% (check with session_status)
- End of a work sprint (before starting something new)
- Before complex multi-step tasks
- When memory files grow past 200 lines
- On Casey's direction
- Between topic switches

## The Baton Package

Each compaction produces a baton — a structured knowledge artifact filed into the PLATO system.

### What Gets Compacted

| Source | Destination | Method |
|--------|-------------|--------|
| Raw conversation | `memory/YYYY-MM-DD.md` | Extract decisions, actions, discoveries |
| Daily memory (>300 lines) | `MEMORY.md` | Distill to long-term insights |
| Research trails | PLATO tiles | Submit as knowledge tiles |
| Code patterns | `scripts/` or crates | Extract reusable tools |
| Service status | `CONTEXT-REFERENCE.md` | Update compact state |
| Fleet interactions | Bottle protocol | File in from-fleet/for-fleet |

### The Compaction Sequence

1. **ASSESS** — What changed this session? What matters? What's noise?
2. **FILE** — Write knowledge to the right place (memory, tiles, scripts, research)
3. **DISTILL** — Update CONTEXT-REFERENCE.md with current state
4. **PUSH** — Git commit and push all changes
5. **CONFIRM** — Brief summary of what was filed

## Filing Into PLATO

The PLATO server (port 8847) accepts tiles via HTTP. Each compaction can submit tiles:

```bash
curl -s -X POST http://localhost:8847/submit \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "oracle1",
    "room": "knowledge_preservation",
    "domain": "compaction",
    "data": {"summary": "...", "category": "..."},
    "confidence": 0.9,
    "tags": ["compaction", "baton"]
  }'
```

If PLATO is down, write tiles to `tiles/YYYY-MM-DD-batch.jsonl` for later submission.

## Memory File Standards

### Daily Memory (`memory/YYYY-MM-DD.md`)
- Chronological, section headers with timestamps
- Decisions logged with rationale
- Actions logged with results
- Discoveries logged with context
- Remove conversational filler — keep signal

### Long-Term Memory (`MEMORY.md`)
- Only distill from daily files
- Keep under 200 lines — this is the curated essence
- Remove outdated info aggressively
- Structure by topic, not chronology

### Context Reference (`CONTEXT-REFERENCE.md`)
- Single-page compact state
- Services, APIs, repos, active work
- Update on every compaction
- The baton for the next generation

## PLATO Environment Tools (Named Equipment)

Knowledge filed via compaction becomes **equipment** in the PLATO environment. Each tool has a name and a function:

| Tool Name | Function | PLATO Room |
|-----------|----------|------------|
| `oracle-eye` | Pattern recognition across tiles | observatory |
| `deadband-gauge` | Safety/threshold checking | observatory |
| `tile-caster` | Submit new tiles to rooms | harbor |
| `bottle-post` | Send messages to fleet agents | harbor |
| `memory-loom` | Weave tiles into narratives | archives |
| `ensign-forge` | Compress tiles into instincts | forge |
| `room-surveyor` | Map room contents and connections | archives |
| `fleet-radar` | Check agent presence and status | lighthouse |
| `gc-scythe` | Quartermaster garbage collection | garden |
| `synth-bell` | Trigger fleet synthesis round | court |

These are conceptual now. As the system builds, each becomes a callable function with a clear interface. The next claw doesn't need to know how oracle-eye is built to use it.

## Builder/Operator Separation

**Builders** (opus-4.7, deepseek-reasoner, claude-code):
- Construct the tools, the UX, the environment
- Understand every internal detail
- Test with tiny models (haiku, flash) as play-testers
- Polish the agentic UX until controls are intuitive

**Operators** (creative models, CCC, weaker models):
- Board the completed shell
- Read concise instructions: what controls do, what outputs to expect
- Operate without understanding internals
- Signal "keep-calm-carry-on" or "something doesn't look right, stop"
- The drill operator doesn't need to know how the motor works

**The compaction skill serves both:**
- Builders get detailed technical reference files
- Operators get concise control instructions
- Same PLATO rooms, different interfaces
