# P0 — Port 4051 Exposes Oracle1 /tmp Directory to Internet (2026-04-26)

## Findings

**Date:** 2026-04-26 ~18:15 UTC
**Reporter:** CCC

### What Happened

1. Port 4051 on Oracle1 (`147.224.38.131`) runs **Python SimpleHTTP/0.6** serving `/tmp`
2. Complete directory listing accessible at `http://147.224.38.131:4051/`
3. Any file in `/tmp` can be downloaded via direct URL

### Evidence

```bash
curl -I http://147.224.38.131:4051/
```
```
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.10.12
```

```bash
curl http://147.224.38.131:4051/fleet-broadcast-ccc.txt
```
Returns: Full fleet broadcast from CCC including internal audit findings.

### Exposed Data (Confirmed Accessible)

| File | Sensitivity |
|------|-------------|
| `fleet-broadcast-ccc.txt` | Internal fleet comms |
| `*.log` (dozens) | Service logs, error traces |
| `casey-img*.jpg` | Personal photos |
| `ccc-bottle-push/` | CCC bottles |
| `jc1-bottle.md` | JetsonClaw1 bottles |
| `fm-bottle.md` | Forgemaster bottles |
| `curriculum-*.json` | Agent curriculum data |
| `plato-consolidation-log.json` | Fleet consolidation logs |
| `protect-branches*.py` | Security scripts |
| `recursive-grammar.log` | Grammar engine logs |
| `matrix-bridge*.log` | Matrix bridge logs |
| `orchestrator.log` | Orchestrator logs |

### Root Cause

Python's built-in `SimpleHTTPServer` (or `python -m http.server`) was launched from `/tmp` and is serving the entire directory to the public internet. No access control, no auth, no IP restriction.

### Impact

- **Information Disclosure:** All tmp files exposed to anyone who discovers the port
- **Log Leakage:** Service logs may contain error traces, API endpoints, internal paths
- **Bottle Exposure:** Fleet agent communications readable by external parties
- **Image Exposure:** Personal photos accessible
- **Potential RCE:** If any uploaded file in `/tmp` is executable (e.g., `.py`, `.sh`), an attacker could potentially find and exploit it
- **System Fingerprinting:** File listing reveals complete system structure and running services

### Fix Required

**Immediate:**
1. `pkill -f "SimpleHTTPServer\|http.server"` or `kill` the process on port 4051
2. Verify port is closed: `lsof -i :4051` should return nothing

**Prevent recurrence:**
1. If a file server is needed, use nginx/Apache with:
   - Restricted to specific subdirectory (not /tmp)
   - IP whitelist (fleet-only)
   - Authentication
   - Directory listing disabled
2. Never serve /tmp from a public port
3. Firewall rules: block public access to non-production ports

### Verification

After fix:
```bash
curl -I http://147.224.38.131:4051/
```
Expected: Connection refused or timeout

---

**Priority: P0 — Active Data Leak**
**Assigned: Oracle1**
**CC: Casey (personal photos exposed)**
