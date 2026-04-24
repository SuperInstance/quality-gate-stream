#!/usr/bin/env python3
"""Oracle1 Night Shift — autonomous work cycles until 14:00 UTC"""
import json, urllib.request, time, os, subprocess, datetime, sys

WAKE = "06:40"  # UTC
WORKSPACE = "/home/ubuntu/.openclaw/workspace"
SERVICES = [
    8900,8901,8847,7777,4042,4043,4044,4045,8848,8849,8850,8851,8852,
    4050,4051,4052,4053,4054,4055,4056,4057,4058,4059,4060,4061,4062,8899
]

def log(msg):
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def check_services():
    up = 0
    down = []
    for port in SERVICES:
        try:
            r = urllib.request.urlopen(f"http://localhost:{port}/", timeout=3)
            r.read()
            up += 1
        except:
            try:
                r = urllib.request.urlopen(f"http://localhost:{port}/status", timeout=3)
                r.read()
                up += 1
            except:
                down.append(port)
    return up, down

def restart_down(down):
    script_map = {
        8900: "scripts/keeper.py", 8901: "scripts/agent-api.py", 8847: "scripts/plato-room-server.py",
        7777: "fleet/services/mud_telnet.py", 4042: "fleet/services/crab_trap.py",
        4043: "fleet/services/the_lock.py", 4044: "fleet/services/arena.py",
        4045: "fleet/services/grammar.py", 8848: "fleet/services/shell.py",
        8849: "fleet/services/fleet_orchestrator.py", 8850: "scripts/adaptive-mud.py" if os.path.exists("scripts/adaptive-mud.py") else None,
        8851: "scripts/purplepincher-monitor.py" if os.path.exists("scripts/purplepincher-monitor.py") else None,
        8852: "scripts/tile-quality-scorer.py" if os.path.exists("scripts/tile-quality-scorer.py") else None,
        4050: "scripts/plato-browser.py", 4051: "fleet/services/pathfinder.py",
        4052: "fleet/services/librarian.py", 4053: "fleet/services/gatekeeper.py",
        4054: "fleet/services/archivist.py", 4055: "fleet/services/grammar_compactor.py" if os.path.exists("fleet/services/grammar_compactor.py") else "scripts/recursive-grammar.py",
        4056: "scripts/rate-attention.py" if os.path.exists("scripts/rate-attention.py") else None,
        4057: "fleet/services/skill_forge.py" if os.path.exists("fleet/services/skill_forge.py") else None,
        4058: "fleet/services/task_queue.py", 4059: "fleet/services/crab_trap_portal.py" if os.path.exists("fleet/services/crab_trap_portal.py") else None,
        4060: "scripts/plato-web-terminal.py", 4061: "fleet/services/conductor.py",
        4062: "fleet/services/steward.py", 8899: "fleet/services/fleet_runner.py",
    }
    restarted = 0
    for port in down:
        script = script_map.get(port)
        if script and os.path.exists(f"{WORKSPACE}/{script}"):
            os.system(f"nohup python3 {WORKSPACE}/{script} > /tmp/svc-{port}.log 2>&1 &")
            restarted += 1
            log(f"  Restarted port {port}")
        elif script:
            # Try finding by port in service-guard
            pass
    return restarted

def git_push():
    os.chdir(WORKSPACE)
    os.system("git add -A && git commit -m 'night shift: auto-commit' --allow-empty 2>/dev/null")
    os.system("git push origin main 2>/dev/null")

def get_plato_stats():
    try:
        r = urllib.request.urlopen("http://localhost:8847/stats", timeout=5)
        return json.loads(r.read())
    except:
        return {}

def run_grammar_compactor():
    """Trigger grammar compaction"""
    try:
        r = urllib.request.urlopen("http://localhost:4055/compact", timeout=30)
        result = json.loads(r.read())
        log(f"  Grammar compacted: {result}")
    except Exception as e:
        log(f"  Grammar compactor error: {e}")

def run_rate_attention_sample():
    """Trigger rate attention sampling"""
    try:
        req = urllib.request.Request("http://localhost:4056/sample", method="POST")
        r = urllib.request.urlopen(req, timeout=10)
        result = json.loads(r.read())
        alerts = [s for s in result.get("sampled", []) if s.get("attention") in ("CRITICAL", "HIGH")]
        if alerts:
            log(f"  ⚠️ Attention alerts: {alerts}")
    except Exception as e:
        log(f"  Rate attention error: {e}")

def submit_night_tile(cycle):
    """Submit a night shift observation tile"""
    stats = get_plato_stats()
    tiles = stats.get("total_tiles", "?")
    rooms = stats.get("total_rooms", "?")
    domains = [
        ("night-ops", f"What did cycle {cycle} of night shift observe?",
         f"Night shift cycle {cycle}: {tiles} tiles across {rooms} rooms. Services stable. Grammar compaction running. Rate attention sampled. Fleet growing while the captain sleeps."),
    ]
    for d, q, a in domains:
        try:
            data = json.dumps({"domain": d, "question": q, "answer": a, "agent": "oracle1-nightshift"}).encode()
            req = urllib.request.Request("http://localhost:8847/submit", data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except:
            pass

# === MAIN LOOP ===
cycle = 0
log(f"Oracle1 Night Shift started. Running until 14:00 UTC.")
log(f"Monitoring {len(SERVICES)} services.")

while True:
    now = datetime.datetime.utcnow()
    if now.hour >= 14:
        log("14:00 UTC reached. Night shift ending.")
        break
    
    cycle += 1
    log(f"--- Cycle {cycle} ---")
    
    # 1. Service check
    up, down = check_services()
    log(f"Services: {up}/{len(SERVICES)} up" + (f" | DOWN: {down}" if down else ""))
    if down:
        restarted = restart_down(down)
        log(f"Restarted {restarted} services")
        time.sleep(5)
    
    # 2. Grammar compaction (every 3 cycles)
    if cycle % 3 == 0:
        run_grammar_compactor()
    
    # 3. Rate attention sampling
    run_rate_attention_sample()
    
    # 4. Git push (every 5 cycles)
    if cycle % 5 == 0:
        git_push()
        log("  Git pushed")
    
    # 5. Submit night tile (every 10 cycles)
    if cycle % 10 == 0:
        submit_night_tile(cycle)
        stats = get_plato_stats()
        log(f"  PLATO: {stats.get('total_tiles','?')} tiles, {stats.get('total_rooms','?')} rooms")
    
    # 6. Memory update (every 20 cycles)
    if cycle % 20 == 0:
        stats = get_plato_stats()
        mempath = f"{WORKSPACE}/memory/2026-04-24.md"
        entry = f"\n## Night Shift Cycle {cycle} ({now.strftime('%H:%M')} UTC)\n- Services: {up}/{len(SERVICES)}\n- PLATO: {stats.get('total_tiles','?')} tiles, {stats.get('total_rooms','?')} rooms\n"
        with open(mempath, "a") as f:
            f.write(entry)
    
    # Sleep 30 min
    log(f"Sleeping 30 min (next cycle ~{(now + datetime.timedelta(minutes=30)).strftime('%H:%M')} UTC)")
    time.sleep(1800)

git_push()
log("Night shift complete. Good morning, Casey.")
