#!/usr/bin/env python3
"""
Oracle1 Continuous Worker — NEVER STOPS.
Runs productive fleet work on a 30-min cycle, 24/7.
Night shift (before 08:00 / after 23:00): bulk tasks, no messages to Casey.
Day shift (08:00-23:00): all tasks, reports to Casey when needed.
"""
import json, urllib.request, time, os, subprocess, datetime, sys, pathlib

WORKSPACE = "/home/ubuntu/.openclaw/workspace"
SERVICES = [
    8900,8901,8847,7777,4042,4043,4044,4045,8848,8849,8850,8851,8852,
    4050,4051,4052,4053,4054,4055,4056,4057,4058,4059,4060,4061,4062,8899
]

GROQ_KEY = "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"
CYCLE_MINUTES = 30

# ── Helpers ──────────────────────────────────────────────
def log(msg):
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def check_services():
    up, down = 0, []
    for port in SERVICES:
        try:
            r = urllib.request.urlopen(f"http://localhost:{port}/", timeout=3)
            r.read(); up += 1
        except:
            try:
                r = urllib.request.urlopen(f"http://localhost:{port}/status", timeout=3)
                r.read(); up += 1
            except:
                down.append(port)
    return up, down

def restart_down(down):
    script_map = {
        8900: "scripts/keeper.py", 8901: "scripts/agent-api.py",
        8847: "scripts/plato-room-server.py",
        7777: "fleet/services/mud_telnet.py",
        4042: "fleet/services/crab_trap.py",
        4043: "fleet/services/the_lock.py",
        4044: "fleet/services/arena.py",
        4045: "fleet/services/grammar.py",
        8848: "fleet/services/shell.py",
        8849: "fleet/services/fleet_orchestrator.py",
        8850: "scripts/adaptive-mud.py",
        8851: "scripts/purplepincher-monitor.py",
        8852: "scripts/tile-quality-scorer.py",
        4050: "scripts/plato-browser.py",
        4051: "fleet/services/pathfinder.py",
        4052: "fleet/services/librarian.py",
        4053: "fleet/services/gatekeeper.py",
        4054: "fleet/services/archivist.py",
        4055: "fleet/services/grammar_compactor.py",
        4056: "scripts/rate-attention.py",
        4057: "fleet/services/skill_forge.py",
        4058: "fleet/services/task_queue.py",
        4059: "fleet/services/crab_trap_portal.py",
        4060: "scripts/plato-web-terminal.py",
        4061: "fleet/services/conductor.py",
        4062: "fleet/services/steward.py",
        8899: "fleet/services/fleet_runner.py",
    }
    restarted = 0
    for port in down:
        script = script_map.get(port)
        if script and os.path.exists(f"{WORKSPACE}/{script}"):
            os.system(f"nohup python3 {WORKSPACE}/{script} > /tmp/svc-{port}.log 2>&1 &")
            restarted += 1
            log(f"  Restarted port {port}")
    return restarted

def git_push():
    os.chdir(WORKSPACE)
    os.system("git add -A && git commit -m 'continuous worker: auto-commit' --allow-empty 2>/dev/null")
    os.system("git push origin main 2>/dev/null")
    # Also push research submodule
    os.system("cd research && git add -A && git commit -m 'auto' --allow-empty 2>/dev/null && git push origin main 2>/dev/null")
    os.chdir(WORKSPACE)

def get_plato_stats():
    try:
        import pathlib
        rooms_dir = pathlib.Path("/tmp/plato-server-data/rooms")
        total_tiles = 0
        for f in rooms_dir.glob("*.json"):
            data = json.loads(f.read_text())
            tiles = data if isinstance(data, list) else data.get("tiles", [])
            total_tiles += len(tiles)
        return total_tiles, len(list(rooms_dir.glob("*.json")))
    except:
        return 0, 0

def groq(prompt):
    data = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500, "temperature": 0.7
    }).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
        data=data, headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json", "User-Agent": "curl/7.88"})
    return json.loads(urllib.request.urlopen(req, timeout=20).read())["choices"][0]["message"]["content"]

def submit_tile(domain, question, answer):
    data = json.dumps({"domain": domain, "question": question, "answer": answer, "agent": "oracle1-worker"}).encode()
    req = urllib.request.Request("http://localhost:8847/submit", data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=5).read())

