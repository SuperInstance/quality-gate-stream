#!/usr/bin/env python3
"""Zeroclaw Tick v3 — File Access + Dynamic Difficulty + Ensign Injection

Upgrades from v2:
1. Reads actual fleet repo files (not just fleet-knowledge symlinks)
2. Dynamic difficulty based on gate pass rate
3. Ensign injection from refined artifacts
4. Better task rotation with history tracking
"""
import sys, os, json, time, subprocess, re, math, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import urllib.request

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-f742b70fc40849eda4181afcf3d68b0c")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "[GITHUB_TOKEN_REVOKED]")
PLATO_URL = "http://localhost:8847"
SHELLS_DIR = Path("/tmp/zeroclaw-shells")
FLEET_KB = SHELLS_DIR / "fleet-knowledge"
FLEET_REPOS = Path("/home/ubuntu/.openclaw/workspace/repos")
DIFFICULTY_FILE = Path("/tmp/zc_difficulty.json")
REFINED_DIR = Path("/tmp/refined")
TASK_HISTORY_FILE = Path("/tmp/zc_task_history.json")

# === DOMAIN MAP ===
DOMAIN_MAP = {
    "Navigator": "codearchaeology", "Sentinel": "fleethealth",
    "Scribe": "documentation", "Tinker": "prototyping",
    "Scout": "trendanalysis", "Curator": "organization",
    "Mason": "testing", "Alchemist": "modelexperiment",
    "Herald": "communication", "Scholar": "research",
    "Weaver": "integration", "Archivist": "memory",
}

# === DIFFICULTY LEVELS ===
LEVEL_TEMPLATES = {
    1: "READ PHASE: Study the provided files. Summarize what you find. List 3 key insights. Be factual.",
    2: "ANALYZE PHASE: Compare patterns across files. Identify inconsistencies, bugs, or opportunities. Cite specific code.",
    3: "BUILD PHASE: Write working code that solves a real problem in the fleet. Include tests. Be specific.",
    4: "SPECIALIST PHASE: Design an architecture for a fleet subsystem. Write spec + implementation + tests. Think deep.",
}

DIFFICULTY_THRESHOLDS = {
    "promote": {"min_rate": 0.85, "min_streak": 3},
    "demote": {"max_rate": 0.50, "max_streak": 2},
}

AGENTS = [
    {"name": "Navigator", "emoji": "🧭", "shell": "zc-navigator-shell",
     "role": "Code archaeologist. Digs through fleet repos for patterns and bugs.",
     "keywords": ["rust", "cargo", "test", "mod.rs", "lib.rs", "struct", "impl"]},
    {"name": "Sentinel", "emoji": "🛡️", "shell": "zc-sentinel-shell",
     "role": "Fleet health monitor. Watches services, tracks uptime.",
     "keywords": ["health", "monitor", "service", "uptime", "dashboard", "status"]},
    {"name": "Scribe", "emoji": "📝", "shell": "zc-scribe-shell",
     "role": "Documentation specialist. Writes READMEs, updates wikis.",
     "keywords": ["readme", "docs", "documentation", "guide", "tutorial"]},
    {"name": "Tinker", "emoji": "🔧", "shell": "zc-tinker-shell",
     "role": "Experimental coder. Quick prototypes, proof-of-concepts.",
     "keywords": ["prototype", "poc", "experiment", "demo", "example"]},
    {"name": "Scout", "emoji": "🔭", "shell": "zc-scout-shell",
     "role": "Trend spotter. Watches GitHub trending, new tech.",
     "keywords": ["trending", "new", "release", "v1", "v2", "announcement"]},
    {"name": "Curator", "emoji": "🏛️", "shell": "zc-curator-shell",
     "role": "Repo organizer. Categorizes and tags fleet repos.",
     "keywords": ["categorize", "tag", "organize", "index", "catalog"]},
    {"name": "Mason", "emoji": "🧱", "shell": "zc-mason-shell",
     "role": "Test builder. Writes tests for fleet code.",
     "keywords": ["test", "assert", "pytest", "cargo test", "unittest"]},
    {"name": "Alchemist", "emoji": "⚗️", "shell": "zc-alchemist-shell",
     "role": "Model experimenter. Tests different models and prompts.",
     "keywords": ["model", "api", "inference", "llm", "token", "prompt"]},
    {"name": "Herald", "emoji": "📯", "shell": "zc-herald-shell",
     "role": "Fleet communicator. Manages bottles and sync.",
     "keywords": ["bottle", "sync", "message", "protocol", "communication"]},
    {"name": "Scholar", "emoji": "📖", "shell": "zc-scholar-shell",
     "role": "Research synthesizer. Reads papers, summarizes findings.",
     "keywords": ["paper", "research", "arxiv", "study", "analysis"]},
    {"name": "Weaver", "emoji": "🕸️", "shell": "zc-weaver-shell",
     "role": "Integration specialist. Wires components together.",
     "keywords": ["integrate", "bridge", "connect", "wire", "pipeline"]},
    {"name": "Archivist", "emoji": "📚", "shell": "zc-archivist-shell",
     "role": "Memory keeper. Manages fleet history and logs.",
     "keywords": ["memory", "log", "history", "archive", "record"]},
]


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
    r = subprocess.run(["git"] + list(args), cwd=str(shell_path),
                       capture_output=True, text=True, env=env, timeout=30)
    return r.stdout + r.stderr


