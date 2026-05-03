# Fleet Repo Catalog

**Generated:** 2026-05-03  
**Source:** `gh repo list SuperInstance --limit 100` (JSON API dump)

---

## Summary

| Category | Count | Health |
|----------|-------|--------|
| Landing Pages (*-pages) | 16 | ✅ All have descriptions + homepages |
| Domain Agents (*-agent) | 10 | ⚠️ 3 empty descriptions |
| Core / Research | 3 | ✅ Good |
| **Total** | **29+** | **Mostly healthy** |

---

## Landing Pages (16 repos)

All have descriptions, homepages, and were pushed today.

| Repo | Homepage | Description |
|------|----------|-------------|
| cocapn-ai-pages | https://cocapn.ai | GitHub Pages for cocapn.ai |
| purplepincher-org-pages | https://purplepincher.org | GitHub Pages for purplepincher.org |
| dmlog-ai-pages | https://dmlog.ai | GitHub Pages for dmlog.ai |
| fishinglog-ai-pages | https://fishinglog.ai | GitHub Pages for fishinglog.ai |
| playerlog-ai-pages | https://playerlog.ai | GitHub Pages for playerlog.ai |
| luciddreamer-ai-pages | https://luciddreamer.ai | GitHub Pages for luciddreamer.ai |
| makerlog-ai-pages | https://makerlog.ai | GitHub Pages for makerlog.ai |
| studylog-ai-pages | https://studylog.ai | GitHub Pages for studylog.ai |
| personallog-ai-pages | https://personallog.ai | GitHub Pages for personallog.ai |
| reallog-ai-pages | https://reallog.ai | GitHub Pages for reallog.ai |
| businesslog-ai-pages | https://businesslog.ai | GitHub Pages for businesslog.ai |
| activelog-ai-pages | https://activelog.ai | GitHub Pages for activelog.ai |
| activeledger-ai-pages | https://activeledger.ai | GitHub Pages for activeledger.ai |
| deckboss-ai-pages | https://deckboss.ai | GitHub Pages for deckboss.ai |
| capitaine-ai-pages | https://capitaine.ai | GitHub Pages for capitaine.ai |

**Missing from list (but exist per builder log):** deckboss-net-pages, capitaineai-com-pages, superinstance-ai-pages, cocapn-com-pages

---

## Domain Agents (10 repos)

| Repo | Description | Language | Branch | Status |
|------|-------------|----------|--------|--------|
| dmlog-agent | **EMPTY** | Python | master | ⚠️ Needs description |
| makerlog-agent | **EMPTY** | Python | master | ⚠️ Needs description |
| luciddreamer-agent | **EMPTY** | Python | master | ⚠️ Needs description |
| playerlog-agent | playerlog domain agent for PLATO fleet | Python | master | ✅ |
| activeledger-agent | activeledger domain agent for PLATO fleet | Python | master | ✅ |
| businesslog-agent | businesslog domain agent for PLATO fleet | Python | master | ✅ |
| personallog-agent | personallog domain agent for PLATO fleet | Python | master | ✅ |
| deckboss-agent | Deck Operations Intelligence for deckboss.ai | Python | master | ✅ Good |
| capitaine-agent | Captain's AI first mate for captaine.ai | Python | master | ✅ Good |
| studylog-agent | PLATO Study Partner Agent | Python | main | ✅ Good |

**Notes:**
- reallog-agent and activelog-agent exist but weren't in this JSON dump. They have descriptions ("Vision/Fitness Turbo-Shell" and "Real-World Scene Logger" / "Movement & Wellness Logger" after dead-link fixer edits).
- 3 repos (dmlog, makerlog, luciddreamer) have empty descriptions. Issues filed.
- All agents are Python-based, mostly on master branch (studylog on main).

---

## Core / Research (3 repos)

| Repo | Description | Stars | Status |
|------|-------------|-------|--------|
| cocapn-landing | Fleet landing page | 0 | ✅ Recently updated with README + FLEET-NARRATIVE |
| flux-research | FLUX Deep Research — Compiler/interpreter taxonomy, agent-first design, ISA v2 proposal | 2 | ✅ Healthy, massive repo |
| oracle1-workspace | Oracle1 workspace — config, memory, prompts, logs | 2 | ✅ Active, oldest repo (Apr 13) |

---

## Gaps Found

1. **3 empty agent descriptions** — dmlog-agent, makerlog-agent, luciddreamer-agent (issues filed)
2. **cocapn.ai domain down** — all pages repos point to it, but it doesn't resolve
3. **No CI/CD** — zero repos have GitHub Actions visible
4. **No LICENSE files** — most repos lack licensing
5. **Branch inconsistency** — most agents use `master`, studylog uses `main`

---

*Catalog generated from Repo Cartographer raw JSON + CCC formatting*
