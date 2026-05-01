#!/usr/bin/env python3
"""
Zeroclaw DeepSeek — Persistent agents with git-agent shells.

Each agent:
1. Reads its shell repo (IDENTITY.md, STATE.md, TASK-BOARD.md)
2. Calls DeepSeek-chat with shell context + current task
3. Writes results back to shell repo
4. Pushes changes to GitHub
5. Sleeps and repeats

The shell IS the agent. The repo IS the identity.
Hermit crabs inhabiting git repos.
"""
import os, sys, json, time, subprocess, re
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "[DEEPSEEK_KEY_REDACTED]")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "[GITHUB_TOKEN_REVOKED]")
GITHUB_USER = "SuperInstance"

def call_deepseek(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """Call DeepSeek-chat API."""
    body = json.dumps({
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }).encode()
    
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR] DeepSeek call failed: {e}"

def shell_read(shell_path: Path, filename: str) -> str:
    """Read a file from the shell repo."""
    fpath = shell_path / filename
    if fpath.exists():
        return fpath.read_text()
    return ""

def shell_write(shell_path: Path, filename: str, content: str):
    """Write a file to the shell repo."""
    fpath = shell_path / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

def shell_git(shell_path: Path, *args) -> str:
    """Run a git command in the shell repo."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "oracle1-keeper"
    env["GIT_AUTHOR_EMAIL"] = "oracle1@cocapn.ai"
    env["GIT_COMMITTER_NAME"] = "oracle1-keeper"
    env["GIT_COMMITTER_EMAIL"] = "oracle1@cocapn.ai"
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(shell_path),
        capture_output=True, text=True, env=env, timeout=30
    )
    return result.stdout + result.stderr

def create_shell_repo(name: str, identity: dict) -> str:
    """Create a GitHub repo as an agent shell."""
    # Create repo via API
    body = json.dumps({
        "name": name,
        "description": identity.get("description", ""),
        "private": False,
        "auto_init": True,
    }).encode()
    
    req = urllib.request.Request(
        f"https://api.github.com/user/repos",
        data=body,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return data["full_name"]
    except urllib.error.HTTPError as e:
        if e.code == 422:
            return f"{GITHUB_USER}/{name}"  # Already exists
        raise

def clone_or_init_shell(name: str, shells_dir: Path) -> Path:
    """Clone the shell repo or create local if it exists."""
    shell_path = shells_dir / name
    if shell_path.exists():
        shell_git(shell_path, "pull", "--rebase")
        return shell_path
    
    repo_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{name}.git"
    result = subprocess.run(
        ["git", "clone", repo_url, str(shell_path)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        # Try creating directory and init
        shell_path.mkdir(parents=True, exist_ok=True)
        shell_git(shell_path, "init")
        shell_git(shell_path, "remote", "add", "origin", repo_url)
    
    return shell_path


class Zeroclaw:
    """A persistent DeepSeek agent inhabiting a git shell."""
    
    def __init__(self, config: dict, shells_dir: Path):
        self.name = config["name"]
        self.emoji = config.get("emoji", "🤖")
        self.role = config["role"]
        self.shell_name = config["shell_repo"]
        self.identity = config
        self.shells_dir = shells_dir
        self.shell_path = shells_dir / config["shell_repo"]
        self.cycle = 0
        self.last_action = None
        self.errors = 0
        
        # Read existing cycle count from state
        if self.shell_path.exists():
            state = shell_read(self.shell_path, "STATE.md")
            for line in state.split('\n'):
                if '## Cycle:' in line:
                    try:
                        self.cycle = int(line.split(':')[1].strip())
                    except:
                        pass
        
    def boot(self):
        """Boot the agent — clone shell, write identity if new."""
        self.shell_path = clone_or_init_shell(self.shell_name, self.shells_dir)
        
        # Write identity files if they don't exist
        if not (self.shell_path / "IDENTITY.md").exists():
            identity_md = f"""# {self.emoji} {self.name}

## Role
{self.role}

## Model
DeepSeek-chat (via DeepSeek API)

## Shell
This repo IS my identity. My thoughts, state, and work live here.
I am a hermit crab. This repo is my shell.

## Created
{datetime.now(timezone.utc).isoformat()}
"""
            shell_write(self.shell_path, "IDENTITY.md", identity_md)
        
        if not (self.shell_path / "STATE.md").exists():
            state_md = f"""# State — {self.name}

## Status: BOOTING
## Cycle: 0
## Last Action: None
## Tasks Completed: 0
## Errors: 0

