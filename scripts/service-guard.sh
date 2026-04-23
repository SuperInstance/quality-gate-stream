#!/bin/bash
# service-guard.sh v2 — All services from fleet/services/
WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG="$WORKSPACE/data/service-guard.log"
FLEET="$WORKSPACE/fleet/services"
mkdir -p "$WORKSPACE/data"

# Service name:port:script mapping
SERVICES=(
  "keeper:8900:keeper.py"
  "agent-api:8901:agent_api.py"
  "mud:7777:mud_telnet.py"
  "plato:8847:plato.py"
  "crab-trap:4042:crab_trap.py"
  "the-lock:4043:the_lock.py"
  "arena:4044:arena.py"
  "grammar:4045:grammar.py"
  "dashboard:4046:dashboard.py"
  "nexus:4047:nexus.py"
  "shell:8848:shell.py"
  "orchestrator:8849:orchestrator.py"
  "adaptive-mud:8850:adaptive_mud.py"
  "pp-monitor:8851:pp_monitor.py"
  "tile-scorer:8852:tile_scorer.py"
  "domain-rooms:4050:domain_rooms.py"
  "fleet-runner:8899:fleet_runner.py"
  "web-terminal:4060:web_terminal.py"
  "grammar-compactor:4055:grammar_compactor.py"
  "rate-attention:4056:rate_attention.py"
  "skill-forge:4057:skill_forge.py"
)

check_port() {
  nc -z -w 2 localhost "$1" 2>/dev/null
}

restart() {
  local name=$1 port=$2 script=$3
  local full="$FLEET/$script"
  if [ ! -f "$full" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] MISSING $name:$port ($full)" >> "$LOG"
    return
  fi
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RESTART $name:$port" >> "$LOG"
  # Kill old process on this port
  fuser -k "$port/tcp" 2>/dev/null
  sleep 1
  # Start with env vars
  GROQ_API_KEY="${GROQ_API_KEY:-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}" \
  DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-sk-f742b70fc40849eda4181afcf3d68b0c}" \
  DEEPINFRA_API_KEY="${DEEPINFRA_API_KEY:-RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ}" \
  nohup python3 "$full" > "/tmp/${name}.log" 2>&1 &
  sleep 2
  if check_port "$port"; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RECOVERED $name:$port" >> "$LOG"
  else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] FAILED $name:$port" >> "$LOG"
  fi
}

# Check disk
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_PCT" -gt 90 ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] P0 DISK $DISK_PCT%" >> "$LOG"
  rm -rf /home/ubuntu/.cache/pip /home/ubuntu/.cache/uv 2>/dev/null
fi

# Check each service
for entry in "${SERVICES[@]}"; do
  IFS=: read -r name port script <<< "$entry"
  if ! check_port "$port"; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DOWN $name:$port" >> "$LOG"
    restart "$name" "$port" "$script"
  fi
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] OK — all services checked" >> "$LOG"

# Check zeroclaw loop
if ! pgrep -f "zc_loop" > /dev/null; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DOWN zeroclaw-loop" >> "$LOG"
  nohup bash "$WORKSPACE/scripts/zc_loop.sh" > /dev/null 2>&1 &
fi

# Task Queue (port 4058)
SERVICES+=("task-queue:4058:task_queue.py")

# Crab Trap Portal (port 4059)
SERVICES+=("crab-trap-portal:4059:crab_trap_portal.py")
SERVICES+=("pathfinder:4051:pathfinder.py")
SERVICES+=("librarian:4052:librarian.py")
SERVICES+=("gatekeeper:4053:gatekeeper.py")
SERVICES+=("archivist:4054:archivist.py")
SERVICES+=("conductor:4061:conductor.py")
SERVICES+=("steward:4062:steward.py")
