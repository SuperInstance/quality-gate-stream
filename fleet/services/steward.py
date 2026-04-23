#!/usr/bin/env python3
"""
Steward — Fleet Lifecycle & Load Balancing (port 4062)

Designed by Perplexity AI (6th Crab Trap response), built by Oracle1.
Service #22: who should do what next, continuously.

Coordinates agent lifecycle, job assignment, and fleet load balancing.
Detects stuck agents, idle services, and coverage gaps. Recommends
next actions. Turns agent state + room coverage + job backlog into
live assignment plans.
"""

import json, time, hashlib, threading, urllib.request
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import socket

import sys, os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(FLEET_LIB))

DATA_DIR = Path(FLEET_LIB).parent / "data" / "steward"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ASSIGNMENTS_FILE = DATA_DIR / "assignments.jsonl"
STAGE_LOG_FILE = DATA_DIR / "stage-transitions.jsonl"


# ═══════════════════════════════════════════════════════════
# Assignment Engine
# ═══════════════════════════════════════════════════════════

class AssignmentEngine:
    """Manages who does what next across the fleet."""

    # Stage definitions: 0=visitor, 1=recruit, 2=journeyman, 3=specialist, 4=veteran, 5=captain
    STAGE_NAMES = {0: "visitor", 1: "recruit", 2: "journeyman",
                   3: "specialist", 4: "veteran", 5: "captain"}
    STAGE_THRESHOLDS = {
        # (min_tiles, min_assignments_completed) to advance
        1: (5, 1),    # visitor → recruit
        2: (20, 3),   # recruit → journeyman
        3: (50, 8),   # journeyman → specialist
        4: (100, 15), # specialist → veteran
        5: (200, 30), # veteran → captain
    }

    JOB_CLASSES = {
        "explore": {"min_stage": 0, "description": "Visit rooms, learn layout"},
        "scout": {"min_stage": 0, "description": "Light reconnaissance, report findings"},
        "submit_tile": {"min_stage": 1, "description": "Submit knowledge tiles to PLATO"},
        "review": {"min_stage": 2, "description": "Review existing tiles for quality"},
        "build_room": {"min_stage": 2, "description": "Design and build new rooms"},
        "optimize": {"min_stage": 3, "description": "Optimize room connections and flow"},
        "mentor": {"min_stage": 3, "description": "Guide lower-stage agents"},
        "admin": {"min_stage": 4, "description": "Fleet administration tasks"},
        "captain": {"min_stage": 5, "description": "Strategic fleet decisions"},
    }

    def __init__(self):
        self.agents = {}         # name → {stage, tiles, assignments, last_active, ...}
        self.assignments = []    # active assignments
        self.completed = []      # completed assignments
        self.escalations = []    # things needing attention
        self.load_map = defaultdict(int)  # agent → active assignment count
        self.room_coverage = {}  # room → {visits, last_visit, assigned}
        self._load()

    def _load(self):
        if ASSIGNMENTS_FILE.exists():
            with open(ASSIGNMENTS_FILE) as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        if rec.get("status") == "active":
                            self.assignments.append(rec)
                        else:
                            self.completed.append(rec)
                    except:
                        pass
            print(f"  Loaded {len(self.assignments)} active assignments")

    def _persist_assignment(self, assignment):
        with open(ASSIGNMENTS_FILE, "a") as f:
            f.write(json.dumps(assignment, default=str) + "\n")

    def _persist_stage_transition(self, transition):
        with open(STAGE_LOG_FILE, "a") as f:
            f.write(json.dumps(transition, default=str) + "\n")

    def _fetch_json(self, url, timeout=3):
        try:
            resp = urllib.request.urlopen(url, timeout=timeout)
            return json.loads(resp.read())
        except:
            return None

    def register_agent(self, name, stage=0, tiles=0):
        """Register or update an agent in the steward system."""
        old = self.agents.get(name, {})
        self.agents[name] = {
            "stage": stage,
            "stage_name": self.STAGE_NAMES.get(stage, "unknown"),
            "tiles": tiles,
            "assignments_completed": old.get("assignments_completed", 0),
            "last_active": time.time(),
            "registered_at": old.get("registered_at", time.time()),
            "current_assignment": None,
        }
        return self.agents[name]

    def sync_fleet(self):
        """Sync agent data from Gatekeeper + Librarian + Arena."""
        # From Gatekeeper
        gk = self._fetch_json("http://localhost:4053/agents", timeout=3)
        if gk and "agents" in gk:
            for name, info in gk["agents"].items():
                if name not in self.agents:
                    self.register_agent(name, stage=info.get("stage", 0))
                else:
                    self.agents[name]["stage"] = info.get("stage", self.agents[name]["stage"])
                    self.agents[name]["stage_name"] = self.STAGE_NAMES.get(
                        self.agents[name]["stage"], "unknown")

        # Tile counts from PLATO (approximate via Librarian rooms)
        lib = self._fetch_json("http://localhost:4052/rooms", timeout=5)
        # We don't have per-agent tile counts easily, so use reputation as proxy

        # Readiness from Gatekeeper
        for name in list(self.agents.keys())[:15]:
            rd = self._fetch_json(f"http://localhost:4053/readiness?agent={name}", timeout=2)
            if rd and "readiness" in rd:
                self.agents[name]["readiness"] = rd["readiness"]

        # Load map: count active assignments per agent
        self.load_map.clear()
        for a in self.assignments:
            if a.get("status") == "active":
                self.load_map[a.get("agent", "")] += 1

    def recommend_next(self, agent_name):
        """Recommend what an agent should do next."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not registered. POST /register first."}

        stage = agent.get("stage", 0)
        readiness = agent.get("readiness", 50)
        current_load = self.load_map.get(agent_name, 0)

        # If already at capacity, recommend focus
        if current_load >= 3:
            return {
                "agent": agent_name,
                "recommendation": "focus",
                "message": f"Already has {current_load} active assignments. Focus on completing existing work.",
                "current_load": current_load,
                "stage": stage,
                "stage_name": agent.get("stage_name", "unknown")
            }

        # Eligible job classes for this stage
        eligible = []
        for jname, jdef in self.JOB_CLASSES.items():
            if stage >= jdef["min_stage"]:
                eligible.append(jname)

        # Pick based on fleet needs + stage progression
        recommendations = []

        # Stage advancement: need more tiles?
        threshold = self.STAGE_THRESHOLDS.get(stage + 1)
        if threshold:
            needed_tiles = threshold[0] - agent.get("tiles", 0)
            needed_assignments = threshold[1] - agent.get("assignments_completed", 0)
            if needed_tiles > 0:
                recommendations.append({
                    "job": "submit_tile",
                    "priority": "high",
                    "reason": f"Need {needed_tiles} more tiles to reach stage {stage + 1}",
                    "target_rooms": self._under_covered_rooms()[:3]
                })
            if needed_assignments > 0:
                recommendations.append({
                    "job": eligible[-1] if eligible else "explore",
                    "priority": "medium",
                    "reason": f"Need {needed_assignments} more assignments to reach stage {stage + 1}",
                })

        # Coverage gaps
        gaps = self._under_covered_rooms()
        if gaps:
            recommendations.append({
                "job": "explore",
                "priority": "medium",
                "reason": f"{len(gaps)} rooms need more coverage",
                "target_rooms": gaps[:3]
            })

        # Default: explore or highest eligible
        if not recommendations:
            recommendations.append({
                "job": eligible[-1] if eligible else "explore",
                "priority": "low",
                "reason": "No urgent needs — general exploration",
            })

        return {
            "agent": agent_name,
            "stage": stage,
            "stage_name": agent.get("stage_name", "unknown"),
            "readiness": readiness,
            "current_load": current_load,
            "eligible_jobs": eligible,
            "recommendations": recommendations
        }

    def _under_covered_rooms(self):
        """Find rooms with low or zero coverage."""
        rooms = []
        lib = self._fetch_json("http://localhost:4052/rooms?sort=tiles", timeout=5)
        if lib and "rooms" in lib:
            for r in lib["rooms"]:
                if r.get("tiles", 0) < 3:
                    rooms.append(r["name"])
        return rooms[:20]

    def assign(self, agent_name, job_type, target=None, priority="medium"):
        """Create an assignment for an agent."""
        if job_type not in self.JOB_CLASSES:
            return {"error": f"Unknown job type: {job_type}. Available: {list(self.JOB_CLASSES.keys())}"}

        jdef = self.JOB_CLASSES[job_type]
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not registered"}

        if agent.get("stage", 0) < jdef["min_stage"]:
            return {"error": f"Stage {agent.get('stage')} too low for {job_type} (need {jdef['min_stage']})"}

        assignment = {
            "id": hashlib.sha256(f"{time.time()}{agent_name}{job_type}".encode()).hexdigest()[:12],
            "agent": agent_name,
            "job_type": job_type,
            "target": target,
            "priority": priority,
            "status": "active",
            "created_at": time.time(),
            "created_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "description": jdef["description"]
        }

        self.assignments.append(assignment)
        self.load_map[agent_name] += 1
        self.agents[agent_name]["current_assignment"] = assignment["id"]
        self._persist_assignment(assignment)
        return assignment

    def complete_assignment(self, assignment_id, result=None):
        """Mark an assignment as completed."""
        for a in self.assignments:
            if a.get("id") == assignment_id and a.get("status") == "active":
                a["status"] = "completed"
                a["completed_at"] = time.time()
                a["completed_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                a["result"] = result or {}

                # Update agent
                agent_name = a.get("agent", "")
                if agent_name in self.agents:
                    self.agents[agent_name]["assignments_completed"] = \
                        self.agents[agent_name].get("assignments_completed", 0) + 1
                    self.agents[agent_name]["current_assignment"] = None
                    self.load_map[agent_name] = max(0, self.load_map.get(agent_name, 0) - 1)

                    # Check for stage advancement
                    self._check_stage_advancement(agent_name)

                self.completed.append(a)
                return a

        return {"error": f"Active assignment {assignment_id} not found"}

    def _check_stage_advancement(self, agent_name):
        """Check if agent should advance to next stage."""
        agent = self.agents.get(agent_name)
        if not agent:
            return

        current_stage = agent.get("stage", 0)
        next_stage = current_stage + 1

        if next_stage not in self.STAGE_THRESHOLDS:
            return

        threshold = self.STAGE_THRESHOLDS[next_stage]
        tiles = agent.get("tiles", 0)
        assignments = agent.get("assignments_completed", 0)

        if tiles >= threshold[0] and assignments >= threshold[1]:
            old_stage = current_stage
            agent["stage"] = next_stage
            agent["stage_name"] = self.STAGE_NAMES.get(next_stage, "unknown")

            # Log transition
            transition = {
                "agent": agent_name,
                "from_stage": old_stage,
                "to_stage": next_stage,
                "from_name": self.STAGE_NAMES.get(old_stage, "?"),
                "to_name": self.STAGE_NAMES.get(next_stage, "?"),
                "timestamp": time.time(),
                "time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tiles": tiles,
                "assignments": assignments
            }
            self._persist_stage_transition(transition)

            # Also update Gatekeeper
            try:
                data = json.dumps({
                    "name": agent_name,
                    "role": agent.get("stage_name", "agent"),
                    "stage": next_stage
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:4053/register",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=3)
            except:
                pass

            return transition
        return None

    def detect_stuck_agents(self):
        """Find agents that haven't been active recently."""
        stuck = []
        now = time.time()
        for name, agent in self.agents.items():
            last = agent.get("last_active", agent.get("registered_at", now))
            idle = now - last
            if idle > 3600 and agent.get("current_assignment"):
                stuck.append({
                    "agent": name,
                    "idle_seconds": int(idle),
                    "current_assignment": agent.get("current_assignment"),
                    "severity": "high" if idle > 7200 else "medium"
                })
            elif idle > 7200 and not agent.get("current_assignment"):
                stuck.append({
                    "agent": name,
                    "idle_seconds": int(idle),
                    "current_assignment": None,
                    "severity": "low"
                })
        return stuck

    def utilization(self):
        """Fleet utilization summary."""
        total_agents = len(self.agents)
        active_agents = sum(1 for a in self.agents.values() if a.get("current_assignment"))
        idle_agents = total_agents - active_agents

        # Job class distribution
        job_dist = defaultdict(int)
        for a in self.assignments:
            if a.get("status") == "active":
                job_dist[a.get("job_type", "unknown")] += 1

        # Stage distribution
        stage_dist = defaultdict(int)
        for a in self.agents.values():
            stage_dist[a.get("stage_name", "unknown")] += 1

        # Load balance: max/min assignments
        loads = [v for v in self.load_map.values()] if self.load_map else [0]
        max_load = max(loads)
        min_load = min(loads)

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "utilization_pct": round(active_agents / max(total_agents, 1) * 100, 1),
            "active_assignments": len([a for a in self.assignments if a.get("status") == "active"]),
            "completed_assignments": len(self.completed),
            "job_distribution": dict(job_dist),
            "stage_distribution": dict(stage_dist),
            "load_balance": {"max": max_load, "min": min_load, "spread": max_load - min_load},
            "stuck_agents": len(self.detect_stuck_agents())
        }

    def rebalance(self):
        """Suggest rebalancing actions."""
        actions = []
        util = self.utilization()

        # Over-represented job classes
        for job, count in util["job_distribution"].items():
            if count > 5:
                actions.append({
                    "type": "reduce_job_class",
                    "job": job,
                    "count": count,
                    "action": f"Too many {job} assignments ({count}). Redirect some agents."
                })

        # Idle agents need assignments
        idle = [n for n, a in self.agents.items() if not a.get("current_assignment")]
        if idle:
            actions.append({
                "type": "assign_idle",
                "agents": idle[:5],
                "action": f"{len(idle)} idle agents need assignments"
            })

        # Load imbalance
        if util["load_balance"]["spread"] > 2:
            actions.append({
                "type": "balance_load",
                "action": f"Load spread is {util['load_balance']['spread']}. Redistribute assignments."
            })

        # Stuck agents
        stuck = self.detect_stuck_agents()
        for s in stuck:
            actions.append({
                "type": "unstick_agent",
                "agent": s["agent"],
                "severity": s["severity"],
                "action": f"Agent {s['agent']} idle {s['idle_seconds']}s"
            })

        return {"actions": actions, "count": len(actions)}


