#!/bin/bash
# Zeroclaw Loop — persistent agent research loop
# Runs zc_tick_v4.py every 5 minutes
# Survives reboots — all paths are in workspace

WORKSPACE="/home/ubuntu/.openclaw/workspace"
SCRIPT="$WORKSPACE/scripts/zc_tick_v4.py"
LOG="$WORKSPACE/data/zeroclaw/loop.log"

mkdir -p "$WORKSPACE/data/zeroclaw/logs"

source ~/.credentials_vault 2>/dev/null

while true; do
    python3 "$SCRIPT" >> "$LOG" 2>&1
    sleep 28800
done