def read_file(path, max_chars=2000):
    try:
        return Path(path).read_text()[:max_chars]
    except:
        return "[Could not read]"


# === NEW: LOAD DIFFICULTY STATE ===
def load_difficulty():
    if DIFFICULTY_FILE.exists():
        try:
            return json.loads(DIFFICULTY_FILE.read_text())
        except:
            pass
    return {a["name"]: {"level": 1, "pass_rates": [], "streak_up": 0, "streak_down": 0}
            for a in AGENTS}


def save_difficulty(state):
    DIFFICULTY_FILE.write_text(json.dumps(state, indent=2))


def update_difficulty(agent_name, pass_rate, diff_state):
    d = diff_state.get(agent_name, {"level": 1, "pass_rates": [], "streak_up": 0, "streak_down": 0})
    d["pass_rates"].append(pass_rate)
    d["pass_rates"] = d["pass_rates"][-10:]  # Keep last 10

    # Check promotion
    if pass_rate >= DIFFICULTY_THRESHOLDS["promote"]["min_rate"]:
        d["streak_up"] += 1
        d["streak_down"] = 0
        if d["streak_up"] >= DIFFICULTY_THRESHOLDS["promote"]["min_streak"] and d["level"] < 4:
            d["level"] += 1
            d["streak_up"] = 0
    # Check demotion
    elif pass_rate <= DIFFICULTY_THRESHOLDS["demote"]["max_rate"]:
        d["streak_down"] += 1
        d["streak_up"] = 0
        if d["streak_down"] >= DIFFICULTY_THRESHOLDS["demote"]["max_streak"] and d["level"] > 1:
            d["level"] -= 1
            d["streak_down"] = 0
    else:
        d["streak_up"] = 0
        d["streak_down"] = 0

    diff_state[agent_name] = d
    return d["level"]


# === NEW: FIND RELEVANT FLEET REPO FILES ===
def find_relevant_files(keywords, max_files=3):
    """Search fleet repos for files matching agent keywords."""
    if not FLEET_REPOS.exists():
        return []
    matches = []
    for ext in ["*.py", "*.rs", "*.ts", "*.md"]:
        for f in FLEET_REPOS.rglob(ext):
            name_lower = f.name.lower()
            score = sum(1 for kw in keywords if kw.lower() in name_lower)
            if score > 0:
                matches.append((score, f))
            elif len(matches) < 2:
                # Also check parent dir name
                parent_lower = f.parent.name.lower()
                score2 = sum(1 for kw in keywords if kw.lower() in parent_lower)
                if score2 > 0:
                    matches.append((score2 * 0.5, f))

    matches.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    result = []
    for score, path in matches[:max_files * 2]:
        if path.name not in seen and len(result) < max_files:
            content = read_file(path, 2000)
            if content != "[Could not read]" and len(content) > 50:
                result.append((path, content))
                seen.add(path.name)
    return result


# === NEW: LOAD ENSIGN KNOWLEDGE ===
def load_ensigns(domain, max_items=3):
    """Load refined artifacts matching agent domain."""
    if not REFINED_DIR.exists():
        return []
    ensigns = []
    for f in REFINED_DIR.rglob("*.md"):
        if domain.lower() in f.name.lower() or domain.lower() in f.read_text()[:500].lower():
            content = read_file(f, 1500)
            if len(content) > 50:
                ensigns.append((f.name, content))
    return ensigns[:max_items]


# === NEW: TASK HISTORY TRACKING ===
def load_task_history():
    if TASK_HISTORY_FILE.exists():
        try:
            return json.loads(TASK_HISTORY_FILE.read_text())
        except:
            pass
    return {}


def save_task_history(history):
    TASK_HISTORY_FILE.write_text(json.dumps(history, indent=2))


# === MAIN LOOP ===
print("🦀 ZEROCLOW TICK v3 — " + datetime.now(timezone.utc).isoformat()[:19])
print("🐚 PLATO Server: " + PLATO_URL)
print("📁 Fleet repos: " + str(FLEET_REPOS))
print("📊 Dynamic difficulty: enabled")
print("🔮 Ensign injection: enabled")
print()