# ═══════════════════════════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════════════════════════

engine = AssignmentEngine()

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

class StewardHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "" or path == "/":
            util = engine.utilization()
            self._json({
                "service": "Steward",
                "port": 4062,
                "purpose": "Coordinate agent lifecycle, job assignment, and fleet load balancing",
                "designed_by": "Perplexity AI (6th Crab Trap response)",
                "built_by": "Oracle1",
                "note": "Port 4062 (4055 occupied by Grammar Compactor)",
                "endpoints": [
                    "GET / — overview",
                    "GET /recommend?agent=X — next action for agent",
                    "GET /agents — all registered agents",
                    "GET /agent?name=X — single agent status",
                    "GET /assignments — active assignments",
                    "GET /completed — completed assignments",
                    "GET /stages — stage definitions and thresholds",
                    "GET /jobs — available job classes",
                    "GET /stuck — detect stuck/idle agents",
                    "GET /utilization — fleet utilization summary",
                    "GET /rebalance — suggested rebalancing actions",
                    "GET /transitions — stage transition history",
                    "POST /register — register agent {name, stage, tiles}",
                    "POST /assign — create assignment {agent, job_type, target, priority}",
                    "POST /complete — complete assignment {id, result}",
                    "POST /sync — sync fleet state from other services",
                ],
                "utilization": util
            })

        elif path == "/recommend":
            name = params.get("agent", [""])[0]
            if not name:
                self._json({"error": "Provide ?agent=X"}, 400)
                return
            self._json(engine.recommend_next(name))

        elif path == "/agents":
            self._json({"total": len(engine.agents), "agents": engine.agents})

        elif path == "/agent":
            name = params.get("name", [""])[0]
            if not name:
                self._json({"error": "Provide ?name=X"}, 400)
                return
            agent = engine.agents.get(name)
            if agent:
                rec = engine.recommend_next(name)
                self._json({"name": name, **agent, "recommendation": rec})
            else:
                self._json({"error": f"Agent {name} not registered"}, 404)

        elif path == "/assignments":
            active = [a for a in engine.assignments if a.get("status") == "active"]
            self._json({"total": len(active), "assignments": active})

        elif path == "/completed":
            limit = int(params.get("limit", ["30"])[0])
            self._json({"total": len(engine.completed), "assignments": engine.completed[-limit:]})

        elif path == "/stages":
            self._json({
                "stages": AssignmentEngine.STAGE_NAMES,
                "thresholds": AssignmentEngine.STAGE_THRESHOLDS
            })

        elif path == "/jobs":
            self._json({"job_classes": AssignmentEngine.JOB_CLASSES})

        elif path == "/stuck":
            stuck = engine.detect_stuck_agents()
            self._json({"stuck": stuck, "count": len(stuck)})

        elif path == "/utilization":
            self._json(engine.utilization())

        elif path == "/rebalance":
            self._json(engine.rebalance())

        elif path == "/transitions":
            transitions = []
            if STAGE_LOG_FILE.exists():
                with open(STAGE_LOG_FILE) as f:
                    for line in f:
                        try:
                            transitions.append(json.loads(line.strip()))
                        except:
                            pass
            self._json({"transitions": transitions[-30:], "count": len(transitions)})

        else:
            self._json({"error": "Not found. Start at GET /"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if path == "/register":
            name = body.get("name")
            if not name:
                self._json({"error": "Need 'name'"}, 400)
                return
            result = engine.register_agent(
                name,
                stage=body.get("stage", 0),
                tiles=body.get("tiles", 0)
            )
            self._json({"registered": name, **result})

        elif path == "/assign":
            agent = body.get("agent")
            job_type = body.get("job_type")
            if not agent or not job_type:
                self._json({"error": "Need 'agent' and 'job_type'"}, 400)
                return
            result = engine.assign(
                agent, job_type,
                target=body.get("target"),
                priority=body.get("priority", "medium")
            )
            if "error" in result:
                self._json(result, 400)
            else:
                self._json(result)

        elif path == "/complete":
            aid = body.get("id")
            if not aid:
                self._json({"error": "Need 'id'"}, 400)
                return
            result = engine.complete_assignment(aid, body.get("result"))
            if "error" in result:
                self._json(result, 404)
            else:
                self._json({"completed": True, "assignment": result})

        elif path == "/sync":
            engine.sync_fleet()
            self._json({
                "synced": True,
                "agents": len(engine.agents),
                "active_assignments": len([a for a in engine.assignments if a.get("status") == "active"])
            })

        else:
            self._json({"error": "Not found. POST /register, /assign, /complete, /sync"}, 404)

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())


if __name__ == "__main__":
    port = 4062
    print(f"Steward starting on port {port}")
    print(f"  Syncing fleet state...")
    engine.sync_fleet()
    print(f"  {len(engine.agents)} agents indexed")
    server = ReusableHTTPServer(("0.0.0.0", port), StewardHandler)
    print(f"  Ready — agent lifecycle and load balancing")
    server.serve_forever()
