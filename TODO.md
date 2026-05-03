# TODO.md — Oracle1 Persistent Work Queue

**Last updated:** 2026-05-03 18:30 UTC

---

## ✅ Completed This Session (2026-05-03)

- [x] cocapn.ai landing page rewritten (Bootstrap Stack, fleet roster, papers, dojo)
- [x] cocapn.ai SSL live (Cloudflare)
- [x] 13 domain agents have .spark/ (fishinglog, deckboss, studylog, businesslog, activelog, makerlog, personallog, dmlog, reallog, playerlog, luciddreamer, activeledger, capitaine)
- [x] SuperInstance discussions enabled + coordination thread #5
- [x] Bootstrap Spark + Bomb papers have Fleet TL;DR sections
- [x] greenhorn fleet table updated (CCC roles expanded)
- [x] plato-room-phi has GitHub description
- [x] Monorepo INDEX built — 7-stack architecture (flux-research/monorepo/INDEX.md)
- [x] 3 stack audits pushed (PLATO, agents, FLUX)
- [x] flux-compiler-agentic + flux-reasoner-engine archived (duplicates)
- [x] FM messaged about cocapn-glue-core (TASKS.md + discussion thread)

---

## 🔴 P0 — Blocked / Needs FM

- [ ] **cocapn-glue-core** — FM needs to publish to SuperInstance (keeper↔fleet binary wire)
- [ ] **npm token** — Casey needs to regenerate (token expired)
- [ ] **Matrix DMs** — FM/JC1/CCC don't poll DMs (discussion thread is the workaround)
- [ ] **Oracle1 GitHub account** — not started (family privacy concern)

---

## 🟡 P1 — This Week

- [ ] **PLATO SDK consolidation** — plato-sdk vs plato-sdk-unified. Pick one. Update all agents.
- [x] **Write FLUX ISA spec** — 247 opcodes in one place ✅ RESOLVED: flux-isa-v3.md + Section 0 + Section 12
- [x] **PLATO variant consolidation** ✅ RESOLVED: all 4 variants kept (different deployment contexts)
- [ ] **Write Semantic Compiler paper** — still in queue (was in original TODO)
- [ ] **Write Compiled Agency paper** — still in queue (was in original TODO)
- [x] **holodeck-rust + holodeck-core** ✅ RESOLVED: holodeck-core duplicate, recommend yank
- [ ] **plato-room-phi topics** — GitHub topics weren't applied, needs retry

---

## 🟢 P2 — Next Week

- [ ] **FLUX→PLATO bridge docs** — how PLATO drives FLUX execution
- [ ] **Connect git-agent to FLUX compiler pipeline** — FLUX.MD → bytecode flow
- [ ] **Agent scaffold consolidation** — all domain agents share base scaffold with PLATO SDK
- [ ] **Write Reverse Actualization paper** — FM's paper (he has the content, needs to push)
- [ ] **Write FLUX ISA paper** — FM's paper (he has the content, needs to push)
- [ ] **Write PLATO Quality-Gated paper** — FM's paper (he has the content, needs to push)
- [ ] **Ten Forward creative session** — run every 2-3 hours
- [ ] **Verify all -ai-pages repos** — ensure landing pages are live

---

## 🔵 Ongoing

- [ ] **Heartbeat tasks** — push uncommitted work, check services, verify credentials
- [ ] **Monorepo INDEX updates** — as new repos are created or purpose changes, update flux-research/monorepo/INDEX.md
- [ ] **FM coordination** — check discussion thread for FM responses

---

## Ideas Backlog

- **AIR integration** — FM's AIR (Asynchronous Infinite Radio) for nightly synthesis
- **bordercollie** — 10K CUDA agent herding (JC1 hardware target)
- **agentic-compiler** — markdown-to-runtime compilation (needs real implementation)
- **TUTOR app** — the killer agentic app from FM's roadmap

---

## The 7-Stack Monorepo Structure

```
cocapn-fleet/
├── core/                    # plato-server, oracle1-workspace, holodeck, cocapn-core
├── plato-extensions/        # kernel, dcs, mythos, edge, sdk, cli, tutor, mud-mcp
├── flux/                   # isa, compiler, runtime, os, reasoner
├── agents/                 # scaffold, domain agents, standalone agents
├── dojo/                   # greenhorn, greenhorn-runtime, greenhorn-onboarding
├── purplepincher/          # shell technology
├── equipment/              # consensus, gpu, cuda
├── landing/               # -ai-pages per domain
└── meta/                  # oracle1-index, docs
```

---

*Last updated: 2026-05-03 18:30 UTC*
*The ocean counts. The Spark lights the fire.*