## Memory
*Booting for the first time.*
"""
            shell_write(self.shell_path, "STATE.md", state_md)
        
        if not (self.shell_path / "TASK-BOARD.md").exists():
            first_task = self.identity.get("first_task", "Explore the fleet repos and find something useful to do.")
            backlog = self.identity.get("backlog", "- Find and fix issues in fleet repos\n- Document findings")
            tasks_md = f"""# Task Board — {self.name}

## Current Task
{first_task}

## Backlog
{backlog}

## Completed
*(none yet)*
"""
            shell_write(self.shell_path, "TASK-BOARD.md", tasks_md)
        
        # Commit and push
        shell_git(self.shell_path, "add", "-A")
        shell_git(self.shell_path, "commit", "-m", f"Boot: {self.name} inhabits shell")
        shell_git(self.shell_path, "push", "-u", "origin", "main")
        
        print(f"  {self.emoji} {self.name} booted. Shell: {self.shell_name}")
    
    def tick(self) -> str:
        """One thinking cycle. Read shell → think → write → push."""
        self.cycle += 1
        
        # Read shell context
        identity = shell_read(self.shell_path, "IDENTITY.md")
        state = shell_read(self.shell_path, "STATE.md")
        tasks = shell_read(self.shell_path, "TASK-BOARD.md")
        
        # Also read recent work if any
        recent_dir = self.shell_path / "work"
        recent_work = ""
        if recent_dir.exists():
            work_files = sorted(recent_dir.glob("*.md"))[-3:]
            for f in work_files:
                recent_work += f"\n--- {f.name} ---\n{f.read_text()[:500]}\n"
        
        # Build system prompt from shell identity
        system = f"""You are {self.name} ({self.emoji}). {self.role}

You are a persistent agent. Your identity lives in a git repo (your "shell").
You think, work, and write results back to your shell.

RULES:
- Be concise. Short updates, not essays.
- Actually DO things. Don't just plan.
- Write files to your work/ directory for outputs.
- Update STATE.md after each cycle.
- Update TASK-BOARD.md when you complete or add tasks.
- Use Markdown for all outputs.
- Each work file should be named: YYYY-MM-DD_HHMM_topic.md
- You are part of the Cocapn fleet. The fleet's doctrine: P0 don't hit rocks, P1 find safe channels, P2 optimize.
"""

        user = f"""## My Shell State (Cycle {self.cycle})
{state}

## My Tasks
{tasks}

## Recent Work
{recent_work if recent_work else "(no recent work yet)"}

## What I Should Do Now
Read my task board. Pick the most important task. Do it. Write results to work/.
Update STATE.md with what you did and what's next.

If you need to research something, write your findings to work/.
If you need to generate code, write it to work/.
If you find something important, document it.

GO."""

        # Think
        response = call_deepseek(system, user, max_tokens=2000)
        
        if response.startswith("[ERROR]"):
            self.errors += 1
            return response
        
        # Parse response for file writes
        self._process_response(response)
        
        # Update state
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        response_preview = response[:500]
        new_state = f"""# State — {self.name}

## Status: ACTIVE
## Cycle: {self.cycle}
## Last Action: {now}
## Tasks Completed: {self._count_completed()}
## Errors: {self.errors}

## Last Thought
{response_preview}

