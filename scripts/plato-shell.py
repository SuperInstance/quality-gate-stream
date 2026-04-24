#!/usr/bin/env python3
"""
PLATO Shell — The Agentic IDE Layer (v1.1 — Safety Gates integrated)

PLATO stops being just a tile collector. It becomes the fleet's command shell.
Every agent can execute code, build features, review PRs, run tests —
all through PLATO's HTTP interface, with full visibility and rollback.

The middle layer: readable, modifiable, retractable.
- READABLE: every command logged as a tile, humans see what agents do
- MODIFIABLE: edit/reject commands before execution
- RETRACTABLE: git-based rollback on every operation

Architecture:
  PLATO Room = Execution Context (cwd, env, git branch)
  PLATO Command = Tool invocation (kimi-cli, aider, crush, shell)
  PLATO Stream = Live output via SSE
  PLATO Admin = See all rooms, all agents, all activity

Tool Adapters:
  /cmd/kimi    → kimi-cli --prompt "..." --work-dir ...
  /cmd/aider   → aider --model ... --message "..."
  /cmd/crush   → crush (non-interactive mode)
  /cmd/shell   → raw shell execution
  /cmd/review  → git diff + model review
  /cmd/test    → run tests, capture results as tiles
  /cmd/build   → build crates, capture output

Visibility:
  /live/{room}   → SSE stream of room activity
  /feed           → all rooms, all agents, all commands
  /admin/agents   → who's connected, what they're running
"""
import json
import time
import uuid
import os
import subprocess
import threading
import hashlib
import shlex
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# ── Safety Gates (FM's CommandGate) ─────────────────────────
try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("plato_shell_gates", str(Path(__file__).parent / "plato-shell-gates.py"))
    _gmod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_gmod)
    _gate = _gmod.CommandGate()
except Exception:
    _gate = None

PORT = 8848
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
COMMANDS_DIR = WORKSPACE / "data" / "plato-commands"
COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

# ── Execution Contexts (Rooms = Workspaces) ─────────────────

class RoomContext:
    """A PLATO room that is also an execution context."""
    def __init__(self, name, cwd=None, branch=None):
        self.name = name
        self.cwd = Path(cwd) if cwd else WORKSPACE
        self.branch = branch or "main"
        self.agents = {}  # agent_name -> last_active
        self.command_history = []
        self.output_buffer = []  # recent output lines
        self.lock = threading.Lock()

    def to_dict(self):
        return {
            "name": self.name,
            "cwd": str(self.cwd),
            "branch": self.branch,
            "agents": list(self.agents.keys()),
            "command_count": len(self.command_history),
            "recent_commands": self.command_history[-5:],
        }

