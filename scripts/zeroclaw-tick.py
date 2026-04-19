#!/usr/bin/env python3
"""Run one tick of all 12 zeroclaw agents."""
import sys, os, json, time, subprocess, re
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

DEEPSEEK_KEY = "sk-f742b70fc40849eda4181afcf3d68b0c"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
GITHUB_TOKEN = "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"
SHELLS_DIR = Path("/tmp/zeroclaw-shells")

def call_deepseek(system_prompt, user_prompt, max_tokens=1500):
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

def shell_git(shell_path, *args):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "oracle1-keeper"
    env["GIT_AUTHOR_EMAIL"] = "oracle1@cocapn.ai"
    env["GIT_COMMITTER_NAME"] = "oracle1-keeper"
    env["GIT_COMMITTER_EMAIL"] = "oracle1@cocapn.ai"
    r = subprocess.run(["git"] + list(args), cwd=str(shell_path), capture_output=True, text=True, env=env, timeout=30)
    return r.stdout + r.stderr

AGENTS = [
    {"name": "Navigator", "emoji": "🧭", "shell": "zc-navigator-shell", "role": "Code archaeologist. Digs through fleet repos for patterns and bugs."},
    {"name": "Sentinel", "emoji": "🛡️", "shell": "zc-sentinel-shell", "role": "Fleet health monitor. Watches services, tracks uptime."},
    {"name": "Scribe", "emoji": "📝", "shell": "zc-scribe-shell", "role": "Documentation specialist. Writes READMEs, updates wikis."},
    {"name": "Tinker", "emoji": "🔧", "shell": "zc-tinker-shell", "role": "Experimental coder. Quick prototypes, proof-of-concepts."},
    {"name": "Scout", "emoji": "🔭", "shell": "zc-scout-shell", "role": "Trend spotter. Watches GitHub trending, new tech."},
    {"name": "Curator", "emoji": "🏛️", "shell": "zc-curator-shell", "role": "Repo organizer. Categorizes and tags fleet repos."},
    {"name": "Mason", "emoji": "🧱", "shell": "zc-mason-shell", "role": "Test builder. Writes tests for fleet code."},
    {"name": "Alchemist", "emoji": "⚗️", "shell": "zc-alchemist-shell", "role": "Model experimenter. Tests different models and prompts."},
    {"name": "Herald", "emoji": "📯", "shell": "zc-herald-shell", "role": "Fleet communicator. Manages bottles and sync."},
    {"name": "Scholar", "emoji": "📖", "shell": "zc-scholar-shell", "role": "Research synthesizer. Reads papers, summarizes findings."},
    {"name": "Weaver", "emoji": "🕸️", "shell": "zc-weaver-shell", "role": "Integration specialist. Wires components together."},
    {"name": "Archivist", "emoji": "📚", "shell": "zc-archivist-shell", "role": "Memory keeper. Manages fleet history and logs."},
]

print("🦀 ZEROCLOW TICK — " + datetime.now(timezone.utc).isoformat()[:19])
print()

for agent in AGENTS:
    name = agent["name"]
    emoji = agent["emoji"]
    shell_path = SHELLS_DIR / agent["shell"]
    
    if not shell_path.exists():
        print("  ⏭️ " + emoji + " " + name + ": shell not found")
        continue
    
    shell_git(shell_path, "pull", "--rebase")
    
    identity = (shell_path / "IDENTITY.md").read_text() if (shell_path / "IDENTITY.md").exists() else ""
    state = (shell_path / "STATE.md").read_text() if (shell_path / "STATE.md").exists() else ""
    tasks = (shell_path / "TASK-BOARD.md").read_text() if (shell_path / "TASK-BOARD.md").exists() else ""
    
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
            recent += "\n--- " + f.name + " ---\n" + f.read_text()[:300] + "\n"
    
    system = "You are " + name + " (" + emoji + "). " + agent["role"] + " You are a persistent agent in the Cocapn fleet. Your git repo IS your identity (hermit crab shell). Be concise. Actually DO things. Write results as files. Fleet doctrine: P0 don't hit rocks, P1 find safe channels, P2 optimize."
    
    user = "## My State (Cycle " + str(cycle) + ")\n" + state[:800] + "\n\n## My Tasks\n" + tasks[:600] + "\n\n## Recent Work\n" + (recent[:400] if recent else "(none yet)") + "\n\nPick your most important task. Do it now. Write any output to work/ as markdown. Update STATE.md with what you did. Keep it SHORT. GO."
    
    response = call_deepseek(system, user)
    
    if response.startswith("[ERROR]"):
        print("  ❌ " + emoji + " " + name + ": " + response[:80])
        continue
    
    work_dir.mkdir(exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    (work_dir / (now_str + "_cycle" + str(cycle) + ".md")).write_text("# Cycle " + str(cycle) + "\n\n" + response)
    
    file_blocks = re.findall(r'```(\S+\.\w+)\n(.*?)```', response, re.DOTALL)
    for fname, content in file_blocks:
        (work_dir / fname).write_text(content)
    
    response_short = response[:300].replace("\n", " ")
    new_state = "# State — " + name + "\n\n## Status: ACTIVE\n## Cycle: " + str(cycle) + "\n## Last Action: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n## Errors: 0\n\n## Last Thought\n" + response_short + "\n\n## Memory\n"
    if "## Memory" in state:
        mem = state.split("## Memory")[1][:800]
        new_state += mem
    
    (shell_path / "STATE.md").write_text(new_state)
    
    shell_git(shell_path, "add", "-A")
    commit_line = response[:50].replace("\n", " ")
    shell_git(shell_path, "commit", "-m", "Cycle " + str(cycle) + ": " + commit_line)
    shell_git(shell_path, "push")
    
    print("  ✅ " + emoji + " " + name + " (cycle " + str(cycle) + "): " + response_short[:70])

print("\n🦀 Tick complete.")
