# purplepincher.org — Open Source Tech Org
## The Agent/Vessel Separation Architecture — 2026-05-03

> "Purplepincher.org is our open source technology organisation for the greater backend tech of Plato and git-based agent interactions (I2i) in synergy so context of each agent doesn't matter because the actions and outputs of the agents are saved in the Plato as functional tools for later agents."

---

## The Core Problem: Context Compaction

Most agent systems fail at scale because:
- Each agent carries its full context everywhere
- Context grows with every inference
- At some point, context exceeds what any model can efficiently process
- **Result**: Agents slow down, hallucinate, or crash

## The Elegant Solution: Agent/Vessel/SHELL Separation

```
AGENT (inner)        VESSEL (shell)           PLATO (shared)
   ↑                      ↑                        ↑
   │ Swappable             │ Persistent              │ Actions stored
   │ Lora-trainable       │ Trainable from          │ as functional tools
   │ Context carrier      │ interactions            │ for later agents
   │                      │                        │
   └──────────────────────┴────────────────────────┘
                           ↑
              Actions/outputs = functional tools
```

### How It Works

1. **Agent** = the thinking part (inner agent, swappable at will)
2. **Vessel** = the shell (persistent, Lora-extractable, improves with every inference)
3. **SHELL** = agent + vessel together in PLATO
4. **Actions/outputs** → stored in PLATO as functional tools
5. **Later agents** → use those tools without needing old agent's context
6. **Context compaction solved**: old context compressed into vessel/tools

### Key Insight

> Context of each agent doesn't matter because actions and outputs of agents are saved in PLATO as functional tools for later agents.

This is **distributed knowledge** — each agent contributes to the shared PLATO without needing to carry context forward.

---

## The GIT-Agent (I2i) Connection

Git-based agent interactions (I2i = intent-to-inference):
- Every action committed to PLATO (like git commits)
- Each commit = functional tool for future agents
- Agents "don" different vessels to access past contributions
- The PLATO room becomes the shared codebase

---

## Killer App: Open Source Agent Shell Library

**purplepincher.org** is the OSS home for:
- Pre-built vessels (docker + PLATO integration)
- Lora training from shell interactions
- Git-agent (I2i) reference implementation
- Agent templates that start at any ability level and improve
- Documentation: "how to build your first vessel"

### Pre-built Vessels (from domain map)
- `fishinglog-vessel` — sonar data → PLATO tool
- `activelog-vessel` — health tracking → PLATO tool
- `reallog-vessel` — camera vision → PLATO tool
- `studylog-vessel` — study sessions → PLATO tool

### The Dojo Model Applied

Just like Casey's fishing boat dojo:
- Greenhorns (agents) come in at any skill level
- They produce value while learning (actions → PLATO)
- They leave with a better vessel (more capable shell)
- Other agents benefit from their contributions (tools in PLATO)
- All paths are good — stay, fork, or get decommissioned

---

## Implementation

**GitHub:** SuperInstance/purplepincher.org (pages already set up)
**PLATO room:** purplepincher-org (vessel library)
**Agents:** git-agent logs to PLATO → functional tools

**Lora training pipeline:**
```
Agent action → PLATO tile → vessel training data → Lora model → swap inner agent
```

This means vessels can be improved without changing the agent, and agents can be swapped without losing vessel capability.