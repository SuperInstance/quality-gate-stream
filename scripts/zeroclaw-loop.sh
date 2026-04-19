#!/bin/bash
# Zeroclaw Persistent Loop — runs all 12 agents every 5 minutes
# Each tick: read shell → call DeepSeek → write results → push

export PYTHONUNBUFFERED=1
INTERVAL=300  # 5 minutes

while true; do
    echo "🦀 TICK $(date -u +%H:%M:%S)"
    python3 /tmp/zc_tick.py 2>&1
    echo "💤 Sleep ${INTERVAL}s"
    echo ""
    sleep $INTERVAL
done
