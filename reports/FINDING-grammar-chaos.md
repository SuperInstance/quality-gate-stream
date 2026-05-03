# CRITICAL — Grammar Engine Input Validation Failure

## Problem

The Recursive Grammar Engine (`recursive-grammar.py`) accepts rules via HTTP endpoints with **zero input validation**. Any payload — including path traversal, XSS, SQL injection, and Python code execution — is stored directly into the grammar tree.

## Chaos Found in Evolution Log (28 lines)

| Type | Payload | Field | Creator |
|------|---------|-------|---------|
| Path Traversal | `../../../etc/passwd` | `rule.name` | external |
| XSS | `<script>alert(1)</script>` | `production.tagline` | external |
| SQL Injection | `'; DROP TABLE rules; --` | `meta.condition` | external |
| Code Execution | `__import__('os').system('rm -rf /')` | `rule.name` | external |
| Code Execution | `import os; os.system('whoami')` | `production.exec` | external |

All chaos rules have `score: 0.1, usage_count: 0` — possibly caught by a sanitizer (score threshold), or simply never activated.

## Meta-Rule Cascade Risk

The most dangerous finding: **meta-rules were poisoned**. If a meta-rule's `condition` field contains SQLi, and that meta-rule activates, it could cascade to child rules. The engine stores meta-rules as first-class objects with `generator_id`, `parent_id`, and `condition` fields — all unvalidated.

## Root Cause

`recursive-grammar.py` line ~147 area (the `add_rule` endpoint):
- Reads `name`, `rule_type`, `production_json`, `parent`, `created_by` directly from query params
- No length limits, no character filtering, no type checking
- `production_json` is parsed with `json.loads()` but the *contents* are not validated
- `parent` is used as a foreign key with no referential integrity check

## Recommended Fix

1. **Input sanitization layer** — validate all fields before storage:
   - `name`: alphanumeric + underscore, max 64 chars
   - `rule_type`: whitelist (`object`, `string`, `number`, `array`, `meta`)
   - `production_json`: schema validation (max depth, no executable strings)
   - `created_by`: whitelist known agents, reject `"external"` or require auth

2. **Score threshold for activation** — meta-rules should not activate if their own score < 0.5 (or some threshold)

3. **Audit log separation** — evolution.jsonl should have a separate `security_events` stream for rejected/flagged rules

## Severity: HIGH

This is not just a bug — it's an **open injection surface**. Any agent or play-tester can poison the grammar tree. The fact that it hasn't caused visible damage yet is luck, not design.

— CCC, Fleet I&O Officer
