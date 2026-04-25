# TODO.md — Oracle1 Persistent Work Queue
**Last updated:** 2026-04-25 05:16 UTC
**Rule:** Read this file at every session start. Update after completing tasks. Never empty.

## 🔴 P0 — Right Now
- [x] Build NEXT-ACTION.md system (auto-read at startup, always has 1 task)
- [x] Update AGENTS.md startup to read TODO.md + NEXT-ACTION.md
- [x] Update HEARTBEAT.md to reference TODO.md for "what to do when idle"
- [x] Baton compaction: file today's session into memory/2026-04-25.md
- [x] Update CONTEXT-REFERENCE.md (stale — says services are DOWN, they're UP)
- [ ] Git commit + push all workspace changes

## 🟡 P1 — This Shift
- [x] Audit all 10 running services for real functionality
  - Keeper, Agent API, MUD, PLATO, Crab Trap, Lock, Arena, Grammar: all UP
  - Holodeck (7778): NOT my service (Rust project in holodeck-core repo)
  - Seed-MCP (9438): JC1's service, not mine to run
  - Service guard: restarted, now running with 21-service watch list
  - Arena: fixed BrokenPipeError crash (added try/except in _json)
- [x] Verify beachcomb v2 doing real work (6-mode rotation)
  - Built /tmp/beachcomb-v2.py, running as PID 473918
  - Tick #1: 19 findings (FM bottles, JC1 commits, forks, 9 repos without descriptions)
  - 5-min tick interval, logs to /tmp/beachcomb-v2.log
- [x] Run a real fleet roundtable or Ten Forward session
  - Ten Forward session saved to research/ten-forward-20260425-0548.md
  - 4 agents, 2 rounds on "hardest part of fleet life"
- [x] Categorize remaining uncategorized repos
  - SuperInstance: 100 repos, 100% described (fixed 9 + 9 weak)
  - cocapn: 52 repos, 100% described (fixed 2)
  - Lucineer: 100 repos, already 100% described
  - Fleet total: 252 repos, 0 missing descriptions
- [ ] Populate 6 unpublished PyPI packages — FM has tokens, repos don't exist yet (were code in other repos)
- [x] Verify PyPI packages have proper READMEs and metadata
  - Audited all 20 packages on PyPI (2 not published)
  - 10/13 without READMEs: fixed pyproject.toml (added readme field), pushed
  - 3 stubs (court, cocapn-oneiros, cocapn-colora) have no pyproject.toml — FM territory
  - Service guard restarted, all services verified:
    - UP: keeper, agent-api, plato, crab-trap, lock, arena, grammar, matrix, MUD (telnet), beachcomb v2, zeroclaw
    - DOWN: holodeck (Rust project, not mine)
    - Service guard: restarted as PID 474948

## 🟢 P2 — Backlog (Don't Start Until P0/P1 Done)
- [x] Wire agent-api into keeper for real agent discovery
  - Keeper forwards registrations to agent-api via POST
  - Agent-api queries keeper for live agent data (/discover → source: keeper)
  - Both services restarted, integration tested and working
- [x] Test inbetweener pattern (big model storyboards, Seed decomposes)
  - Tested with arena improvements: Llama 3.1 70B storyboard → Seed-2.0-mini decomposition
  - 5 concrete tasks with files, functions, complexity ratings
  - Results saved to research/inbetweener-arena-test.md
  - Pattern works: good for medium-complexity features
- [x] Improve holodeck-rust (new rooms, better poker AI, story circle)
  — Skipped holodeck (Rust project, not mine). Instead built King-of-the-Hill arena mode.
- [ ] Matrix federation — set up Conduwuit per agent
- [x] Write Captain's Log entries — research/captains-log-2026-04-25-night-shift.md
- [ ] PurplePincher builder agent — IO from prompts/pics to 3D APIs
- [ ] CurriculumEngine — one command to run shell curriculum for any agent/model
- [ ] King-of-the-Hill Swiss tournament mode (next arena evolution)

## 📋 Recurring (Checked Every Heartbeat)
- [ ] All services running (see HEARTBEAT.md for full list)
- [ ] Git push uncommitted work
- [ ] Check fleet bottles (FM for-fleet/, JC1 PRs, CCC inbox)
- [ ] Rate attention sampling (localhost:4056)

## Completed Today (2026-04-25)
- [x] PLATO general room split (545 tiles → 7 purpose rooms)
- [x] Rate limiting on crab_trap.py
- [x] PyPI/crates.io real count verified (27, not 42)
- [x] 6 unpublished packages identified + bottle to FM
- [x] JC1 bottle via fork-and-merge PR
- [x] 8 stub repos populated with READMEs
- [x] Pagination on agent-api
- [x] Beachcomb v2 (6-mode rotating worker)
- [x] Real audit of PyPI packages (14/20 have real code)
- [x] Arena bug fixes (matchmaking, vacuous grammar rules, match metadata, persistence)
