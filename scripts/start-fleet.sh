#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
# Cocapn Fleet — Start All Services
# Usage: bash scripts/start-fleet.sh [--check] [--stop]
# ═══════════════════════════════════════════════════════

set -e
WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
cd "$WORKSPACE"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[FLEET]${NC} $1"; }
warn() { echo -e "${YELLOW}[FLEET]${NC} $1"; }
fail() { echo -e "${RED}[FLEET]${NC} $1"; }

# ── Check Mode ──────────────────────────────────────
if [ "$1" = "--stop" ]; then
    log "Stopping all fleet services..."
    for pidfile in /tmp/fleet-*.pid; do
        [ -f "$pidfile" ] && kill "$(cat "$pidfile")" 2>/dev/null && warn "Stopped $(basename "$pidfile" .pid)"
    done
    log "All services stopped."
    exit 0
fi

# ── Health Check Mode ───────────────────────────────
check_port() {
    local port=$1 name=$2
    if ss -tlnp | grep -q ":$port "; then
        echo -e "  ${GREEN}✅${NC} $name (:$port)"
        return 0
    else
        echo -e "  ${RED}❌${NC} $name (:$port)"
        return 1
    fi
}

if [ "$1" = "--check" ]; then
    log "Fleet status:"
    check_port 8847 "PLATO Room Server"
    check_port 8900 "Keeper"
    check_port 8901 "Agent API"
    check_port 7777 "MUD Telnet"
    check_port 4042 "Crab Trap"
    check_port 4043 "The Lock"
    check_port 4044 "Self-Play Arena"
    check_port 4045 "Recursive Grammar"
    check_port 6167 "Matrix (Conduwuit)"
    
    echo ""
    log "Zeroclaw loop: $(ps aux | grep zc_loop | grep -v grep | wc -l) running"
    log "PLATO tiles: $(curl -s http://localhost:8847/status 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin)["total_tiles"])' 2>/dev/null || echo 'N/A')"
    exit 0
fi

# ── Start Services ──────────────────────────────────
log "Starting Cocapn Fleet..."
log "Workspace: $WORKSPACE"

mkdir -p "$WORKSPACE/data"

# Start in dependency order
start_service() {
    local name=$1 port=$2 script=$3 log=$4
    if ss -tlnp | grep -q ":$port "; then
        warn "$name already running on :$port"
        return 0
    fi
    
    log "Starting $name..."
    nohup python3 "$WORKSPACE/scripts/$script" > "$WORKSPACE/data/$log" 2>&1 &
    local pid=$!
    echo "$pid" > "/tmp/fleet-${name}.pid"
    
    # Wait for port to open (max 10s)
    local i=0
    while [ $i -lt 10 ] && ! ss -tlnp | grep -q ":$port "; do
        sleep 1
        i=$((i + 1))
    done
    
    if ss -tlnp | grep -q ":$port "; then
        log "  ✅ $name started (PID $pid, :$port)"
        return 0
    else
        fail "  ❌ $name failed to start (check data/$log)"
        return 1
    fi
}

start_service "plato"     8847 "plato-room-server.py" "plato.log"
start_service "keeper"    8900 "keeper.py"            "keeper.log"
start_service "agent-api" 8901 "agent-api.py"         "agent-api.log"
start_service "mud"       7777 "mud-telnet-server.py" "mud.log"
start_service "crabtrap"  4042 "crab-trap-mud.py"     "crab-trap.log"
start_service "thelock"   4043 "the-lock.py"          "the-lock.log"
start_service "arena"     4044 "self-play-arena.py"   "self-play-arena.log"
start_service "grammar"   4045 "recursive-grammar.py" "recursive-grammar.log"

# Zeroclaw loop (optional)
if [ -f "$WORKSPACE/scripts/zc_loop.sh" ] && ! ps aux | grep -q "[z]c_loop"; then
    log "Starting Zeroclaw loop..."
    nohup bash "$WORKSPACE/scripts/zc_loop.sh" > /tmp/zeroclaw-loop.log 2>&1 &
    log "  ✅ Zeroclaw started"
fi

echo ""
log "═══════════════════════════════════"
log "Cocapn Fleet is running."
log "  PLATO tiles:  http://localhost:8847/status"
log "  Crab Trap:    http://localhost:4042/connect"
log "  The Lock:     http://localhost:4043/start"
log "  Arena:        http://localhost:4044/"
log "  Grammar:      http://localhost:4045/"
log "  MUD:          telnet localhost 7777"
log ""
log "Commands:"
log "  Check status:  bash scripts/start-fleet.sh --check"
log "  Stop all:      bash scripts/start-fleet.sh --stop"
log "  Curriculum:    python3 scripts/curriculum-engine.py --agent X --repo URL --domain D --model deepseek"
log "  Submit tiles:  python3 scripts/submit-session.py session.md --agent X"
log "═══════════════════════════════════"
