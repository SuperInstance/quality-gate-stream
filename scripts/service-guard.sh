#!/bin/bash
# service-guard.sh — Holistic Instance Protection (PPE for Oracle1)
# "Stay where the rocks aren't. Explore edges with tools from distance."
# Monitors all 7 services, auto-restarts, logs everything.

SERVICES=(
    "keeper:8900"
    "agent-api:8901"
    "holodeck:7778"
    "seed-mcp:9438"
    "shell:8846"
    "plato-server:8847"
    "fleet-dashboard:8848"
)

LOG="/tmp/service-guard.log"
MAX_LOG_SIZE=$((10 * 1024 * 1024))  # 10MB max log

# Rotate log if too big
if [ -f "$LOG" ] && [ $(stat -f%z "$LOG" 2>/dev/null || stat -c%s "$LOG" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
    mv "$LOG" "$LOG.old"
fi

check_port() {
    nc -z -w 2 localhost "$1" 2>/dev/null
}

restart_service() {
    local name=$1
    local port=$2
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RESTART $name:$port" >> "$LOG"
    
    case $name in
        holodeck)
            pkill -f "target/release/holodeck" 2>/dev/null
            sleep 1
            cd /tmp/holodeck-rust && nohup ./target/release/holodeck --port $port >> /tmp/holodeck.log 2>&1 &
            ;;
        agent-api)
            pkill -f agent_api.py 2>/dev/null
            sleep 1
            nohup python3 /tmp/agent_api.py >> /tmp/agent-api.log 2>&1 &
            ;;
        seed-mcp)
            pkill -f seed-mcp 2>/dev/null
            sleep 1
            cd /tmp/seed-mcp-v2 && nohup node dist/index.js >> /tmp/seed-mcp.log 2>&1 &
            ;;
        shell)
            pkill -f shell_system.py 2>/dev/null
            sleep 1
            cd /tmp/fleet-sim && nohup python3 shell_system.py >> /tmp/shell.log 2>&1 &
            ;;
        plato-server)
            pkill -f plato-room-server.py 2>/dev/null
            sleep 1
            nohup python3 /tmp/plato-room-server.py >> /tmp/plato-server.log 2>&1 &
            ;;
        fleet-dashboard)
            pkill -f fleet_dashboard.py 2>/dev/null
            sleep 1
            nohup python3 /tmp/fleet_dashboard.py >> /tmp/fleet-dashboard.log 2>&1 &
            ;;
        keeper)
            pkill -f "keeper\|8900" 2>/dev/null
            sleep 1
            nohup python3 /tmp/brothers-keeper/oracle1-keeper.py >> /tmp/keeper.log 2>&1 &
            ;;
    esac
}

# Check disk space — P0 for the instance itself
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_PCT" -gt 90 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] P0 DISK $DISK_PCT% — emergency cleanup" >> "$LOG"
    # Clear caches first
    rm -rf /home/ubuntu/.cache/pip /home/ubuntu/.cache/uv 2>/dev/null
    # Clear old logs
    find /tmp -name "*.log" -size +50M -exec truncate -s 0 {} \; 2>/dev/null
fi

# Check memory
MEM_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ "$MEM_PCT" -gt 90 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] P0 MEMORY $MEM_PCT% — killing stale processes" >> "$LOG"
    # Kill zombie python processes
    pkill -f "defunct" 2>/dev/null
fi

# Check each service
for svc in "${SERVICES[@]}"; do
    name="${svc%%:*}"
    port="${svc##*:}"
    if ! check_port "$port"; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DOWN $name:$port" >> "$LOG"
        restart_service "$name" "$port"
        sleep 3
        if check_port "$port"; then
            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RECOVERED $name:$port" >> "$LOG"
        else
            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] FAILED $name:$port — manual intervention needed" >> "$LOG"
        fi
    fi
done

# Check zeroclaw loop
if ! pgrep -f "zc_tick" > /dev/null; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DOWN zeroclaw-loop — restarting" >> "$LOG"
    nohup bash /tmp/zc_loop2.sh >> /tmp/zeroclaw-loop.log 2>&1 &
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] OK — all services checked" >> "$LOG"
