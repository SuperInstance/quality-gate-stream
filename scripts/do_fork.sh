#!/bin/bash
# Wrapper: wait for rate limit reset, then fork
echo "Waiting 120s for GitHub rate limit to reset..."
sleep 120
python3 /home/ubuntu/.openclaw/workspace/scripts/fork_lucineer.py