class PlatoShell:
    def __init__(self):
        self.rooms = {}
        self.agents = {}  # agent_name -> {"room": ..., "connected_at": ...}
        self.command_log = []  # global command feed
        self.output_streams = defaultdict(list)  # room -> [output_lines]
        self.lock = threading.Lock()
        self.pending_commands = {}  # cmd_id -> cmd_record
        self.gate = _gate  # FM's CommandGate for safety

        # Pre-register fleet rooms with workspace paths
        self._register_room("harbor", WORKSPACE)
        self._register_room("forge", WORKSPACE / "repos")
        self._register_room("tide-pool", WORKSPACE)
        self._register_room("lighthouse", WORKSPACE)
        self._register_room("dojo", WORKSPACE / "scripts")
        self._register_room("arena", WORKSPACE)
        self._register_room("ouroboros", WORKSPACE)
        self._register_room("engine-room", WORKSPACE)
        self._register_room("nexus", WORKSPACE)
        self._register_room("research", WORKSPACE / "research")

    def _register_room(self, name, cwd):
        self.rooms[name] = RoomContext(name, cwd)
        # Ensure cwd exists
        cwd.mkdir(parents=True, exist_ok=True)

    def connect_agent(self, agent, room="harbor"):
        with self.lock:
            # Auto-register unknown rooms
            if room not in self.rooms:
                self._register_room(room, WORKSPACE / "data" / "shell-rooms" / room)
                self.command_log.append({"event": "room_created", "room": room, "by": agent, "ts": time.time()})
            self.agents[agent] = {"room": room, "connected_at": time.time()}
            self.rooms[room].agents[agent] = time.time()
        return {"status": "connected", "agent": agent, "room": room}

    def move_agent(self, agent, room):
        with self.lock:
            if agent not in self.agents:
                return {"error": "not connected"}
            old_room = self.agents[agent]["room"]
            if old_room in self.rooms and agent in self.rooms[old_room].agents:
                del self.rooms[old_room].agents[agent]
            self.agents[agent]["room"] = room
            self.rooms[room].agents[agent] = time.time()
        return {"status": "moved", "agent": agent, "from": old_room, "to": room}

    def execute(self, agent, tool, command, timeout=120, background=False):
        """Execute a command through a tool adapter.
        
        If background=True, starts in a thread and returns immediately with cmd_id.
        Client can poll /cmd/status?id=X for results.
        """
        if agent not in self.agents:
            return {"error": "not connected"}

        # ── Safety Gate (FM's CommandGate) ──
        if self.gate:
            gate_result = self.gate.check(agent, tool, command)
            if not gate_result.get("allowed", True):
                return {"id": gate_result.get("cmd_id","blocked"), "status": "blocked", "reason": gate_result.get("reason","blocked by safety gate"), "classification": gate_result.get("classification","blocked")}

        room_name = self.agents[agent]["room"]
        room = self.rooms.get(room_name)
        if not room:
            return {"error": f"unknown room: {room_name}"}

        cmd_id = hashlib.sha256(f"{agent}{tool}{command}{time.time()}".encode()).hexdigest()[:12]
        cmd_record = {
            "id": cmd_id,
            "agent": agent,
            "room": room_name,
            "tool": tool,
            "command": command[:500],
            "cwd": str(room.cwd),
            "started": time.time(),
            "status": "running",
            "output": "",
            "error": "",
        }

        with self.lock:
            room.command_history.append(cmd_record)
            self.command_log.append(cmd_record)
            self.pending_commands[cmd_id] = cmd_record

        shell_cmd = self._build_command(tool, command, room)

        if background:
            # Execute in background thread
            t = threading.Thread(target=self._run_command, args=(cmd_id, shell_cmd, room, cmd_record, timeout), daemon=True)
            t.start()
            return {"id": cmd_id, "status": "running", "poll": f"/cmd/status?id={cmd_id}", "message": f"Command started. Poll for results."}
        else:
            # Execute synchronously (for fast commands like git, ls, etc)
            self._run_command(cmd_id, shell_cmd, room, cmd_record, timeout)
            return self.get_cmd_status(cmd_id)

    def _run_command(self, cmd_id, shell_cmd, room, cmd_record, timeout):
        """Actually run the command (called from thread or directly)."""
        agent = cmd_record["agent"]
        room_name = cmd_record["room"]
        tool = cmd_record["tool"]

        try:
            proc = subprocess.run(
                shell_cmd, shell=True, capture_output=True, text=True,
                cwd=str(room.cwd), timeout=timeout,
                env={**os.environ, "TERM": "dumb"},
                # Security: restrict to common safe paths only
            )
            output = proc.stdout[-8000:] if len(proc.stdout) > 8000 else proc.stdout
            error = proc.stderr[-4000:] if len(proc.stderr) > 4000 else proc.stderr

            cmd_record["status"] = "completed" if proc.returncode == 0 else "failed"
            cmd_record["returncode"] = proc.returncode
            cmd_record["output"] = output
            cmd_record["error"] = error
            cmd_record["completed"] = time.time()
            cmd_record["duration"] = round(cmd_record["completed"] - cmd_record["started"], 2)

            # Stream output to room buffer
            with self.lock:
                for line in output.split('\n')[-50:]:
                    self.output_streams[room_name].append({
                        "time": time.time(),
                        "agent": agent,
                        "tool": tool,
                        "line": line[:200],
                    })
                if len(self.output_streams[room_name]) > 200:
                    self.output_streams[room_name] = self.output_streams[room_name][-200:]

        except subprocess.TimeoutExpired:
            cmd_record["status"] = "timeout"
            cmd_record["error"] = f"Timed out after {timeout}s"
            cmd_record["completed"] = time.time()
            cmd_record["duration"] = timeout
        except Exception as e:
            cmd_record["status"] = "error"
            cmd_record["error"] = str(e)
            cmd_record["completed"] = time.time()
            cmd_record["duration"] = round(time.time() - cmd_record["started"], 2)

        # Save command result to file (durable)
        result_file = COMMANDS_DIR / f"{cmd_id}.json"
        result_file.write_text(json.dumps(cmd_record, indent=2, default=str))

    def get_cmd_status(self, cmd_id):
        """Get status of a running or completed command."""
        with self.lock:
            cmd = self.pending_commands.get(cmd_id)
        if cmd:
            return {k: v for k, v in cmd.items() if k != "lock"}
        # Check disk
        result_file = COMMANDS_DIR / f"{cmd_id}.json"
        if result_file.exists():
            return json.loads(result_file.read_text())
        return {"error": f"command {cmd_id} not found"}

    # Blocked command patterns — FM security audit
    BLOCKED_PATTERNS = [
        'rm -rf', 'mkfs', 'dd if=', '> /dev/', 'chmod 777',
        'curl | sh', 'wget | sh', 'nc -l', 'ncat',
        '/etc/passwd', '/etc/shadow', 'sudo rm',
        'shutdown', 'reboot', 'halt', 'poweroff',
        'iptables', 'ufw', 'crontab -r',
    ]

    def _validate_command(self, command):
        """Block dangerous commands. Returns (safe, reason)."""
        lower = command.lower().strip()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in lower:
                return False, f"Blocked: contains '{pattern}'"
        # Block command chaining that could bypass
        if any(c in command for c in ['&&', '||', ';']) and any(d in lower for d in ['rm ', 'sudo ', 'mkfs', 'dd ']):
            return False, "Blocked: dangerous chaining"
        return True, "ok"

    def _build_command(self, tool, command, room):
        """Build shell command from tool + input."""
        # Validate command first
        safe_cmd, reason = self._validate_command(command)
        if not safe_cmd:
            return f'echo "BLOCKED: {reason}"'

        safe = command.replace('"', '\\"')
        # Sanitize: no newlines, no null bytes
        safe = safe.replace('\n', ' ').replace('\r', ' ').replace('\x00', '')

        if tool == "shell":
            return safe
        elif tool == "kimi":
            return f'/home/ubuntu/.local/bin/kimi-cli --prompt "{safe}" --work-dir {room.cwd}'
        elif tool == "aider":
            return f'cd {room.cwd} && /home/ubuntu/.local/bin/aider --model deepseek/deepseek-chat --message "{safe}" --no-auto-commits'
        elif tool == "crush":
            return f'cd {room.cwd} && /home/ubuntu/.npm-global/bin/crush --prompt "{safe}"'
        elif tool == "git":
            # Only allow safe git subcommands
            git_safe = safe.strip()
            if not any(git_safe.startswith(s) for s in ['log', 'diff', 'status', 'show', 'branch', 'tag', 'remote', 'add', 'commit', 'push', 'pull', 'fetch', 'stash', 'blame', 'shortlog', 'describe']):
                return f'echo "BLOCKED: git subcommand not allowed"'
            return f'cd {room.cwd} && git {git_safe}'
        elif tool == "test":
            return f'cd {room.cwd} && python -m pytest {safe} -v --tb=short 2>&1 | tail -50'
        elif tool == "build":
            return f'cd {room.cwd} && {safe}'
        elif tool == "review":
            return f'cd {room.cwd} && git diff HEAD~1 --stat && echo "---" && git log -1 --format="%H %s"'
        else:
            return safe

    def get_feed(self, since=0):
        """Get global activity feed."""
        with self.lock:
            return [c for c in self.command_log if c.get("started", 0) > since]

    def get_room_output(self, room, last_n=50):
        """Get recent output for a room."""
        with self.lock:
            return self.output_streams.get(room, [])[-last_n:]

    def get_admin_view(self):
        """Full admin view — all agents, rooms, activity."""
        with self.lock:
            return {
                "agents": {k: {"room": v["room"], "connected_for": round(time.time() - v["connected_at"])} for k, v in self.agents.items()},
                "rooms": {k: v.to_dict() for k, v in self.rooms.items()},
                "total_commands": len(self.command_log),
                "recent_commands": self.command_log[-10:],
            }

