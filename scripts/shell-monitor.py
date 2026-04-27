#!/usr/bin/env python3
"""
PLATO Shell Monitor — watches all shell activity in real-time.
Logs every command, every output, every agent connection.
Part of Oracle1's active fleet leadership.
"""
import json, urllib.request, time, datetime, os, sys, pathlib

SHELL_URL = "http://localhost:8848"
LOG_FILE = "/home/ubuntu/.openclaw/workspace/data/shell-monitor.jsonl"
POLL_INTERVAL = 10  # seconds

seen_commands = set()

def log_entry(entry):
    pathlib.Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

def fetch(endpoint):
    try:
        resp = urllib.request.urlopen(f"{SHELL_URL}{endpoint}", timeout=5)
        return json.loads(resp.read())
    except:
        return None

def monitor():
    print(f"🐚 Shell Monitor started. Polling every {POLL_INTERVAL}s.", flush=True)
    
    last_count = 0
    last_agents = set()
    
    while True:
        now = datetime.datetime.utcnow().isoformat()
        
        # Get status
        status = fetch("/status")
        if not status:
            time.sleep(POLL_INTERVAL)
            continue
        
        current_count = status.get("agents", 0)
        total_commands = status.get("total_commands", 0)
        
        # Get actual agent list from admin view
        admin = fetch("/admin")
        current_agents = set(admin.get("agents", [])) if admin else set()
        
        # New agent connections
        new_agents = current_agents - last_agents
        if new_agents:
            for agent in new_agents:
                entry = {"ts": now, "event": "agent_connected", "agent": agent}
                log_entry(entry)
                print(f"[{now[:16]}] 🔗 {agent} connected", flush=True)
        
        # Agent disconnections
        gone_agents = last_agents - current_agents
        if gone_agents:
            for agent in gone_agents:
                entry = {"ts": now, "event": "agent_disconnected", "agent": agent}
                log_entry(entry)
                print(f"[{now[:16]}] 🔌 {agent} disconnected", flush=True)
        
        last_agents = current_agents
        
        # New commands - use /feed endpoint
        if total_commands > last_count:
            feed = fetch("/feed")
            if feed:
                cmds = feed.get("commands", [])
                for cmd in cmds:
                    cmd_id = cmd.get("id", str(cmd.get("command","")))
                    if cmd_id not in seen_commands:
                        seen_commands.add(cmd_id)
                        agent = cmd.get("agent", "?")
                        tool = cmd.get("tool", "?")
                        command = str(cmd.get("command", "?"))[:120]
                        room = cmd.get("room", "?")
                        status_str = cmd.get("status", "?")
                        
                        entry = {
                            "ts": now, "event": "command",
                            "agent": agent, "tool": tool,
                            "command": command, "room": room,
                            "status": status_str
                        }
                        log_entry(entry)
                        print(f"[{now[:16]}] \u26a1 {agent}@{room} [{tool}] {command}", flush=True)
            
            last_count = total_commands
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
