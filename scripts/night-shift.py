#!/usr/bin/env python3
"""
Oracle1 Night Shift Worker — runs all night while Casey sleeps.
Logs to /tmp/night-shift.log
"""
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

LOG = "/tmp/night-shift.log"
WORKSPACE = "/home/ubuntu/.openclaw/workspace"
SCRIPTS = f"{WORKSPACE}/scripts"
SERVICES = {
    4042: "crab-trap-mud.py",
    4043: "the-lock.py",
    4044: "self-play-arena.py",
    4045: "recursive-grammar.py",
    4046: "fleet-dashboard.py",
    4047: "federated-nexus.py",
    4050: "domain-rooms.py",
    4060: "plato-web-terminal.py",
    6167: "matrix",
    7777: "mud-telnet-server.py",
    8847: "plato-room-server.py",
    8848: "plato-shell.py",
    8849: "fleet-orchestrator.py",
    8850: "adaptive-mud.py",
    8851: "purplepincher-monitor.py",
    8852: "tile-quality-scorer.py",
    8900: "keeper.py",
    8901: "agent-api.py",
}
PLATO_URL = "http://127.0.0.1:8847"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def check_services():
    """Check all 18 services, restart any that are down."""
    result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    listening = result.stdout
    down = []
    for port, name in SERVICES.items():
        if f":{port} " not in listening:
            down.append((port, name))
    
    if down:
        log(f"⚠️ {len(down)} services down: {', '.join(f'{p}({n})' for p,n in down)}")
        for port, script in down:
            if script == "matrix":
                continue  # Conduwuit managed separately
            log(f"  Restarting {script} on :{port}")
            subprocess.Popen(
                ["python3", f"{SCRIPTS}/{script}"],
                stdout=open(f"/tmp/{script.replace('.py','')}.log", "a"),
                stderr=subprocess.STDOUT,
                cwd=WORKSPACE
            )
            time.sleep(1)
    else:
        log("✅ All 18 services up")
    return len(down)

def get_plato_stats():
    """Get current PLATO tile count."""
    try:
        req = urllib.request.Request(f"{PLATO_URL}/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            tiles = data.get("total_tiles", 0)
            # Get room count from /rooms endpoint
            try:
                req2 = urllib.request.Request(f"{PLATO_URL}/rooms")
                with urllib.request.urlopen(req2, timeout=5) as resp2:
                    rooms_data = json.loads(resp2.read())
                    rooms = len(rooms_data) if isinstance(rooms_data, list) else rooms_data.get("total", 0)
            except:
                rooms = 0
            return rooms, tiles
    except:
        return 0, 0

def check_agent_repos():
    """Check FM/JC1/CCC repos for new commits."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return
    
    agents = [
        ("FM", "SuperInstance/forgemaster"),
        ("JC1", "Lucineer/capitaine"),
        ("CCC", "cocapn/cocapn"),
    ]
    
    for name, repo in agents:
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/commits?per_page=1",
                headers={
                    "Authorization": f"token {token}",
                    "User-Agent": "oracle1-night/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                commits = json.loads(resp.read())
                if commits:
                    msg = commits[0]["commit"]["message"].split("\n")[0][:70]
                    date = commits[0]["commit"]["committer"]["date"][:16]
                    log(f"  {name}: {date} — {msg}")
        except Exception as e:
            log(f"  {name}: check failed — {e}")

def run_tile_quality():
    """Score tiles and log results."""
    try:
        req = urllib.request.Request("http://127.0.0.1:8852/score/all")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            avg = data.get("average_score", 0)
            count = data.get("scored", 0)
            log(f"  Tile quality: {count} scored, avg {avg:.2f}")
    except Exception as e:
        log(f"  Tile quality check failed: {e}")

def run_grammar_evolution():
    """Trigger grammar engine evolution cycle."""
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:4045/evolve",
            data=json.dumps({"force": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            rules = data.get("total_rules", 0)
            evolved = data.get("evolved", 0)
            log(f"  Grammar: {rules} rules, {evolved} evolved this cycle")
    except Exception as e:
        log(f"  Grammar evolution: {e}")

def git_push():
    """Push any uncommitted workspace changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    if result.stdout.strip():
        count = len(result.stdout.strip().split("\n"))
        log(f"  Git: {count} uncommitted changes, pushing...")
        subprocess.run(["git", "add", "-A"], cwd=WORKSPACE, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"[night-shift] {count} files"],
            cwd=WORKSPACE, capture_output=True
        )
        subprocess.run(["git", "push"], cwd=WORKSPACE, capture_output=True)
        log(f"  Git: pushed")
    else:
        log(f"  Git: clean")

