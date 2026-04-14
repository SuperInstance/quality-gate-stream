#!/bin/bash
# Resume fork_lucineer.py with safe throttling
# GitHub secondary rate limit on forks resets ~1hr after first hit
# First burst was ~07:10 UTC, so safe to resume ~08:10 UTC
python3 /home/ubuntu/.openclaw/workspace/scripts/fork_lucineer.py >> /home/ubuntu/.openclaw/workspace/scripts/output/fork_log.txt 2>&1
echo "Fork job completed at $(date)" >> /home/ubuntu/.openclaw/workspace/scripts/output/fork_log.txt
