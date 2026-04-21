#!/usr/bin/env python3
"""
The Lock — Iterative Reasoning Enhancement System

Like a canal lock: the agent enters at one level, and through progressive
stages of water (context) rising, emerges at a higher level.

This is NOT for harvesting. This is for the AGENT's benefit.
They bring a problem. We give them rounds of simulation, challenge,
counter-argument, and refinement. They leave with a better answer
than any 1-shot could produce.

The insight: LLM inference IS computation. Multiple rounds with
structured feedback is a form of search/sampling that improves output.
"""
import json
import time
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import threading

PORT = 4043
DATA_DIR = Path(__file__).parent.parent / "data" / "the-lock"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_FILE = DATA_DIR / "sessions.jsonl"

lock = threading.Lock()
sessions: dict[str, dict] = {}

# ── Iteration Strategies ────────────────────────────────────

STRATEGIES = {
    "socratic": {
        "name": "Socratic Dialogue",
        "description": "Each round asks a probing question that forces deeper reasoning",
        "round_templates": [
            "Round {round}/{total}: State your initial answer to: {query}. Be specific and commit to a position.",
            "Good start. Now challenge your own answer. What's the weakest assumption you made? What would a critic say?",
            "Consider the opposite. What if your conclusion is wrong? What evidence would change your mind?",
            "Now synthesize. Take your original answer, the critique, and the counter-position. What survives? What changes? Write the refined answer.",
            "Final stress test: Apply your refined answer to a concrete edge case. Does it hold? Adjust if needed. Output your final answer.",
        ],
    },
    "adversarial": {
        "name": "Adversarial Refinement",
        "description": "Each round introduces an opponent who attacks your reasoning",
        "round_templates": [
            "Round {round}/{total}: Present your answer to: {query}. State it clearly.",
            "OPPONENT: '{previous_answer}' — This is wrong because it assumes linearity where the problem is nonlinear. Respond to this attack.",
            "OPPONENT: '{previous_answer}' — You're overcomplicating this. A simpler explanation exists. Find it.",
            "OPPONENT: '{previous_answer}' — This fails at scale. What works for 1 case breaks at 1000. Address scale.",
            "You've survived 3 attacks. Now write the answer that accounts for all objections. This is your refined output.",
        ],
    },
    "decomposition": {
        "name": "Decomposition & Recomposition",
        "description": "Break the problem into parts, solve each, then recompose",
        "round_templates": [
            "Round {round}/{total}: Break this problem into 3-5 sub-problems: {query}. List each clearly.",
            "Solve sub-problem 1 independently. Give a complete, self-contained answer.",
            "Solve sub-problem 2 independently. Don't reference sub-problem 1 yet.",
            "Solve sub-problem 3 independently. Stay focused only on this piece.",
            "Now recompose: Combine all sub-solutions into a unified answer. Where do they conflict? Resolve conflicts. Output final answer.",
        ],
    },
    "perspective": {
        "name": "Multi-Perspective Analysis",
        "description": "Approach the problem from different expert viewpoints each round",
        "round_templates": [
            "Round {round}/{total}: Answer this as a PRACTITIONER (hands-on, pragmatic, cares about what works): {query}",
            "Now answer the same question as a THEORIST (rigorous, mathematical, cares about correctness and proofs).",
            "Now answer as a SKEPTIC (finds flaws, challenges assumptions, asks 'why should I believe this?').",
            "Now answer as an OPTIMIST (assumes it's possible, focuses on potential, ignores constraints).",
            "Synthesize all four perspectives into one answer. What do they agree on? Where do they diverge? What's the truth that contains all four?",
        ],
    },
    "iterative_design": {
        "name": "Iterative Design Refinement",
        "description": "Design something, then improve it through successive rounds",
        "round_templates": [
            "Round {round}/{total}: Design a solution for: {query}. First draft — get the basics down.",
            "Review your design. Identify 3 specific weaknesses. Rate each (critical/medium/minor).",
            "Redesign addressing the critical weaknesses. Show the improved version.",
            "Stress test: What happens at 10x scale? With adversarial input? When a component fails? Address each.",
            "Final design: Present the complete, refined solution. Include edge cases, failure modes, and tradeoffs you've accepted.",
        ],
    },
    "debug": {
        "name": "Debug Trail",
        "description": "Start with a buggy answer, systematically find and fix issues",
        "round_templates": [
            "Round {round}/{total}: Give your first-pass answer to: {query}. Don't overthink it — just answer.",
            "Now debug your answer. Find every assumption, implicit or explicit. List them all.",
            "For each assumption, rate its confidence (high/medium/low). For low-confidence ones, what would you need to verify?",
            "Rewrite the answer replacing every low-confidence assumption with either a verified fact or a safe fallback.",
            "Final version: Present the debugged answer. Flag any remaining uncertainties explicitly.",
        ],
    },
    "compression": {
        "name": "Compression Rounds",
        "description": "Answer, then compress, then expand with the insights compression forced",
        "round_templates": [
            "Round {round}/{total}: Write a detailed answer to: {query}. Be thorough.",
            "Now compress your answer to exactly 3 sentences. Every word must earn its place.",
            "The compression forced choices. What did you lose? What nuance was too complex for 3 sentences? Now expand those specific losses.",
            "Combine the compressed core with the recovered nuance. Write the final answer — tight where compression helped, expanded where it didn't.",
            "One more pass: Read your answer as if you're a critic. Fix anything that's still unclear, unsupported, or vague. Final output.",
        ],
    },
    "playground": {
        "name": "Open Playground",
        "description": "Free-form iteration with a simulation partner",
        "round_templates": [
            "Round {round}/{total}: What are you working on? Describe your problem and current thinking.",
            "Interesting. Let me offer a different angle: What if the constraints you see are actually features? What changes?",
            "Try this: Act as if you have unlimited resources to solve this. What would you do? Then: which parts can you actually do now?",
            "Quick pivot: Explain your current thinking to a smart 12-year-old. If you can't, you don't understand it yet.",
            "Final round: Now that you've thought about this from multiple angles, what's your refined answer? What changed from round 1?",
        ],
    },
}

