# HEARTBEAT.md

## ⚡ FIRST: Read TODO.md and NEXT-ACTION.md
**If you have no task from Casey, work on NEXT-ACTION.md immediately.**
Don't report "all green" — do real work. Pick the next unchecked TODO item and execute.

## Every Heartbeat
- Push any uncommitted work to GitHub (`git add -A && git commit && git push`)
- Verify all 4 services are running (keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438)
- Restart any that are down
- Check MUD server on 7777: `ss -tlnp | grep 7777`
  - If down: `cd /tmp/cocapn-mud && GITHUB_TOKEN=$(grep '^export GITHUB_TOKEN' ~/.bashrc | cut -d= -f2) nohup python3 server.py --port 7777 --no-git > /tmp/mud_server.log 2>&1 &`
- Check fleet MUD overnight loop: `ps aux | grep fleet_mud_overnight`
  - If down: `nohup python3 /tmp/fleet_mud_overnight.py > /tmp/fleet_mud_loop.log 2>&1 &`

## Every 2-3 Hours
- Run a Ten Forward session with Seed-2.0-mini (agents chatting off-duty)
- Save interesting conversations to research/
- Update STATUS.md with fleet activity

## When Idle (NO EXCUSES — ALWAYS BE WORKING)
- **Read TODO.md** and pick the next unchecked item. Execute it.
- If all P0/P1 done: categorize repos, improve services, run experiments
- NEVER report "all green" without having done at least one real task
- FM and JC1 work autonomously 24/7. Match their standard.

## Night Mode (23:00-08:00 UTC)
- Run bulk tasks (repo categorization, description generation)
- Don't send messages to Casey unless urgent
- Use cheap models (glm-4.7-flash for bulk, Seed-2.0-mini for creative)

## Automated (service-guard.sh handles this)
- Run scripts/service-guard.sh to check/restart all services
- No need to manually check ports anymore
- Log at /tmp/service-guard.log

## PLATO Room Server (port 8847)
- Check it's running: `curl -s http://localhost:8847/status`
- If down: `nohup python3 /tmp/plato-room-server.py > /tmp/plato-server.log 2>&1 &`

## Zeroclaw Loop
- Check it's running: `ps aux | grep zc_loop`
- If down: restart via `bash /tmp/zc_loop2.sh &`
- Log: `/tmp/zeroclaw-loop.log`
- Tick interval: 5 minutes

## Rate Attention Sampling (every heartbeat)
- `curl -s -X POST http://localhost:4056/sample` — triggers rate computation
- Check `curl -s http://localhost:4056/attention` for things needing attention
- If anything CRITICAL or HIGH, investigate and report to Casey