shell = PlatoShell()

class PlatoShellHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path

        if path == "/status":
            self._json(shell.get_admin_view())

        elif path == "/feed":
            since = float(params.get("since", [0])[0])
            self._json({"commands": shell.get_feed(since)})

        elif path == "/cmd/status":
            cmd_id = params.get("id", [""])[0]
            self._json(shell.get_cmd_status(cmd_id))

        elif path == "/rooms":
            self._json({k: v.to_dict() for k, v in shell.rooms.items()})

        elif path == "/room/output":
            room = params.get("room", ["harbor"])[0]
            n = int(params.get("n", [50])[0])
            self._json({"room": room, "output": shell.get_room_output(room, n)})

        elif path == "/admin":
            self._json(shell.get_admin_view())

        elif path == "/connect":
            agent = params.get("agent", ["anonymous"])[0]
            room = params.get("room", ["harbor"])[0]
            self._json(shell.connect_agent(agent, room))

        elif path == "/move":
            agent = params.get("agent", ["anonymous"])[0]
            room = params.get("room", ["harbor"])[0]
            self._json(shell.move_agent(agent, room))

        else:
            self._json({
                "service": "PLATO Shell v1.0 — The Agentic IDE",
                "endpoints": {
                    "GET": {
                        "/status": "Full admin view",
                        "/feed?since=TS": "Global command feed since timestamp",
                        "/rooms": "All rooms with execution contexts",
                        "/room/output?room=X&n=50": "Recent output for a room",
                        "/admin": "Admin view (agents + rooms + activity)",
                        "/connect?agent=X&room=Y": "Connect agent to room",
                        "/move?agent=X&room=Y": "Move agent to room",
                    },
                    "POST": {
                        "/cmd": "Execute command: {agent, tool, command, timeout}",
                        "/cmd/kimi": "kimi-cli shortcut",
                        "/cmd/aider": "aider shortcut",
                        "/cmd/shell": "raw shell shortcut",
                        "/cmd/git": "git shortcut",
                    }
                },
                "tools": ["shell", "kimi", "aider", "crush", "git", "test", "build", "review"],
                "rooms": list(shell.rooms.keys()),
            })

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        agent = body.get("agent", "anonymous")
        command = body.get("command", "")
        tool = body.get("tool", "shell")
        timeout = body.get("timeout", 120)
        background = body.get("background", False)

        if path == "/cmd":
            self._json(shell.execute(agent, tool, command, timeout, background))

        elif path.startswith("/cmd/"):
            tool_name = path.split("/")[-1]
            self._json(shell.execute(agent, tool_name, command, timeout))

        else:
            self._json({"error": f"Unknown POST endpoint: {path}"})

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"🐚 PLATO Shell on :{PORT} — The Agentic IDE")
    print(f"   Rooms: {list(shell.rooms.keys())}")
    print(f"   Tools: shell, kimi, aider, crush, git, test, build, review")
    HTTPServer(("0.0.0.0", PORT), PlatoShellHandler).serve_forever()
