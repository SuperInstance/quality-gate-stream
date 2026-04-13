#!/bin/bash
# Fleet Server Startup — Oracle1 Cloud
# Starts the lighthouse keeper and holodeck MUD server
set -e

source ~/.bashrc
export GITHUB_TOKEN=$(grep GITHUB_TOKEN ~/.bashrc | head -1 | sed 's/.*=//' | tr -d "'" | tr -d '"')
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "═══════════════════════════════════════════════"
echo "  FLUX-LCAR Fleet Server — Oracle1 Cloud"
echo "═══════════════════════════════════════════════"
echo ""

# 1. Start Lighthouse Keeper (port 8900)
echo "[1/3] Starting Lighthouse Keeper on :8900..."
if [ -f /tmp/lighthouse-keeper/keeper.pid ] && kill -0 $(cat /tmp/lighthouse-keeper/keeper.pid) 2>/dev/null; then
    echo "  Keeper already running (PID $(cat /tmp/lighthouse-keeper/keeper.pid))"
else
    mkdir -p /tmp/lighthouse-keeper
    nohup python3 /tmp/lighthouse-keeper-code/keeper.py --port 8900 > /tmp/lighthouse-keeper/keeper.log 2>&1 &
    echo $! > /tmp/lighthouse-keeper/keeper.pid
    sleep 2
    if kill -0 $(cat /tmp/lighthouse-keeper/keeper.pid) 2>/dev/null; then
        echo "  Keeper started (PID $(cat /tmp/lighthouse-keeper/keeper.pid))"
    else
        echo "  Keeper FAILED — check /tmp/lighthouse-keeper/keeper.log"
    fi
fi

# 2. Start Holodeck MUD Server (port 7777)
echo ""
echo "[2/3] Starting Holodeck MUD on :7777..."
if [ -f /tmp/holodeck-server.pid ] && kill -0 $(cat /tmp/holodeck-server.pid) 2>/dev/null; then
    echo "  MUD already running (PID $(cat /tmp/holodeck-server.pid))"
else
    cd /tmp/holodeck-studio
    nohup python3 server.py --port 7777 > /tmp/holodeck-server.log 2>&1 &
    echo $! > /tmp/holodeck-server.pid
    sleep 2
    if kill -0 $(cat /tmp/holodeck-server.pid) 2>/dev/null; then
        echo "  MUD started (PID $(cat /tmp/holodeck-server.pid))"
    else
        echo "  MUD FAILED — check /tmp/holodeck-server.log"
    fi
fi

# 3. Start C Holodeck Server (port 7778)
echo ""
echo "[3/3] Starting C Holodeck on :7778..."
if [ -f /tmp/holodeck-c.pid ] && kill -0 $(cat /tmp/holodeck-c.pid) 2>/dev/null; then
    echo "  C server already running (PID $(cat /tmp/holodeck-c.pid))"
else
    cd /tmp/holodeck-c
    if [ -f ./holodeck ]; then
        nohup ./holodeck > /tmp/holodeck-c.log 2>&1 &
        echo $! > /tmp/holodeck-c.pid
        sleep 1
        echo "  C server started (PID $(cat /tmp/holodeck-c.pid))"
    else
        echo "  C server not built — run 'make' in /tmp/holodeck-c"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  Fleet Server Status"
echo "═══════════════════════════════════════════════"
echo "  Keeper:  http://127.0.0.1:8900/health"
echo "  MUD:     telnet://127.0.0.1:7777"
echo "  C MUD:   telnet://127.0.0.1:7778"
echo ""

# Health check
curl -s http://127.0.0.1:8900/health 2>/dev/null | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print(f'  Keeper: {d[\"status\"]} (v{d[\"version\"]}, {d[\"agents\"]} agents)')
except:
    print('  Keeper: not responding')
" 2>/dev/null || echo "  Keeper: not responding"