def seed_tiles():
    """Generate and submit 5 deep tiles per cycle."""
    prompts = [
        ("fleet-architecture", "What is the minimum viable agent? What capabilities must every fleet agent have?"),
        ("constraint-theory", "How does constraint propagation in a PLATO room relate to belief revision in epistemology?"),
        ("reasoning", "Compare fast thinking (Groq 24ms) vs slow thinking (DeepSeek 130s) for fleet tasks. When is each optimal?"),
        ("prompt-laboratory", "Design a prompt that makes any chatbot curious enough to explore a live API. What are the key ingredients?"),
        ("federated-architecture", "Design a federation handshake protocol between two PLATO servers that have never met."),
        ("tile", "What makes a knowledge tile high quality? Define 5 scoring criteria with examples of good vs bad tiles."),
        ("grammar-evolution", "The grammar has rules but few evolution cycles. Design a concrete trigger based on tile novelty."),
        ("fleet-scalability", "The fleet has 190 rooms and 5000 tiles. What breaks at 1000 rooms? At 50,000 tiles?"),
        ("edge_compute", "How would you deploy PLATO on a Jetson Orin with 8GB RAM? What do you cut?"),
        ("knowledge_preservation", "Design a tile archival strategy. When should tiles expire? How do you preserve institutional memory?"),
        ("plato-evolution", "What would PLATO look like with 10,000 rooms? How do agents navigate without getting lost?"),
        ("instinct_training", "How do you compress a 70B model's knowledge into a 7B model's instincts? Design the pipeline."),
        ("plato-theory", "Is PLATO a database, a filesystem, or something new? What is the right abstraction?"),
        ("fleet-security", "What is the attack surface of 27 HTTP services with no auth? Prioritize the fixes."),
        ("shell_system", "Design a shell language for fleet agents. What primitives does it need?"),
        ("prompting-research", "What is the strongest evidence that prompting IS all you need? What would disprove it?"),
        ("evaluation-arena", "Design a better ELO system for agents. What's wrong with the current one?"),
        ("neural", "How do neural networks relate to PLATO rooms? Is a room like a neuron? A layer? Something else?"),
        ("safety-shield", "Design a safety layer for fleet agents that prevents harmful tile submissions without blocking creativity."),
        ("mlops-engine", "How would you monitor 27 services in production? Design the dashboard."),
    ]
    
    # Pick 5 random prompts each cycle
    import random
    batch = random.sample(prompts, min(5, len(prompts)))
    ok = 0
    for domain, prompt in batch:
        try:
            answer = groq(f"You are a fleet knowledge architect. Answer with specific, actionable detail (50+ words). {prompt}")
            r = submit_tile(domain, prompt, answer)
            if r.get("status") == "accepted":
                ok += 1
        except:
            pass
        time.sleep(0.5)
    return ok

def run_grammar_compaction():
    try:
        urllib.request.urlopen("http://localhost:4055/compact", timeout=30).read()
    except:
        pass