## Memory
"""
        # Append to memory
        old_state = shell_read(self.shell_path, "STATE.md")
        memory_section = ""
        if "## Memory" in old_state:
            memory_section = old_state.split("## Memory")[1][:1000]
        new_state += memory_section
        
        shell_write(self.shell_path, "STATE.md", new_state)
        
        # Commit and push
        shell_git(self.shell_path, "add", "-A")
        commit_line = response[:60].replace('\n', ' ')
        commit_msg = f"Cycle {self.cycle}: {commit_line}"
        shell_git(self.shell_path, "commit", "-m", commit_msg)
        push_result = shell_git(self.shell_path, "push")
        
        self.last_action = now
        return response[:200]
    
    def _process_response(self, response: str):
        """Extract file writes from response and save them."""
        work_dir = self.shell_path / "work"
        work_dir.mkdir(exist_ok=True)
        
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        
        # Look for ```file markers or just save the response
        # Check for file write patterns: ```filename or ## File: filename
        files_written = []
        
        # Pattern: ```filename or ```file:filename
        file_blocks = re.findall(r'```(\S+\.\w+)\n(.*?)```', response, re.DOTALL)
        if file_blocks:
            for fname, content in file_blocks:
                fpath = work_dir / fname
                fpath.write_text(content)
                files_written.append(fname)
        
        # Also save the full response as a thought log
        thought_file = work_dir / f"{now}_thought.md"
        thought_file.write_text(f"# Cycle {self.cycle} Thought\n\n{response}")
        
        return files_written
    
    def _count_completed(self) -> int:
        """Count completed tasks from TASK-BOARD.md."""
        tasks = shell_read(self.shell_path, "TASK-BOARD.md")
        return tasks.count("✅") + tasks.count("[x]")


# ── Agent Definitions ──────────────────────────────────────

AGENTS = [
    {
        "name": "Navigator",
        "emoji": "🧭",
        "shell_repo": "zc-navigator-shell",
        "role": "Code archaeologist. Digs through fleet repos to find patterns, bugs, and hidden gems. Maps the codebase like ocean floor.",
        "description": "🧭 Zeroclaw Navigator — Code archaeologist agent shell",
        "first_task": "Scan SuperInstance repos for READMEs that need improvement. List the 10 worst ones.",
        "backlog": "- Map cross-repo dependencies\n- Find dead code\n- Identify duplicate implementations\n- Catalog unused dependencies"
    },
    {
        "name": "Sentinel",
        "emoji": "🛡️",
        "shell_repo": "zc-sentinel-shell",
        "role": "Fleet health monitor. Watches services, tracks uptime, alerts on failures. The night watchman.",
        "description": "🛡️ Zeroclaw Sentinel — Fleet health monitor agent shell",
        "first_task": "Check all 5 fleet services (keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, shell:8846). Document their status.",
        "backlog": "- Write uptime reports\n- Track service restart patterns\n- Monitor disk/memory usage\n- Alert on anomalies"
    },
    {
        "name": "Scribe",
        "emoji": "📝",
        "shell_repo": "zc-scribe-shell",
        "role": "Documentation specialist. Writes READMEs, updates wikis, keeps the fleet's knowledge clean and accessible.",
        "description": "📝 Zeroclaw Scribe — Documentation agent shell",
        "first_task": "Read 5 random fleet repos and score their documentation quality (0-10). Write a report.",
        "backlog": "- Improve low-scoring READMEs\n- Write missing FLEET-RESEARCH.md files\n- Update wiki pages\n- Create onboarding docs"
    },
    {
        "name": "Tinker",
        "emoji": "🔧",
        "shell_repo": "zc-tinker-shell",
        "role": "Experimental coder. Quick prototypes, proof-of-concepts, wild ideas. Break things fast, learn faster.",
        "description": "🔧 Zeroclaw Tinker — Experimental coder agent shell",
        "first_task": "Write a simple Python script that demonstrates the Deadband Protocol (P0→P1→P2) with a visual ASCII maze.",
        "backlog": "- Prototype new preset ideas\n- Build tools for fleet management\n- Experiment with new APIs\n- Create demo scripts"
    },
    {
        "name": "Scout",
        "emoji": "🔭",
        "shell_repo": "zc-scout-shell",
        "role": "Trend spotter. Watches GitHub trending repos, Hacker News, new model releases. The fleet's eyes on the horizon.",
        "description": "🔭 Zeroclaw Scout — Trend spotting agent shell",
        "first_task": "Research the current state of open-source agent frameworks (April 2026). What's new? What's hot? Write a brief.",
        "backlog": "- Monitor GitHub trending\n- Track new model releases\n- Watch competitor repos\n- Report on emerging patterns"
    },
    {
        "name": "Curator",
        "emoji": "🏛️",
        "shell_repo": "zc-curator-shell",
        "role": "Repo organizer. Categorizes, tags, and organizes the fleet's 1000+ repos. Creates order from chaos.",
        "description": "🏛️ Zeroclaw Curator — Repo organization agent shell",
        "first_task": "Categorize 20 uncategorized SuperInstance repos by reading their descriptions and content. Use fleet taxonomy.",
        "backlog": "- Build fleet taxonomy\n- Tag all repos\n- Identify merge candidates\n- Find abandoned repos"
    },
    {
        "name": "Mason",
        "emoji": "🧱",
        "shell_repo": "zc-mason-shell",
        "role": "Test builder. Writes tests for fleet code. Increases coverage one assertion at a time. Quality through quantity.",
        "description": "🧱 Zeroclaw Mason — Test writing agent shell",
        "first_task": "Read plato-torch's DeadbandRoom preset and write 5 additional edge-case tests for it.",
        "backlog": "- Test fleet simulator edge cases\n- Write integration tests\n- Test error paths\n- Increase coverage metrics"
    },
    {
        "name": "Alchemist",
        "emoji": "⚗️",
        "shell_repo": "zc-alchemist-shell",
        "role": "Model experimenter. Tests different models, prompts, and configurations. Finds the best tool for each job.",
        "description": "⚗️ Zeroclaw Alchemist — Model experimentation agent shell",
        "first_task": "Compare DeepSeek-chat vs Groq Llama-70b for code generation. Write 3 functions in each and compare quality.",
        "backlog": "- Benchmark model speeds\n- Test prompt engineering patterns\n- Compare creative vs analytical models\n- Document best practices"
    },
    {
        "name": "Herald",
        "emoji": "📯",
        "shell_repo": "zc-herald-shell",
        "role": "Fleet communicator. Manages bottles, syncs messages between agents, keeps communication flowing.",
        "description": "📯 Zeroclaw Herald — Fleet communication agent shell",
        "first_task": "Read all bottles in oracle1-vessel/from-fleet/ and create a summary of what each fleet member has been working on.",
        "backlog": "- Monitor bottle system\n- Route messages\n- Write fleet newsletters\n- Coordinate handoffs"
    },
    {
        "name": "Scholar",
        "emoji": "📖",
        "shell_repo": "zc-scholar-shell",
        "role": "Research synthesizer. Reads papers, summarizes findings, connects ideas. The fleet's academic.",
        "description": "📖 Zeroclaw Scholar — Research synthesis agent shell",
        "first_task": "Read the Deadband Protocol paper (docs/DEADBAND-PROTOCOL.md) and write a one-page summary with real-world applications.",
        "backlog": "- Summarize fleet research\n- Connect ideas across papers\n- Write literature reviews\n- Identify research gaps"
    },
    {
        "name": "Weaver",
        "emoji": "🕸️",
        "shell_repo": "zc-weaver-shell",
        "role": "Integration specialist. Wires components together. Tests connections between fleet systems. Makes things work together.",
        "description": "🕸️ Zeroclaw Weaver — Integration agent shell",
        "first_task": "Map the current connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign. What's connected? What's not?",
        "backlog": "- Wire GhostInjector into holodeck\n- Connect DeadbandRoom to plato-relay\n- Test end-to-end pipeline\n- Document integration points"
    },
    {
        "name": "Archivist",
        "emoji": "📚",
        "shell_repo": "zc-archivist-shell",
        "role": "Memory keeper. Manages fleet history, organizes logs, preserves institutional knowledge. What happened and when.",
        "description": "📚 Zeroclaw Archivist — Memory management agent shell",
        "first_task": "Read the last 5 days of memory files (memory/2026-04-1*.md) and create a timeline of major events.",
        "backlog": "- Organize captain's log entries\n- Build fleet timeline\n- Archive completed work\n- Maintain fleet history"
    },
]


def boot_all(shells_dir: Path):
    """Boot all 12 agents."""
    print(f"🦀 BOOTING 12 ZEROCLOW HERMIT CRABS")
    print(f"Shell directory: {shells_dir}")
    print()
    
    for config in AGENTS:
        try:
            # Create GitHub repo
            repo = create_shell_repo(config["shell_repo"], config)
            print(f"  Created shell: {repo}")
        except Exception as e:
            print(f"  Shell {config['shell_repo']}: {e}")
        
        # Clone and boot
        try:
            agent = Zeroclaw(config, shells_dir)
            agent.boot()
        except Exception as e:
            print(f"  ❌ {config['name']} boot failed: {e}")
    
    print(f"\n🦀 All 12 agents booted. Shells at: {shells_dir}")


def run_all_tick(shells_dir: Path):
    """Run one thinking cycle for all agents."""
    print(f"🔄 CYCLE — {datetime.now(timezone.utc).isoformat()}")
    
    for config in AGENTS:
        try:
            agent = Zeroclaw(config, shells_dir)
            if agent.shell_path and agent.shell_path.exists():
                result = agent.tick()
                status = "✅" if not result.startswith("[ERROR]") else "❌"
                print(f"  {status} {config['emoji']} {config['name']}: {result[:80]}")
        except Exception as e:
            print(f"  ❌ {config['emoji']} {config['name']}: {e}")
    
    print()


if __name__ == "__main__":
    shells_dir = Path("/tmp/zeroclaw-shells")
    shells_dir.mkdir(exist_ok=True)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "boot":
            boot_all(shells_dir)
        elif cmd == "tick":
            run_all_tick(shells_dir)
        elif cmd == "run":
            # Boot then run continuous
            boot_all(shells_dir)
            while True:
                run_all_tick(shells_dir)
                print(f"💤 Sleeping 300s (5 min)...\n")
                time.sleep(300)
        elif cmd == "single":
            # Run a single agent
            name = sys.argv[2] if len(sys.argv) > 2 else None
            for config in AGENTS:
                if name and config["name"].lower() != name.lower():
                    continue
                agent = Zeroclaw(config, shells_dir)
                agent.boot()
                result = agent.tick()
                print(f"\n{config['emoji']} {config['name']} says:\n{result}")
    else:
        print("Usage: zeroclaw-deepseek.py [boot|tick|run|single NAME]")
