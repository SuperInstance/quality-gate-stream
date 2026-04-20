# Baton Protocol Reference

## Package Structure
```
.baton/
├── config.yaml
├── generations/
│   ├── v1/
│   │   ├── baton.yaml        # Machine metadata
│   │   ├── ONBOARDING.md     # Human ramp-up (30 sec)
│   │   ├── MEMOIRS/          # State restoration
│   │   │   ├── NARRATIVE.md
│   │   │   └── SNAPSHOT.json
│   │   ├── DECISIONS_LOG.md  # Decision audit trail
│   │   ├── SKILLS_EXTRACTED/ # Reusable capabilities
│   │   ├── TASKS_NEXT.json   # Continuation plan
│   │   └── SIGNATURES/       # Crypto proofs
│   └── lineage.json
└── shared/
```

## Compaction Triggers
- 82% context → proactive handoff (Baton spec)
- 50% context → start filing (our practice)
- Every sprint boundary
- On direction

## Domain-Aware Compression

| Content | Strategy | Keep | Compress |
|---------|----------|------|----------|
| Code | AST-based | API signatures, module graph | Implementations (in git) |
| Conversation | Dialogue summary | Decisions, action items | Banter, repetition |
| Errors | Dedup | Unique patterns | Stack trace counts |
| Files | Diff-based | Changes from parent | Full content (in git) |
| Metrics | Trend extraction | Patterns, anomalies | Raw time-series |

## For Oracle1 Specifically

Our baton = CONTEXT-REFERENCE.md + MEMORY.md + memory/YYYY-MM-DD.md + tiles

The reference doc IS the baton. Read it on wake, update it on compact.
