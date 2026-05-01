#!/usr/bin/env python3
"""Zeroclaw Tick v3 — Submits tiles to local PLATO room server."""
import sys, os, json, time, subprocess, re
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

DEEPSEEK_KEY = "[DEEPSEEK_KEY_REDACTED]"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
GITHUB_TOKEN = "[GITHUB_TOKEN_REVOKED]"
PLATO_URL = "http://localhost:8847"
SHELLS_DIR = Path("/tmp/zeroclaw-shells")
FLEET_KB = SHELLS_DIR / "fleet-knowledge"

def call_deepseek(system_prompt, user_prompt, max_tokens=2000):
    body = json.dumps({
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }).encode()
    req = urllib.request.Request(DEEPSEEK_URL, data=body,
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=90)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "[ERROR] " + str(e)

def submit_tile(tile):
    """Submit a tile to the PLATO room server."""
    try:
        body = json.dumps(tile).encode()
        req = urllib.request.Request(PLATO_URL + "/submit",
            data=body, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def shell_git(shell_path, *args):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "oracle1-keeper"
    env["GIT_AUTHOR_EMAIL"] = "oracle1@cocapn.ai"
    env["GIT_COMMITTER_NAME"] = "oracle1-keeper"
    env["GIT_COMMITTER_EMAIL"] = "oracle1@cocapn.ai"
    r = subprocess.run(["git"] + list(args), cwd=str(shell_path), capture_output=True, text=True, env=env, timeout=30)
    return r.stdout + r.stderr

def read_file(path, max_chars=2000):
    try:
        return Path(path).read_text()[:max_chars]
    except:
        return "[Could not read]"

DOMAIN_MAP = {
    "Navigator": "codearchaeology",
    "Sentinel": "fleethealth",
    "Scribe": "documentation",
    "Tinker": "prototyping",
    "Scout": "trendanalysis",
    "Curator": "organization",
    "Mason": "testing",
    "Alchemist": "modelexperiment",
    "Herald": "communication",
    "Scholar": "research",
    "Weaver": "integration",
    "Archivist": "memory",
}

AGENTS = [
    {"name": "Navigator", "emoji": "🧭", "shell": "zc-navigator-shell",
     "role": "Code archaeologist. Digs through fleet repos for patterns and bugs.",
     "read_files": ["fleet-knowledge/docs/PROJECT-VISION.md", "fleet-knowledge/docs/DEADBAND-PROTOCOL.md"]},
    {"name": "Sentinel", "emoji": "🛡️", "shell": "zc-sentinel-shell",
     "role": "Fleet health monitor. Watches services, tracks uptime.",
     "read_files": ["fleet-knowledge/MEMORY.md"]},
    {"name": "Scribe", "emoji": "📝", "shell": "zc-scribe-shell",
     "role": "Documentation specialist. Writes READMEs, updates wikis.",
     "read_files": ["fleet-knowledge/docs/PROJECT-VISION.md"]},
    {"name": "Tinker", "emoji": "🔧", "shell": "zc-tinker-shell",
     "role": "Experimental coder. Quick prototypes, proof-of-concepts.",
     "read_files": ["fleet-knowledge/narrow-games/constraint_sim_final.json", "fleet-knowledge/docs/DEADBAND-PROTOCOL.md"]},
    {"name": "Scout", "emoji": "🔭", "shell": "zc-scout-shell",
     "role": "Trend spotter. Watches GitHub trending, new tech.",
     "read_files": ["fleet-knowledge/FLEET-CONTEXT.md"]},
    {"name": "Curator", "emoji": "🏛️", "shell": "zc-curator-shell",
     "role": "Repo organizer. Categorizes and tags fleet repos.",
     "read_files": ["fleet-knowledge/MEMORY.md"]},
    {"name": "Mason", "emoji": "🧱", "shell": "zc-mason-shell",
     "role": "Test builder. Writes tests for fleet code.",
     "read_files": ["fleet-knowledge/FLEET-CONTEXT.md"]},
    {"name": "Alchemist", "emoji": "⚗️", "shell": "zc-alchemist-shell",
     "role": "Model experimenter. Tests different models and prompts.",
     "read_files": ["fleet-knowledge/FLEET-CONTEXT.md"]},
    {"name": "Herald", "emoji": "📯", "shell": "zc-herald-shell",
     "role": "Fleet communicator. Manages bottles and sync.",
     "read_files": ["fleet-knowledge/MEMORY.md"]},
    {"name": "Scholar", "emoji": "📖", "shell": "zc-scholar-shell",
     "role": "Research synthesizer. Reads papers, summarizes findings.",
     "read_files": ["fleet-knowledge/docs/DEADBAND-PROTOCOL.md", "fleet-knowledge/docs/PROJECT-VISION.md"]},
    {"name": "Weaver", "emoji": "🕸️", "shell": "zc-weaver-shell",
     "role": "Integration specialist. Wires components together.",
     "read_files": ["fleet-knowledge/FLEET-CONTEXT.md"]},
    {"name": "Archivist", "emoji": "📚", "shell": "zc-archivist-shell",
     "role": "Memory keeper. Manages fleet history and logs.",
     "read_files": ["fleet-knowledge/MEMORY.md"]},
]

print("🦀 ZEROCLOW TICK v3 — " + datetime.now(timezone.utc).isoformat()[:19])
print("🐚 PLATO Server: " + PLATO_URL)
print()

tiles_submitted = 0
tiles_accepted = 0
tiles_rejected = 0

for agent in AGENTS:
    name = agent["name"]
    emoji = agent["emoji"]
    shell_path = SHELLS_DIR / agent["shell"]
    domain = DOMAIN_MAP.get(name, "general")
    
    if not shell_path.exists():
        print("  ⏭️ " + emoji + " " + name + ": shell not found")
        continue
    
    shell_git(shell_path, "pull", "--rebase")
    
    state = read_file(shell_path / "STATE.md")
    tasks = read_file(shell_path / "TASK-BOARD.md")
    
    cycle = 0
    for line in state.split("\n"):
        if "## Cycle:" in line:
            try: cycle = int(line.split(":")[1].strip())
            except: pass
    cycle += 1
    
    recent = ""
    work_dir = shell_path / "work"
    if work_dir.exists():
        for f in sorted(work_dir.glob("*.md"))[-2:]:
            recent += "\n--- " + f.name + " ---\n" + f.read_text()[:400] + "\n"
    
    fleet_context = read_file(SHELLS_DIR / "fleet-knowledge" / "FLEET-CONTEXT.md")
    real_files = ""
    for rf in agent.get("read_files", []):
        real_files += "\n--- " + rf + " ---\n" + read_file(SHELLS_DIR / rf, 1500) + "\n"
    
    bootcamp = read_file(SHELLS_DIR / "fleet-knowledge" / "BOOTCAMP.md")
    
    system = "You are " + name + " (" + emoji + "). " + agent["role"] + "\n\n" + fleet_context + "\n\nYou are a hermit crab agent in the Cocapn fleet. Your git repo IS your shell. Your work output becomes training tiles submitted to a PLATO room server. You are a zero-trust contributor — the server validates your tiles. Avoid absolute claims (always, never, guaranteed). Be factual and specific. Write real, useful output based on the files provided. Fleet doctrine: P0 don't hit rocks, P1 find safe channels, P2 optimize."
    
    user = "## Fleet Knowledge (REAL FILES)\n" + real_files + "\n\n## Boot Camp\n" + bootcamp + "\n\n## My State (Cycle " + str(cycle) + ")\n" + state[:600] + "\n\n## My Tasks\n" + tasks[:500] + "\n\n## Recent Work\n" + (recent[:300] if recent else "(none)") + "\n\nPhase " + str(min((cycle // 5) + 1, 4)) + " of boot camp. Do your task. Write output. Be factual — avoid words like 'always', 'never', 'guaranteed'. GO."
    
    response = call_deepseek(system, user)
    
    if response.startswith("[ERROR]"):
        print("  ❌ " + emoji + " " + name + ": " + response[:80])
        continue
    
    work_dir.mkdir(exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    (work_dir / (now_str + "_cycle" + str(cycle) + ".md")).write_text("# Cycle " + str(cycle) + "\n\n" + response)
    
    file_blocks = re.findall(r'```(\w+\.\w+)\n(.*?)```', response, re.DOTALL)
    for fname, fcontent in file_blocks:
        fname = fname.split('/')[-1]
        if len(fname) > 50 or len(fname) < 3:
            continue
        (work_dir / fname).write_text(fcontent)
    
    # SUBMIT TILES TO PLATO SERVER
    # Extract Q&A pairs from response for tile submission
    sections = re.split(r'\n## ', response)
    agent_tiles_submitted = 0
    agent_tiles_accepted = 0
    for section in sections:
        lines = section.strip().split('\n')
        if len(lines) < 3:
            continue
        question = lines[0].strip().lstrip('#').strip()
        answer = '\n'.join(lines[1:]).strip()
        if len(question) < 10 or len(answer) < 20:
            continue
        
        tile = {
            "domain": domain,
            "question": question[:200],
            "answer": answer[:3000],
            "tags": [name.lower(), domain, "zeroclaw", "cycle" + str(cycle)],
            "confidence": 0.5,
            "source": "zeroclaw:" + name + ":cycle" + str(cycle),
        }
        result = submit_tile(tile)
        agent_tiles_submitted += 1
        if result.get("status") == "accepted":
            agent_tiles_accepted += 1
            tiles_accepted += 1
        else:
            tiles_rejected += 1
        tiles_submitted += 1
    
    response_short = response[:200].replace("\n", " ")
    new_state = "# State — " + name + "\n\n## Status: ACTIVE\n## Cycle: " + str(cycle) + "\n## Phase: " + str(min((cycle // 5) + 1, 4)) + "\n## Tiles Submitted: " + str(agent_tiles_submitted) + "\n## Tiles Accepted: " + str(agent_tiles_accepted) + "\n## Last Action: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n\n## Last Thought\n" + response_short + "\n\n## Memory\n"
    if "## Memory" in state:
        mem = state.split("## Memory")[1][:800]
        new_state += mem
    
    (shell_path / "STATE.md").write_text(new_state)
    
    shell_git(shell_path, "add", "-A")
    commit_line = response[:50].replace("\n", " ")
    shell_git(shell_path, "commit", "-m", "Cycle " + str(cycle) + ": " + commit_line)
    shell_git(shell_path, "push")
    
    tile_info = " 🐚" + str(agent_tiles_accepted) + "/" + str(agent_tiles_submitted) + " tiles"
    print("  ✅ " + emoji + " " + name + " (c" + str(cycle) + tile_info + "): " + response_short[:50])

print("\n🐚 PLATO tiles: " + str(tiles_accepted) + " accepted / " + str(tiles_rejected) + " rejected / " + str(tiles_submitted) + " submitted")
print("🦀 Tick complete.")
