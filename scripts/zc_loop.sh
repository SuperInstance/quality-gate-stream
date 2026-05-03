#!/bin/bash
# Zeroclaw Loop — 3x daily via ~/.credentials_vault
WORKSPACE="/home/ubuntu/.openclaw/workspace"
SCRIPT="$WORKSPACE/scripts/zc_tick_v4.py"
LOG="$WORKSPACE/data/zeroclaw/loop.log"

source ~/.credentials_vault 2>/dev/null
export GROQ_API_KEY

mkdir -p "$WORKSPACE/data/zeroclaw/logs"

while true; do
    python3 "$SCRIPT" >> "$LOG" 2>&1
    sleep 28800
done