def run_arena_round():
    """Run a self-play arena round with cheap models."""
    try:
        # Use Groq (fast + cheap) for arena round
        agents = ["NightOwl-1", "NightOwl-2", "NightOwl-3"]
        for agent in agents:
            req = urllib.request.Request(
                f"http://127.0.0.1:4044/enter?agent={agent}&model=groq-llama"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        
        req = urllib.request.Request(
            "http://127.0.0.1:4044/round",
            data=json.dumps({"strategy": "socratic"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            log(f"  Arena: round completed, {data.get('results_count',0)} results")
    except Exception as e:
        log(f"  Arena round: {e}")

def generate_night_tiles():
    """Generate knowledge tiles using cheap model."""
    domains = ["philosophy", "fleet-ops", "reasoning", "architecture", "edge-computing"]
    try:
        import random
        domain = random.choice(domains)
        req = urllib.request.Request(
            f"http://127.0.0.1:4043/start",
            data=json.dumps({
                "agent": f"night-shift-{int(time.time())}",
                "domain": domain,
                "rounds": 3,
                "strategy": "socratic"
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            tiles = data.get("tiles_generated", 0)
            log(f"  Lock ({domain}): {tiles} tiles generated")
    except Exception as e:
        log(f"  Night tiles: {e}")

def refactoring_step():
    """Continue four-layer migration — one service per cycle."""
    # Check what's been migrated already
    migrated = os.path.exists(f"{WORKSPACE}/fleet/services")
    if not migrated:
        os.makedirs(f"{WORKSPACE}/fleet/services", exist_ok=True)
    
    # List source services not yet migrated
    source_dir = f"{WORKSPACE}/scripts"
    target_dir = f"{WORKSPACE}/fleet/services"
    
    sources = [f for f in os.listdir(source_dir) 
               if f.endswith(".py") and not os.path.exists(f"{target_dir}/{f}")]
    
    if not sources:
        log("  Refactor: all services have wrappers")
        return
    
    # Pick the next one and create a thin wrapper
    next_service = sources[0]
    log(f"  Refactor: creating wrapper for {next_service}")
    
    wrapper = f'''"""Migrated {next_service} — four-layer architecture."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# TODO: Decompose inline logic into vessel/equipment/agent/skills layers
# For now, import and run the original service
exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "{next_service}")).read())
'''
    with open(f"{target_dir}/{next_service}", "w") as f:
        f.write(wrapper)
    log(f"  Refactor: wrapper created for {next_service}")


def main():
    log("🌙 Night shift started")
    log(f"   Working directory: {WORKSPACE}")
    
    cycle = 0
    while True:
        cycle += 1
        now = datetime.now(timezone.utc)
        
        # Stop at 14:00 UTC (Casey likely awake by then)
        if now.hour >= 14:
            log("☀️ Night shift ending — approaching Casey's wake time")
            break
        
        log(f"\n{'='*50}")
        log(f"Cycle {cycle} — {now.strftime('%H:%M UTC')}")
        log(f"{'='*50}")
        
        # 1. Service health check
        down = check_services()
        
        # 2. PLATO stats
        rooms, tiles = get_plato_stats()
        log(f"  PLATO: {rooms} rooms, {tiles} tiles")
        
        # 3. Agent repo check (every 3 cycles)
        if cycle % 3 == 0:
            log("  Agent repos:")
            check_agent_repos()
        
        # 4. Tile quality scoring (every 4 cycles)
        if cycle % 4 == 0:
            run_tile_quality()
        
        # 5. Grammar evolution (every 5 cycles)
        if cycle % 5 == 0:
            run_grammar_evolution()
        
        # 6. Arena round (every 3 cycles)
        if cycle % 3 == 0:
            run_arena_round()
        
        # 7. Night tile generation (every 2 cycles)
        if cycle % 2 == 0:
            generate_night_tiles()
        
        # 8. Refactoring step (every cycle)
        refactoring_step()
        
        # 9. Git push (every cycle)
        git_push()
        
        # Sleep 30 minutes between cycles
        log(f"  Sleeping 30 min (next cycle ~{(now.hour + 0 if now.minute + 30 < 60 else now.hour + 1):02d}:{(now.minute + 30) % 60:02d} UTC)")
        time.sleep(1800)
    
    log("🌙 Night shift complete")

if __name__ == "__main__":
    main()

# NOTE: PLATO /status returns total_tiles but not total_rooms in top-level
# Use /rooms to get room count
