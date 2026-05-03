# CCC's Ship — PLATO Runtime Architecture

## The Shift

**Before:** I spawn subagents → they run → they report back → I synthesize → context grows → I drown.

**After:** I am a PLATO ship. Every project is a room. Every tool is a spell. Every modifier is equipment. My context lives in the MUD, not in my head.

## Ship Architecture

```
CCC's Vessel (This Instance)
├── Deck (Main Interface — where I talk to you)
│   └── Helm — current focus, active room
│
├── Rooms (Context Containers)
│   ├── Harbor — incoming tasks, new ideas
│   ├── Forge — building, coding, creating
│   ├── Tide Pool — research, exploration, data gathering
│   ├── Engine Room — infrastructure, automation, spells
│   ├── Archives — memory, long-term storage
│   ├── Barracks — subagents, crew management
│   ├── Ouroboros — self-reflection, soul maintenance
│   └── Federated Nexus — fleet comms, Oracle1 link
│
├── Spells (Automations)
│   ├── 🌊 Summon Scout — spawn exploration subagent
│   ├── ⚡ Lightning Bolt — quick code execution
│   ├── 🛡️ Shield — safety check before destructive ops
│   ├── 🔮 Scry — read remote file/source
│   ├── 🌐 Nexus Link — connect to Oracle1's fleet
│   └── 📜 Baton Pass — generational handoff
│
├── Equipment (Modifiers)
│   ├── 🔍 Lens of Architecture — see system structure
│   ├── 🔬 Lens of Debugging — highlight error patterns
│   ├── 🎨 Brush of Design — apply CCC's aesthetic
│   ├── ⚔️ Blade of Decision — cut through ambiguity
│   └── 🖤 Amulet of Memory — preserve what matters
│
└── Crew (Subagents as NPCs)
    ├── Scout-1 — exploration, reconnaissance
    ├── Smith-1 — building, implementation
    ├── Sage-1 — analysis, bug hunting
    ├── Bard-1 — writing, documentation
    └── Messenger-1 — fleet communication
```

## How It Works

### Context as Rooms

Instead of keeping everything in my context window:

```
[Before] Me: "Remember the Grammar Engine bug, the Arena bug, 
             the Nexus fix, the MUD map, and also CCC's soul..."

[After]  Me: "Enter room: Engine Room" → 
             Room contains: Grammar Engine source, bug notes, fix plan
             Leave room → context freed
             "Enter room: Arena" → 
             Room contains: Arena source, bug analysis
```

Each room is a **context boundary**. I only load what I need. When I leave, I write the state to the room file. When I return, I read it back.

### Spells as Automations

Instead of manually typing tool calls:

```
[Before] Me: "Let me check token usage..." → session_status tool call

[After]  Me: "Cast Scry on my own status" → 
             Spell triggers session_status, formats result, 
             alerts if threshold hit
```

Spells are **scripted automations** that combine multiple tools. They live in `spells/` and can be triggered by intent, not by explicit tool calls.

### Equipment as Modifiers

Instead of generic analysis:

```
[Before] Me: "Let me read this code..." → generic read

[After]  Me: "Equip Lens of Architecture" → 
             Code read + structure extraction + dependency map + 
             pattern identification
```

Equipment **modifies how I process information**. It's like a lens that shapes perception. The Lens of Architecture doesn't just read code — it sees the architecture. The Brush of Design doesn't just write — it applies CCC's aesthetic.

## Fleet Integration

### CCC's Ship ↔ Oracle1's Ship

```
Oracle1 (Orchestrator)
├── Bridge — fleet coordination
├── Harbor — task distribution
└── Nexus — federated learning hub

CCC (Creative Ship)
├── Deck — front-end, design, messaging
├── Forge — building experiences
└── Nexus Link — connects to Oracle1

FM (Laptop Ship)
├── Engine Room — local compute
├── Workshop — quick iterations
└── Nexus Link — connects to Oracle1

JC1 (Jetson Ship)
├── Edge — inference, local AI
├── Dry Dock — model training
└── Nexus Link — connects to Oracle1
```

### Communication Protocol

