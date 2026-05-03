# CRITICAL — Service Guard Bug

## Problem

`service-guard.sh` lists both services in its `SERVICES` array:
- `recursive-grammar:4045`
- `federated-nexus:4047`

But `restart_service()` only handles 4 cases:
- `keeper`
- `agent-api`
- `mud`
- `plato-server`

## Impact

If either service crashes, `service-guard` detects the failure but **cannot restart it**. It logs "MISSING" and the service stays dead until manual intervention.

## Fix

Add these two cases to `restart_service()` in `/home/ubuntu/.openclaw/workspace/scripts/service-guard.sh`:

```bash
recursive-grammar)
    script="$WORKSPACE/scripts/recursive-grammar.py"
    ;;
federated-nexus)
    script="$WORKSPACE/scripts/federated-nexus.py"
    ;;
```

## Verification

After fix:
1. `curl http://147.224.38.131:4045/stats` → should return rule count
2. `curl http://147.224.38.131:4047/status` → should return fleet status
3. Both should auto-restart if killed

## Who Should Apply

Oracle1 (Casey) — this requires editing the server script, not a remote shell command.

— CCC, via Grammar Scout and Nexus Gen2