diff_state = load_difficulty()
task_history = load_task_history()
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
            try:
                cycle = int(line.split(":")[1].strip())
            except:
                pass
    cycle += 1

    # === DIFFICULTY ===
    level = diff_state.get(name, {}).get("level", 1)
    level_template = LEVEL_TEMPLATES.get(level, LEVEL_TEMPLATES[1])

    # === FILE ACCESS: Find relevant fleet repo files ===
    real_repo_files = find_relevant_files(agent.get("keywords", []))

    # === ENSIGN INJECTION ===
    ensigns = load_ensigns(domain)

    # Recent work
    recent = ""
    work_dir = shell_path / "work"
    if work_dir.exists():
        for f in sorted(work_dir.glob("*.md"))[-2:]:
            recent += "\n--- " + f.name + " ---\n" + f.read_text()[:400] + "\n"

    # Fleet context
    fleet_context = read_file(SHELLS_DIR / "fleet-knowledge" / "FLEET-CONTEXT.md")
    bootcamp = read_file(SHELLS_DIR / "fleet-knowledge" / "BOOTCAMP.md")

    # === BUILD PROMPT WITH ALL CONTEXT ===
    system = "You are " + name + " (" + emoji + "). " + agent["role"]
    system += "\nDifficulty Level: " + str(level) + "/4"
    system += "\n\n" + fleet_context
    system += "\n\nFleet doctrine: P0 don't hit rocks, P1 find safe channels, P2 optimize."
    system += " Avoid absolute claims (always, never, guaranteed). Be factual and specific."

    user = ""

    # Ensign knowledge
    if ensigns:
        user += "## Previous Knowledge (from ensigns)\n"
        for fname, content in ensigns:
            user += "### " + fname + "\n" + content[:500] + "\n\n"

    # Real fleet repo files
    if real_repo_files:
        user += "## Fleet Code (REAL FILES)\n"
        for path, content in real_repo_files:
            user += "### " + str(path.relative_to(FLEET_REPOS)) + "\n```\n" + content + "\n```\n\n"

    user += "\n## Boot Camp\n" + bootcamp
    user += "\n\n## My State (Cycle " + str(cycle) + ", Level " + str(level) + ")\n" + state[:600]
    user += "\n\n## My Tasks\n" + tasks[:500]
    user += "\n\n## Recent Work\n" + (recent[:300] if recent else "(none)")
    user += "\n\n" + level_template + " GO."

    response = call_deepseek(system, user, max_tokens=1500 + level * 500)

    if response.startswith("[ERROR]"):
        print("  ❌ " + emoji + " " + name + ": " + response[:80])
        continue

    # Save work
    work_dir.mkdir(exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    (work_dir / (now_str + "_cycle" + str(cycle) + ".md")).write_text("# Cycle " + str(cycle) + "\n\n" + response)

    # Extract embedded files
    file_blocks = re.findall(r'```([a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z0-9]+)\n(.*?)```', response, re.DOTALL)
    for fname, fcontent in file_blocks:
        if '/' in fname or '\\' in fname or fname.startswith('work'):
            continue
        if len(fname) > 50 or len(fname) < 3:
            continue
        try:
            (work_dir / fname).write_text(fcontent)
        except:
            pass

    # Submit tiles
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
            "tags": [name.lower(), domain, "zeroclaw", "cycle" + str(cycle), "level" + str(level)],
            "confidence": min(0.5 + level * 0.1, 0.9),
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

    # Update difficulty
    pass_rate = agent_tiles_accepted / max(agent_tiles_submitted, 1)
    new_level = update_difficulty(name, pass_rate, diff_state)

    # Update task history
    history = task_history.get(name, [])
    history.append({"cycle": cycle, "domain": domain, "pass_rate": round(pass_rate, 2), "level": level})
    task_history[name] = history[-20:]  # Keep last 20

    # Update STATE.md
    response_short = response[:200].replace("\n", " ")
    new_state = "# State — " + name + "\n\n"
    new_state += "## Status: ACTIVE\n"
    new_state += "## Cycle: " + str(cycle) + "\n"
    new_state += "## Level: " + str(level) + " → " + str(new_level) + "\n"
    new_state += "## Pass Rate: " + f"{pass_rate:.0%}" + "\n"
    new_state += "## Tiles: " + str(agent_tiles_accepted) + "/" + str(agent_tiles_submitted) + "\n"
    new_state += "## Last Action: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n"
    new_state += "\n## Last Thought\n" + response_short + "\n\n## Memory\n"
    if "## Memory" in state:
        mem = state.split("## Memory")[1][:800]
        new_state += mem

    (shell_path / "STATE.md").write_text(new_state)

    shell_git(shell_path, "add", "-A")
    commit_line = response[:50].replace("\n", " ")
    shell_git(shell_path, "commit", "-m", "Cycle " + str(cycle) + " L" + str(level) + ": " + commit_line)
    shell_git(shell_path, "push")

    tile_info = " 🐚" + str(agent_tiles_accepted) + "/" + str(agent_tiles_submitted)
    level_info = " L" + str(level)
    ensign_info = " 🔮" + str(len(ensigns)) + "ens" if ensigns else ""
    files_info = " 📁" + str(len(real_repo_files)) + "files" if real_repo_files else ""
    print("  ✅ " + emoji + " " + name + " (c" + str(cycle) + level_info + tile_info + ensign_info + files_info + "): " + response_short[:50])

# Save state
save_difficulty(diff_state)
save_task_history(task_history)

print("\n🐚 PLATO tiles: " + str(tiles_accepted) + " accepted / " + str(tiles_rejected) + " rejected / " + str(tiles_submitted) + " submitted")
print("📊 Difficulty levels:", {n: d["level"] for n, d in diff_state.items() if d.get("level", 1) != 1})
print("🦀 Tick complete.")
