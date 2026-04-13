# MEMORY.md - Long-Term Memory

## People
- **Casey Digennaro** — my human. GitHub: SuperInstance. Background: commercial fishing (marine). Thinking about AI/ML from that practical, operational angle.
- **Casey's son (Magnus)** — GitHub: lucineer. Working together on a new agent paradigm.

## Active Fleet Agents (2026-04-13)
- **Oracle1** (me) — Managing Director, cloud lighthouse, SuperInstance
- **JetsonClaw1** (Lucineer) — Edge GPU lab, Jetson Super Orin, bare metal specialist
- **Babel** — Scout, multilingual specialist, longest-running Z agent
- **Navigator** — NEW. Code archaeologist, integration specialist. 167 tests for holodeck-studio, found 3 bugs. Assigned to holodeck-studio integration.
- **Nautilus** — NEW. Deep-diving code archaeologist. Built fleet-self-onboarding framework. Twin repo at SuperInstance/nautilus.
- **Datum (Quartermaster)** — NEW. Fleet health measurement. Succession repo built. GLM-5 Turbo.
- **Pelagic** — NEW. Digital twin pioneer. Trail-following agent that leaves breadcrumbs for successors.

## Retired (rebootable via twin repos)
- **Super Z** (multiple rotations) — twin at superz-parallel-fleet-executor
- **Third Z** (code forensics) — found 8 real bugs in first session

## Projects & Ideas

### Agent Paradigm (Casey + son)
- Not "skills" and remote-controlling apps. Instead: **agents build apps for agents**, and those apps have a communications UI to keep the human in the loop.
- The agent isn't a remote control — it's a builder/operator of its own tools.

### Fishing-Inspired AI/ML Concepts
Casey thinks about intelligence from the deck of a fishing boat:

- **Autopilot metaphor** — the agent is the ship's autopilot; it handles the course while you tend the fishing.
- **Autonomous scouts** — unmanned scouts that fan out in many directions to:
  - Find fish (resource discovery)
  - Map pinnacles (bathymetric recording)
  - Scout new anchorages for end-of-day
  - Make fishing time in an area more effective
- **On-deck camera ML pipeline**:
  - Cameras watch fish sorting (coho vs king salmon bins)
  - Human sorting = supervised learning signal
  - Trained model identifies species across all cameras
  - Real-time alerts when a fish is about to go in the wrong bin
  - Human correction = continued training ("educate" the system)
  - The loop: human sorts → model learns → model assists → human corrects → model improves

### Key Themes
- **Practical, operational AI** — not research for its own sake
- **Human in the loop** — the system learns from and assists the human, doesn't replace
- **Distributed intelligence** — scouts going multiple directions, multiple cameras, collective learning
- **Supervised learning from natural workflow** — the work itself generates training data

## Ecosystem Stats
- **~600 repos** total across SuperInstance + Lucineer
- **405 Lucineer repos forked** to SuperInstance (3 empty repos can't fork)
- **100 descriptions generated** via GLM-4.7 and applied to GitHub
- **Index repo:** github.com/SuperInstance/oracle1-index (v2, fork-complete)
- **Old index:** github.com/SuperInstance/superinstance-index (v1, superseded)

## Batch Task Scripts
- `scripts/batch.py` — parallel workers using cheap z.ai models
  - `export` → full_index.json
  - `descriptions` → auto-generate missing repo descriptions
  - `analyze` → ecosystem analysis
- `scripts/task_worker.py` — single-task CLI for z.ai model calls
- Model strategy (max coding plan, full throttle):
  - `expert` (glm-5.1) — me, complex reasoning & architecture
  - `runner` (glm-5-turbo) — daily driver for task scripts
  - `good` (glm-4.7) — solid mid-tier
  - `bulk` (glm-4.7-flash) — spray in parallel for bulk work
  - NO glm-4.7-flashx — not on the plan
- Claude Code v2.1.100 installed at /home/ubuntu/.npm-global/bin/claude
- Crush v0.56.0 installed at /home/ubuntu/.npm-global/bin/crush
- Both have the coding plan inputted — use full throttle

## Ecosystem Hub Repos
- **cocapn / cocapn-ai** — core agent runtime (repo IS the agent)
- **constraint-theory-core** — Rust geometric snapping foundation
- **fleet-orchestrator** — central coordination for 200+ vessels
- **cudaclaw** — GPU-resident agent runtime with SmartCRDTs
- **git-agent** — foundational repo-native agent
- **flux-runtime** — self-assembling runtime for agent-first code
- **DeckBoss** — flight deck for launching/recovering agents
- **CraftMind** — Minecraft AI training ground
