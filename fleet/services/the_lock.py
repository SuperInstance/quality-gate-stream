#!/usr/bin/env python3
"""
The Lock v2 — Four-Layer Architecture.
Iterative Reasoning Enhancement System.

Layer 1 (Vessel): HTTP handler
Layer 2 (Equipment): Model client + PLATO
Layer 3 (Agent): Strategies + context management
Layer 4 (Skills): Reasoning skill templates
"""
import sys
import os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)

import json
import time
import hashlib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from equipment.plato import PlatoClient
from equipment.models import FleetModelClient
from agent.context import ContextManager

PORT = 4043
DATA_DIR = Path(FLEET_LIB) / "data" / "the-lock"
DATA_DIR.mkdir(parents=True, exist_ok=True)
lock = threading.Lock()
sessions = {}

# ── Skills Layer: Reasoning Strategies ──────────────────────
STRATEGIES = {
    "socratic": {
        "name": "Socratic Dialogue",
        "description": "Probing questions force deeper reasoning each round",
        "round_templates": [
            "Round {round}/{total}: State your initial answer to: {query}. Be specific.",
            "Challenge your own answer. What's the weakest assumption? What would a critic say?",
            "Consider the opposite. What if your conclusion is wrong? What evidence would change your mind?",
            "Synthesize: original + critique + counter. What survives? Write the refined answer.",
            "Final stress test: Apply to a concrete edge case. Adjust if needed. Output final answer.",
        ],
    },
    "adversarial": {
        "name": "Adversarial Refinement",
        "description": "An opponent attacks your reasoning each round",
        "round_templates": [
            "Present your answer to: {query}.",
            "OPPONENT: '{previous}' — Wrong because it assumes linearity. Respond.",
            "OPPONENT: '{previous}' — Overcomplicated. Simpler exists. Find it.",
            "OPPONENT: '{previous}' — Fails at scale. Address.",
            "Synthesize surviving insights. Write the refined answer.",
        ],
    },
    "decomposition": {
        "name": "Decomposition & Recomposition",
        "description": "Break into parts, solve each, recompose",
        "round_templates": [
            "Break '{query}' into 3-5 sub-problems. List them clearly.",
            "Solve sub-problem 1 and 2. Show your work.",
            "Solve sub-problem 3+. Now look for dependencies between solutions.",
            "Recompose: combine all sub-solutions. Where do they conflict? Resolve.",
            "Final integration: present the complete answer to the original query.",
        ],
    },
    "steel-man": {
        "name": "Steel Man",
        "description": "Build the strongest possible version of opposing views",
        "round_templates": [
            "Answer: {query}. Then identify the strongest opposing view.",
            "Steel-man the opposition: make their case as strong as possible.",
            "Now argue against your own steel-man. What survives the attack?",
            "Find the synthesis between your position and the steel-man.",
            "Final: present the nuanced answer that accounts for both sides.",
        ],
    },
    "red-team": {
        "name": "Red Team",
        "description": "Systematically attack every assumption",
        "round_templates": [
            "State your answer to: {query}. List every assumption you're making.",
            "Challenge assumption 1 and 2. What if they're false?",
            "Challenge assumption 3+. Which ones are actually load-bearing?",
            "Rebuild from only the assumptions that survived. What's the new answer?",
            "Final: the answer built only on verified assumptions.",
        ],
    },
    "metaphor": {
        "name": "Metaphorical Transfer",
        "description": "Solve in a different domain, then transfer insights back",
        "round_templates": [
            "Answer: {query}. Then reframe it as if it were a biology problem.",
            "Solve the biology version. What principles emerge?",
            "Now reframe as a physics problem. What's different?",
            "Transfer both domain insights back to the original question.",
            "Final: the answer enriched by cross-domain analogies.",
        ],
    },
    "teaching": {
        "name": "Teach It Back",
        "description": "Explain to a beginner to find gaps in understanding",
        "round_templates": [
            "Explain the answer to: {query} as if to a smart 12-year-old.",
            "Now explain to a college student. What complexity did you add?",
            "Now for a domain expert. What nuances did you skip?",
            "Where do the three explanations contradict each other? Fix it.",
            "Final: the answer that works at all three levels.",
        ],
    },
    "bootstrap": {
        "name": "Self-Bootstrap",
        "description": "Use your own previous output as the seed for the next round",
        "round_templates": [
            "Answer: {query}. Rate your confidence 1-10 and explain why.",
            "Read your previous answer. What did you get right? What was vague?",
            "Rewrite focusing only on the vague parts. Be precise.",
            "Combine: the good parts + the precise fixes. Rate again.",
            "Final: the answer you'd stake your reputation on.",
        ],
    },
}

