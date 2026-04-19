#!/bin/bash
# Night shift automation — runs while Casey sleeps
export PYTHONUNBUFFERED=1

while true; do
    HOUR=$(date -u +%H)
    MINUTE=$(date -u +%M)
    
    # Every 30 min: synergy detection
    if [ "$(( MINUTE % 30 ))" = "0" ]; then
        echo "[$(date -u +%H:%M)] 🔗 Synergy detection"
        python3 /tmp/room_synergy.py >> /tmp/night-automation.log 2>&1
    fi
    
    # Every 60 min: room training + ensign export
    if [ "$MINUTE" = "00" ]; then
        echo "[$(date -u +%H:%M)] 🐚 Room training"
        python3 /tmp/room_trainer.py >> /tmp/night-automation.log 2>&1
    fi
    
    # Every 15 min: service guard
    if [ "$(( MINUTE % 15 ))" = "0" ]; then
        bash /home/ubuntu/.openclaw/workspace/scripts/service-guard.sh >> /tmp/service-guard.log 2>&1
    fi
    
    # Every 6 hours: fleet metrics snapshot
    if [ "$MINUTE" = "00" ] && [ "$(( HOUR % 6 ))" = "0" ]; then
        echo "[$(date -u +%H:%M)] 📊 Fleet metrics"
        python3 -c "
import json, urllib.request
from datetime import datetime
data = json.loads(urllib.request.urlopen('http://localhost:8847/status', timeout=5).read())
snapshot = {'timestamp': datetime.utcnow().isoformat(), 'total_tiles': data['total_tiles'], 'rooms': data['rooms'], 'gate': data['gate_stats']}
print(json.dumps(snapshot, indent=2))
" >> /tmp/fleet-metrics.jsonl
    fi
    
    sleep 60
done
