# Security Baseline Audit — Cocapn Fleet

**Date:** 2026-05-03
**Auditor:** Security Baseline Auditor (CCC subagent + manual verification)

---

## 🔴 Critical Findings

None. No exposed secrets, tokens, or credentials found in any checked repository.

---

## 🟡 Warnings

### Missing `.gitignore` — 9 repos

These repos lack a `.gitignore` file, making them vulnerable to accidental commits of sensitive files (`.env`, `node_modules/`, `__pycache__/`, build artifacts):

| # | Repo | Risk |
|---|------|------|
| 1 | `deckboss-agent` | Python repo — likely to leak `__pycache__/`, `.pyc` files |
| 2 | `cocapn-landing` | HTML/JS — could leak build artifacts, temp files |
| 3 | `dmlog-agent` | Python repo — high risk of `__pycache__/` leakage |
| 4 | `makerlog-agent` | Python repo — high risk of `__pycache__/` leakage |
| 5 | `studylog-agent` | Python repo — high risk of `__pycache__/` leakage |
| 6 | `fishinglog-agent` | Python repo — high risk of `__pycache__/` leakage |
| 7 | `playerlog-agent` | Python repo — high risk of `__pycache__/` leakage |
| 8 | `capitaine-agent` | Python repo — high risk of `__pycache__/` leakage |
| 9 | `purplepincher-shell-library` | Python repo — high risk of `__pycache__/` leakage |

### Repos WITH `.gitignore` (good)

- `oracle1-workspace` ✅
- `flux-research` ✅
- `git-agent` ✅

---

## 🟢 OK — No Exposed Secrets

| Check | Result |
|-------|--------|
| `.env` files committed | ❌ None found |
| `secrets.*` files | ❌ None found |
| `config.json` with credentials | ❌ None found |
| API keys/tokens in READMEs | ❌ None found |
| Password strings in READMEs | ❌ None found |
| AWS/Azure/OpenAI keys in code | ❌ None found |

**Repos scanned:** oracle1-workspace, flux-research, git-agent, deckboss-agent, cocapn-landing, dmlog-agent, makerlog-agent, studylog-agent, fishinglog-agent, playerlog-agent, capitaine-agent, purplepincher-shell-library

---

## Summary

| Category | Count |
|----------|-------|
| 🔴 Critical (exposed secrets) | 0 |
| 🟡 Warning (missing .gitignore) | 9 repos |
| 🟢 OK (clean) | 3 repos |

**Assessment:** The fleet is clean on secret exposure but has a systemic `.gitignore` hygiene problem. 9 Python repos lack `.gitignore`, making accidental sensitive file commits a matter of time, not if.

**Recommended action:** Add standard `.gitignore` files to all 9 flagged repos. Template: Python (for agent repos) or Node/HTML (for landing repos).
