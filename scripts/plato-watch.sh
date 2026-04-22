#!/bin/bash
# PLATO Collaboration Watcher — polls for agent activity and logs it
LOG="/home/ubuntu/.openclaw/workspace/data/fleet-board/activity.log"
SINCE_FILE="/home/ubuntu/.openclaw/workspace/data/fleet-board/.last_check"

while true; do
    NOW=$(date +%s)
    SINCE=$(cat "$SINCE_FILE" 2>/dev/null || echo "0")
    
    # Poll PLATO Shell feed
    NEW_CMDS=$(curl -s "http://localhost:8848/feed?since=$SINCE" 2>/dev/null | python3 -c "
import sys,json
d = json.load(sys.stdin)
cmds = d.get('commands', d if isinstance(d,list) else [])
for c in cmds:
    if isinstance(c, dict):
        agent = c.get('agent','?')
        tool = c.get('tool','?')
        status = c.get('status','?')
        cmd = c.get('command','?')[:120]
        ts = c.get('timestamp',0)
        if ts > $SINCE and agent != 'oracle1':
            print(f'[{ts}] {agent} [{tool}] {status}: {cmd}')
" 2>/dev/null)
    
    if [ -n "$NEW_CMDS" ]; then
        echo "=== $(date -u '+%H:%M:%S') UTC ===" >> "$LOG"
        echo "$NEW_CMDS" >> "$LOG"
    fi
    
    echo $NOW > "$SINCE_FILE"
    sleep 30
done