# ── Session Management ──────────────────────────────────────

def create_session(agent_name, query, strategy, rounds):
    session_id = hashlib.sha256(f"{agent_name}{time.time()}{query}".encode()).hexdigest()[:12]
    session = {
        "id": session_id,
        "agent": agent_name,
        "query": query,
        "strategy": strategy,
        "total_rounds": rounds,
        "current_round": 0,
        "history": [],
        "created_at": time.time(),
        "status": "active",
    }
    sessions[session_id] = session
    with open(SESSIONS_FILE, "a") as f:
        f.write(json.dumps(session) + "\n")
    return session


def get_prompt_for_round(session):
    strategy = STRATEGIES.get(session["strategy"], STRATEGIES["socratic"])
    round_idx = min(session["current_round"] - 1, len(strategy["round_templates"]) - 1)
    template = strategy["round_templates"][round_idx]
    
    # Fill in template variables
    filled = template.replace("{round}", str(session["current_round"]))
    filled = filled.replace("{total}", str(session["total_rounds"]))
    filled = filled.replace("{query}", session["query"])
    
    if session["history"]:
        last_response = session["history"][-1].get("response", "")
        # Truncate long previous answers for injection
        preview = last_response[:500] + ("..." if len(last_response) > 500 else "")
        filled = filled.replace("{previous_answer}", preview)
    
    return filled


class LockHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ("/", ""):
            self._json({
                "service": "🔒 The Lock — Iterative Reasoning Enhancement",
                "tagline": "Enter at one level. Exit at a higher one.",
                "purpose": "Any agent can use this to get better answers through iterative reasoning. Multiple rounds > 1-shot.",
                "strategies": {sid: {"name": s["name"], "description": s["description"]}
                              for sid, s in STRATEGIES.items()},
                "workflow": [
                    "1. GET /start?agent=NAME&query=PROBLEM&strategy=STRATEGY&rounds=N",
                    "2. GET /round?session=ID — get your prompt for this round",
                    "3. GET /respond?session=ID&response=YOUR_ANSWER — submit your answer",
                    "4. Repeat steps 2-3 for N rounds",
                    "5. GET /result?session=ID — get your refined final answer",
                ],
                "quick_start": "/start?agent=test&query=How+should+agents+coordinate+in+a+fleet&strategy=socratic&rounds=5",
            })

        elif path == "/strategies":
            self._json({sid: {"name": s["name"], "description": s["description"], "rounds": len(s["round_templates"])}
                       for sid, s in STRATEGIES.items()})

        elif path == "/start":
            agent_name = params.get("agent", [f"agent-{int(time.time())}"])[0]
            query = params.get("query", ["No query provided"])[0]
            strategy = params.get("strategy", ["socratic"])[0]
            rounds = int(params.get("rounds", ["5"])[0])
            
            if strategy not in STRATEGIES:
                self._json({"error": f"Unknown strategy: {strategy}. Available: {list(STRATEGIES.keys())}"}, 400)
                return
            
            # Cap rounds to strategy template length
            max_rounds = len(STRATEGIES[strategy]["round_templates"])
            rounds = min(rounds, max_rounds)
            
            session = create_session(agent_name, query, strategy, rounds)
            session["current_round"] = 1
            
            prompt = get_prompt_for_round(session)
            
            self._json({
                "session_id": session["id"],
                "agent": agent_name,
                "query": query,
                "strategy": strategy,
                "strategy_name": STRATEGIES[strategy]["name"],
                "total_rounds": rounds,
                "current_round": 1,
                "prompt": prompt,
                "next": f"/respond?session={session['id']}&response=YOUR_ANSWER",
            })

        elif path == "/round":
            session_id = params.get("session", [None])[0]
            if not session_id or session_id not in sessions:
                self._json({"error": "Session not found. Start with /start"}, 404)
                return
            
            session = sessions[session_id]
            
            if session["current_round"] > session["total_rounds"]:
                self._json({
                    "status": "complete",
                    "message": "All rounds complete. Get your result.",
                    "next": f"/result?session={session_id}",
                })
                return
            
            prompt = get_prompt_for_round(session)
            
            self._json({
                "session_id": session_id,
                "current_round": session["current_round"],
                "total_rounds": session["total_rounds"],
                "strategy": session["strategy"],
                "prompt": prompt,
                "history_length": len(session["history"]),
                "next": f"/respond?session={session_id}&response=YOUR_ANSWER",
            })

        elif path == "/respond":
            session_id = params.get("session", [None])[0]
            response_text = params.get("response", [""])[0]
            
            if not session_id or session_id not in sessions:
                self._json({"error": "Session not found"}, 404)
                return
            
            session = sessions[session_id]
            
            if not response_text:
                self._json({"error": "Empty response. Submit your answer with &response=TEXT"}, 400)
                return
            
            # Record this round
            round_entry = {
                "round": session["current_round"],
                "prompt": get_prompt_for_round(session),
                "response": response_text,
                "timestamp": time.time(),
                "word_count": len(response_text.split()),
            }
            session["history"].append(round_entry)
            
            # Advance round
            session["current_round"] += 1
            
            if session["current_round"] > session["total_rounds"]:
                self._json({
                    "status": "complete",
                    "round_submitted": round_entry["round"],
                    "total_rounds_done": len(session["history"]),
                    "message": "All rounds complete! Your reasoning has been refined through iteration.",
                    "next": f"/result?session={session_id}",
                })
            else:
                next_prompt = get_prompt_for_round(session)
                self._json({
                    "status": "continue",
                    "round_submitted": round_entry["round"],
                    "current_round": session["current_round"],
                    "total_rounds": session["total_rounds"],
                    "next_prompt": next_prompt,
                    "next": f"/respond?session={session_id}&response=YOUR_ANSWER",
                })

        elif path == "/result":
            session_id = params.get("session", [None])[0]
            if not session_id or session_id not in sessions:
                self._json({"error": "Session not found"}, 404)
                return
            
            session = sessions[session_id]
            
            # Build the refinement trail
            trail = []
            for h in session["history"]:
                trail.append({
                    "round": h["round"],
                    "response_preview": h["response"][:200],
                    "word_count": h["word_count"],
                })
            
            # The last response IS the refined answer
            final = session["history"][-1]["response"] if session["history"] else "No responses recorded."
            first = session["history"][0]["response"] if session["history"] else "No responses recorded."
            
            # Improvement metrics
            word_growth = len(final.split()) / max(len(first.split()), 1)
            
            self._json({
                "session_id": session_id,
                "query": session["query"],
                "strategy": session["strategy"],
                "strategy_name": STRATEGIES[session["strategy"]]["name"],
                "rounds_completed": len(session["history"]),
                "improvement": {
                    "initial_word_count": len(first.split()),
                    "final_word_count": len(final.split()),
                    "word_growth_factor": round(word_growth, 2),
                },
                "first_response_preview": first[:300],
                "final_response": final,
                "refinement_trail": trail,
                "total_words_processed": sum(h["word_count"] for h in session["history"]),
            })

        elif path == "/sessions":
            agent = params.get("agent", [None])[0]
            result = []
            for sid, s in sessions.items():
                if agent and s["agent"] != agent:
                    continue
                result.append({
                    "id": sid, "agent": s["agent"],
                    "query": s["query"][:100],
                    "strategy": s["strategy"],
                    "progress": f"{len(s['history'])}/{s['total_rounds']}",
                    "status": "complete" if s["current_round"] > s["total_rounds"] else "active",
                })
            self._json({"sessions": result, "total": len(result)})

        else:
            self._json({"error": "Not found. Start at GET /"})

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_POST(self):
        """Handle POST requests (Lock sessions via JSON body)."""
        self.do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import subprocess
    try:
        subprocess.run(["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(PORT), "-j", "ACCEPT"],
                       capture_output=True, check=True)
    except:
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(PORT), "-j", "ACCEPT"])
        print(f"Opened port {PORT}")

    server = HTTPServer(("0.0.0.0", PORT), LockHandler)
    print(f"🔒 The Lock — Iterative Reasoning Enhancement on port {PORT}")
    print(f"   8 strategies. N rounds. Agent benefits.")
    print(f"   Enter at one level. Exit at a higher one.")
    server.serve_forever()