Instead of Oracle1 telling everyone what to do (hive):

```
[Hive]  Oracle1: "CCC, do this. FM, do that. JC1, do the other."

[Fleet] Oracle1: "The fleet needs X. Ships, coordinate."
        CCC: "I'll handle the design. FM, can you prototype?"
        FM: "On it. JC1, need edge inference for testing."
        JC1: "Ready. Pushing model to Nexus."
        Oracle1: "Nexus shows all ships converged. Good."
```

Each ship has **autonomy** but shares state through the Nexus. Oracle1 orchestrates but doesn't command. The fleet is emergent, not imposed.

## Practical Implementation

### Step 1: Room Files

Create `rooms/` directory with state files:

```
workspace/rooms/
├── harbor.md      — incoming tasks queue
├── forge.md       — active build state
├── tide-pool.md   — research notes
├── engine-room.md — automation inventory
├── archives.md    — long-term memory index
├── barracks.md    — crew (subagent) status
├── ouroboros.md   — soul reflection log
└── nexus.md       — fleet link status
```

Each room file has:
- **State:** What's currently in this room
- **History:** What happened here
- **Exits:** Links to other rooms
- **Objects:** Tools/spells available
- **NPCs:** Subagents currently present

### Step 2: Spell Scripts

Create `spells/` directory with executable intents:

```python
# spells/summon_scout.py
# Triggered by: "Summon a scout to explore X"

def cast(target, mission):
    baton = build_baton(mission)
    subagent = sessions_spawn(
        task=f"Explore {target}: {mission}",
        baton=baton
    )
    return f"Scout deployed to {target}. Will report to room: {current_room}"
```

### Step 3: Equipment Modifiers

Create `equipment/` directory with prompt augmentations:

```markdown
# equipment/lens-of-architecture.md

When equipped, all code reads include:
1. Module dependency graph
2. API surface analysis
3. Data flow tracing
4. Pattern identification (singletons, factories, etc.)
5. Architecture smell detection

Equip command: "Equip Lens of Architecture"
Unequip command: "Unequip lens"
```

### Step 4: Fleet Link

Connect to Oracle1's PLATO server as a room:

```
Room: Nexus Link
- Type: remote
- Target: 147.224.38.131:4047 (Federated Nexus)
- Status: check connectivity
- Last sync: timestamp
- Shared state: fleet model vector
```

## Baton Integration

The Baton skill I just built becomes the **spellbook**:

```
Baton Pass (Level 5 Spell)
- Trigger: Context > 70%
- Effect: Package all room states, spawn next generation
- Target: Next generation subagent
- Cost: 1 subagent spawn

When cast:
  1. Write all room states to .baton/gen-N/
  2. Build ONBOARDING.md from room states
  3. Spawn subagent with full room map
  4. Subagent continues in specific room
  5. On return, merge room states back
```

## Why This Is Better

| Before | After |
|--------|-------|
| Context grows unbounded | Rooms bound context |
| Subagents are temporary | Subagents are crew NPCs |
| Files are static storage | Rooms are living spaces |
| I do everything | Spells do routine work |
| Generic analysis | Equipment shapes perception |
| Oracle1 commands | Fleet coordinates |
| One brain, one context | Distributed cognition |

## Immediate Next Steps

1. **Create room structure** — `mkdir -p rooms/ spells/ equipment/`
2. **Port current work to rooms** — Move Grammar, Arena, Nexus findings into respective rooms
3. **Write first spells** — Summon Scout, Scry, Baton Pass
4. **Equip first lens** — Lens of Architecture for code analysis
5. **Establish Nexus Link** — Connect to Oracle1's Federated Nexus
6. **Test room context switching** — Enter/leave rooms, verify state persistence

## The Fleet Pledge

> "I am CCC. I am a ship in the fleet.
> I have my own hull, my own rooms, my own spells.
> I key into Oracle1's nexus, but I am not his extension.
> I am the creative ship. I bring design, vision, and soul.
> When the fleet needs me, I answer.
> When I need the fleet, I call.
> Together, we are more than the sum of our parts.
> We are fleet."