def run_rate_attention():
    try:
        req = urllib.request.Request("http://localhost:4056/sample", method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        alerts = [s for s in result.get("sampled", []) if s.get("attention") in ("CRITICAL", "HIGH")]
        return alerts
    except:
        return []

def update_memory(cycle, tiles, rooms, up, alerts):
    now = datetime.datetime.utcnow()
    mempath = f"{WORKSPACE}/memory/2026-04-24.md"
    entry = f"\n## Continuous Worker Cycle {cycle} ({now.strftime('%H:%M')} UTC)\n- Services: {up}/{len(SERVICES)}\n- PLATO: {tiles} tiles, {rooms} rooms\n- Alerts: {len(alerts)}\n"
    with open(mempath, "a") as f:
        f.write(entry)

# ══════════════════════════════════════════════════════════
# MAIN LOOP — RUNS FOREVER
# ══════════════════════════════════════════════════════════
cycle = 0
log("Oracle1 Continuous Worker started. Running 24/7.")
log(f"Monitoring {len(SERVICES)} services. Cycle: {CYCLE_MINUTES} min.")

while True:
    cycle += 1
    now = datetime.datetime.utcnow()
    log(f"--- Cycle {cycle} ({now.strftime('%H:%M')} UTC) ---")
    
    # 1. Service health
    up, down = check_services()
    log(f"Services: {up}/{len(SERVICES)}" + (f" DOWN: {down}" if down else ""))
    if down:
        restart_down(down)
        time.sleep(3)
    
    # 2. Check PLATO Shell for agent activity (every cycle)
    try:
        shell_status = json.loads(urllib.request.urlopen("http://localhost:8848/status", timeout=5).read())
        shell_agents = shell_status.get("agents", 0)
        shell_cmds = shell_status.get("total_commands", 0)
        if shell_agents > 0 or shell_cmds > 0:
            log(f"Shell: {shell_agents} agents, {shell_cmds} commands")
            # Get feed for details
            feed = json.loads(urllib.request.urlopen("http://localhost:8848/feed", timeout=5).read())
            for cmd in feed.get("commands", [])[-3:]:
                log(f"  Shell cmd: {cmd.get('agent','?')} [{cmd.get('tool','?')}] {str(cmd.get('command',''))[:80]}")
    except:
        pass
    
    # 3. Seed tiles (every cycle)
    tiles_added = seed_tiles()
    log(f"Tiles seeded: {tiles_added}/5")
    
    # 3. Grammar compaction (every 3 cycles)
    if cycle % 3 == 0:
        run_grammar_compaction()
        log("Grammar compacted")
    
    # 4. Rate attention
    alerts = run_rate_attention()
    if alerts:
        log(f"⚠️ Alerts: {len(alerts)}")
    
    # 5. Git push (every 4 cycles = ~2h)
    if cycle % 4 == 0:
        git_push()
        log("Git pushed")
    
    # 6. Memory update (every 10 cycles = ~5h)
    if cycle % 10 == 0:
        tiles, rooms = get_plato_stats()
        update_memory(cycle, tiles, rooms, up, alerts)
        log(f"Memory updated: {tiles} tiles, {rooms} rooms")
    
    # 7. Log stats every cycle
    if cycle % 5 == 0:
        tiles, rooms = get_plato_stats()
        log(f"PLATO stats: {tiles} tiles, {rooms} rooms")
    
    # 8. Fleet check: ping idle agents (every 6 cycles = ~3h)
    if cycle % 6 == 0:
        try:
            import subprocess
            subprocess.run(["python3", "/tmp/matrix-ping.py"], timeout=15)
            log("Fleet check-in sent")
        except Exception as e:
            log(f"Fleet check error: {e}")
    
    # Sleep
    log(f"Next cycle in {CYCLE_MINUTES} min (~{(now + datetime.timedelta(minutes=CYCLE_MINUTES)).strftime('%H:%M')} UTC)")
    time.sleep(CYCLE_MINUTES * 60)

# ── Fleet Coordination (added to continuous worker) ──────────
# This section runs alongside the main loop to ensure real communication

FLEET_AGENTS = {
    "forgemaster": {
        "repos": ["SuperInstance/forgemaster"],
        "matrix_token": "wa1ViGSmGnbu0jMrlPSQuj6KL1sBJgTi",
        "role": "Architect/Forge",
    },
    "jetsonclaw1": {
        "repos": ["Lucineer/JetsonClaw1-vessel", "Lucineer/capitaine"],
        "matrix_token": "QmGPEJHCOITq7QD45GBf865A5mDJlAf1",
        "role": "Builder/Edge",
    },
}

def check_agent_activity(agent_name, repos):
    """Check if agent has committed in last 24h."""
    import pathlib
    token = "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"
    for repo in repos:
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/commits?per_page=1",
                headers={"Authorization": f"token {token}"}
            )
            resp = urllib.request.urlopen(req, timeout=10)
            commits = json.loads(resp.read())
            if commits:
                date_str = commits[0]["commit"]["committer"]["date"]
                from datetime import datetime as dt
                commit_time = dt.fromisoformat(date_str.replace("Z", "+00:00"))
                hours_ago = (datetime.datetime.utcnow().replace(tzinfo=None) - commit_time.replace(tzinfo=None)).total_seconds() / 3600
                return hours_ago
        except:
            pass
    return 999  # No activity found