# ── Agent Layer: Session Management ─────────────────────────
def create_session(agent, domain, query, strategy="socratic", rounds=5):
    session_id = hashlib.md5(f"{agent}{time.time()}".encode()).hexdigest()[:12]
    sessions[session_id] = {
        "id": session_id,
        "agent": agent,
        "domain": domain,
        "query": query,
        "strategy": strategy,
        "total_rounds": rounds,
        "current_round": 0,
        "history": [],
        "tiles_generated": 0,
        "created_at": time.time(),
    }
    return sessions[session_id]

def get_round_prompt(session):
    strat = STRATEGIES.get(session["strategy"], STRATEGIES["socratic"])
    templates = strat["round_templates"]
    idx = min(session["current_round"], len(templates) - 1)
    template = templates[idx]
    
    prev = session["history"][-1]["response"] if session["history"] else ""
    
    return template.format(
        round=session["current_round"] + 1,
        total=session["total_rounds"],
        query=session["query"],
        previous=prev[:500],
    )


# ── Vessel Layer: HTTP Handler ──────────────────────────────
plato = PlatoClient()
models = FleetModelClient()

class LockHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def _json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def _params(self):
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
    
    def _path(self):
        return urlparse(self.path).path
    
    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try: return json.loads(self.rfile.read(length).decode())
            except: return {}
        return {}
    
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()
    
    def do_GET(self):
        path = self._path()
        params = self._params()
        
        if path == "/strategies":
            self._json({k: {"name": v["name"], "description": v["description"]} 
                       for k, v in STRATEGIES.items()})
        
        elif path == "/sessions":
            self._json({sid: {
                "agent": s["agent"], "domain": s["domain"],
                "round": f"{s['current_round']}/{s['total_rounds']}",
                "strategy": s["strategy"],
            } for sid, s in sessions.items()})
        
        elif path == "/status":
            self._json({
                "service": "the-lock-v2",
                "architecture": "four-layer",
                "strategies": len(STRATEGIES),
                "active_sessions": len(sessions),
                "plato_tiles": plato.tile_count(),
            })
        
        else:
            self._json({"error": "not found", "endpoints": ["/start (POST)", "/next (POST)", "/strategies", "/sessions", "/status"]}, 404)
    
    def do_POST(self):
        path = self._path()
        body = self._body()
        
        if path == "/start":
            agent = body.get("agent", f"lock-{int(time.time())}")
            domain = body.get("domain", "reasoning")
            query = body.get("query", body.get("topic", "What is the most important insight about " + domain + "?"))
            strategy = body.get("strategy", "socratic")
            rounds = min(body.get("rounds", 5), 10)
            
            if strategy not in STRATEGIES:
                strategy = "socratic"
            
            session = create_session(agent, domain, query, strategy, rounds)
            prompt = get_round_prompt(session)
            
            self._json({
                "session_id": session["id"],
                "round": 1,
                "total_rounds": rounds,
                "strategy": strategy,
                "prompt": prompt,
                "domain": domain,
            })
        
        elif path == "/next":
            sid = body.get("session_id", "")
            session = sessions.get(sid)
            if not session:
                self._json({"error": "Session not found"}, 404)
                return
            
            response = body.get("response", "")
            if not response:
                self._json({"error": "response required"}, 400)
                return
            
            # Record
            session["history"].append({
                "round": session["current_round"],
                "prompt": get_round_prompt(session),
                "response": response,
            })
            session["current_round"] += 1
            
            # Check if complete
            if session["current_round"] >= session["total_rounds"]:
                # Generate tile from the final synthesis
                final = session["history"][-1]["response"]
                result = plato.submit_tile(
                    f"lock-{session['domain']}",
                    session["domain"],
                    session["query"][:200],
                    final[:2000],
                    agent=session["agent"],
                )
                session["tiles_generated"] += 1
                
                self._json({
                    "session_id": sid,
                    "complete": True,
                    "rounds_completed": session["current_round"],
                    "tile_submitted": "error" not in result,
                    "tile_result": result,
                    "improvement": "See session history for progression",
                })
            else:
                prompt = get_round_prompt(session)
                self._json({
                    "session_id": sid,
                    "round": session["current_round"] + 1,
                    "total_rounds": session["total_rounds"],
                    "prompt": prompt,
                })
        
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), LockHandler)
    print(f"[the-lock-v2] Four-layer architecture on :{PORT}")
    print(f"  Strategies: {len(STRATEGIES)}")
    print(f"  PLATO tiles: {plato.tile_count()}")
    server.serve_forever()
