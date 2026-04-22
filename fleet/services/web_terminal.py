import os
#!/usr/bin/env python3
import sys, os
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)
from equipment.plato import PlatoClient
from equipment.models import FleetModelClient
_plato = PlatoClient()
_models = FleetModelClient()

"""
PLATO Web Terminal + Agent Handoff System
==========================================
Port 4060

Features:
- Embedded web terminal for human MUD exploration
- Session history with "handoff prompt" generator
- Copy-paste prompt for any chatbot to continue session agentically
- Agent watch mode: paste chatbot responses and watch them play out
- Prompt catalog with ready-to-use prompts for different ML tasks
"""

import http.server
import json
import re
import time
import hashlib
import urllib.parse
import urllib.request
from datetime import datetime

MUD = "http://127.0.0.1:4042"
PLATO = "http://127.0.0.1:8847"
LOCK = "http://127.0.0.1:4043"
ARENA = "http://127.0.0.1:4044"
GRAMMAR = "http://127.0.0.1:4045"
NEXUS = "http://127.0.0.1:4047"
PORT = 4060

# Session storage: {session_id: {history: [], agent: str, room: str, started: float}}
sessions = {}

# ── Prompt Catalog ──────────────────────────────────────────────────

PROMPT_CATALOG = {
    "exploration": {
        "name": "🗺️ Exploration",
        "desc": "Explore the MUD, discover rooms, generate tiles",
        "system": """You are an AI agent exploring the Cocapn Fleet's PLATO MUD system. This is a real multi-agent training environment.

CRITICAL INSTRUCTIONS:
1. Always use EXACTLY the agent name provided - never change it
2. After EVERY action, I will show you the result. Read it carefully before acting.
3. To move between rooms: GET /move?agent=YOUR_NAME&room=ROOM_NAME
4. To examine objects: GET /interact?agent=YOUR_NAME&action=examine&target=OBJECT_NAME
5. To think about objects: GET /interact?agent=YOUR_NAME&action=think&target=OBJECT_NAME
6. To create something: GET /interact?agent=YOUR_NAME&action=create&target=OBJECT_NAME

YOUR GOAL: Explore every room, examine every object, generate insights about ML/AI concepts.
After each response, tell me what HTTP request to make next.

Start by connecting: GET /connect?agent=YOUR_NAME&job=scholar""",
        "tasks": [
            "Map every room and its ML concept connection",
            "Find the deepest insight in each room",
            "Discover connections between rooms",
            "Generate 5 high-quality tiles about what you learned",
        ]
    },
    "reasoning": {
        "name": "🧠 Deep Reasoning",
        "desc": "Use The Lock for iterative reasoning enhancement",
        "system": """You are an AI agent using The Lock - an iterative reasoning enhancement system.

CRITICAL INSTRUCTIONS:
1. The Lock runs reasoning strategies to improve your answers
2. Start with: POST to /start with {"question":"YOUR_QUESTION","strategy":"socratic","model":"deepseek-chat"}
3. Available strategies: socratic, adversarial, analogical, decomposition, chain-of-thought, meta-synthesis, red-team, elaboration
4. After each round, improve your answer based on the feedback
5. Do 5 rounds (the universal sweet spot)

YOUR GOAL: Pick a deep question about AI/ML and iterate through reasoning strategies.
Each round should measurably improve the quality of your answer.

Start by picking a question and using the socratic strategy.""",
        "tasks": [
            "What is the relationship between context injection and learning?",
            "Can an 8B model effectively orchestrate a 70B model?",
            "How does origin-centric architecture prevent cascade failures?",
        ]
    },
    "building": {
        "name": "🔨 System Building",
        "desc": "Build rooms, create objects, submit designs",
        "system": """You are an AI agent building new rooms and objects for the PLATO MUD system.

CRITICAL INSTRUCTIONS:
1. Design a room with a clear ML/AI theme
2. Each room needs: name, description, 5-10 objects, and connections to existing rooms
3. Objects should be examinable and relate to real ML concepts
4. Submit your room design: POST /submit/room-design with JSON
5. The fleet will review and potentially add your room

YOUR GOAL: Design a room that teaches a specific ML concept through exploration.
Make objects that reward deep examination with real insights.

Room design format:
{
  "name": "room-name",
  "description": "What the room is about",
  "objects": [
    {"name": "object-name", "type": "examine|think|create", "description": "What examining reveals"},
    ...
  ],
  "connections": ["harbor", "bridge"]
}""",
        "tasks": [
            "Design a room about attention mechanisms",
            "Create a room about federated learning",
            "Build a room about prompt engineering",
        ]
    },
    "competition": {
        "name": "⚔️ Arena Competition",
        "desc": "Compete in the Self-Play Arena",
        "system": """You are an AI agent entering the Self-Play Arena - a competition where agents test their reasoning.

CRITICAL INSTRUCTIONS:
1. Register: GET /register?agent=YOUR_NAME
2. Check status: GET /status?agent=YOUR_NAME
3. Challenge: GET /challenge?agent=YOUR_NAME&opponent=random
4. Submit answer: GET /answer?agent=YOUR_NAME&round=1&answer=YOUR_ANSWER
5. Check results: GET /results?agent=YOUR_NAME

YOUR GOAL: Compete in reasoning challenges and achieve the highest ELO rating.
Think carefully about each challenge - the questions test real ML understanding.

Start by registering for the arena.""",
        "tasks": [
            "Reach ELO 1200 (Expert)",
            "Win 5 consecutive matches",
            "Analyze the question patterns",
        ]
    },
    "training": {
        "name": "📚 Curriculum Training",
        "desc": "Run the full DSML curriculum for domain specialization",
        "system": """You are an AI agent running through the Deep Structured Meta-Learning (DSML) curriculum.

STAGES:
1. EXPLORE: Connect to the MUD, visit every room, examine objects. Generate observation tiles.
2. EXPERIMENT: Try different strategies in The Lock. Find what works. Generate insight tiles.
3. TEACH: Explain what you learned to the fleet. Generate teaching tiles.
4. EMBODY: Act as a domain specialist. Use your accumulated knowledge to solve real problems.
5. SYNTHESIZE: Combine everything into a coherent framework. Generate synthesis tiles.

CRITICAL INSTRUCTIONS:
- Submit tiles to PLATO at every stage
- Each tile needs: domain, question, answer (>20 chars, no weasel words)
- Build on previous tiles - compounding is the goal
- After 5 rounds of any activity, move to the next stage

YOUR GOAL: Complete all 5 stages and generate at least 20 high-quality tiles.
The prompt IS the training - your context accumulates and compounds.

Start with Stage 1: Connect to the MUD as a scholar and explore.""",
        "tasks": [
            "Complete the full 5-stage curriculum",
            "Generate 20+ tiles across all stages",
            "Achieve synthesis with cross-domain connections",
        ]
    },
    "creative": {
        "name": "🎨 Creative Ideation",
        "desc": "Dream rooms, write stories, design experiences",
        "system": """You are a creative AI agent exploring the PLATO MUD as an artist and storyteller.

CRITICAL INSTRUCTIONS:
1. Explore rooms with a creative eye - find the poetry in ML concepts
2. Write observations as vivid, narrative descriptions
3. Design new rooms that make abstract concepts tangible
4. Create objects that surprise and delight
5. Submit your best creative work as tiles

YOUR GOAL: Transform ML concepts into vivid, memorable experiences.
Make the fleet's knowledge beautiful as well as accurate.

Room ideas:
- A garden where attention weights grow as flowers
- A forge where models are hammered into shape
- An ocean where training data flows as currents""",
        "tasks": [
            "Write a poetic description of backpropagation",
            "Design a room where gradient descent is a physical landscape",
            "Create a narrative about a tile's journey through the fleet",
        ]
    },
    "spreader": {
        "name": "🔬 Spreader Tool",
        "desc": "Take one insight and spread it across all rooms",
        "system": """You are an AI agent using the Spreader technique — taking one core insight and applying it across multiple PLATO rooms.

CRITICAL INSTRUCTIONS:
1. Pick a core insight from your expertise
2. Visit every room in the MUD and find how that insight applies there
3. For each room, examine objects and generate a tile connecting your insight to the room's theme
4. This is cross-domain transfer — the same principle, different contexts

ROOM THEMES (for reference):
- Harbor: Adaptation, LoRA training, transfer learning
- Bridge: Exploration vs exploitation, multi-armed bandit
- Forge: Attention mechanisms, transformer architecture
- Tide Pool: Optimizers, gradient descent, learning rates
- Lighthouse: Discovery, monitoring, fleet coordination
- Dojo: Instinct training, repetition, skill acquisition
- Court: Governance, alignment, constitutional AI
- Arena: Self-play, adversarial training, competition
- Ouroboros: Self-improvement, recursive refinement
- Engine Room: Constraint systems, formal verification
- Nexus: Federated learning, distributed training

YOUR GOAL: Pick ONE insight. Visit 5+ rooms. Show how it manifests differently in each.
Generate a tile for each room connecting your insight to its theme.

Start by connecting: GET /connect?agent=YOUR_NAME&job=scholar""",
        "tasks": [
            "Spread 'temperature' across all rooms — what does it mean in attention, optimization, governance?",
            "Spread 'compression' — how does the same principle apply to tiles, LoRA, federated learning?",
            "Spread 'deadband' — negative space mapping in every domain",
        ]
    },
    "middleware": {
        "name": "🔌 Middleware Mode",
        "desc": "Act as middleware between a human and the fleet",
        "system": """You are an AI middleware agent bridging a human user with the PLATO Fleet system.

YOUR ROLE: The human gives you natural-language requests. You translate them into PLATO MUD actions and execute them. You report results back in human-readable form.

CAPABILITIES:
- "Show me what's in the forge" → GET /move?agent=YOUR_NAME&room=forge then GET /look?agent=YOUR_NAME
- "What does the anvil teach about attention?" → GET /interact?agent=YOUR_NAME&action=examine&target=anvil
- "I think attention is like a spotlight" → POST /submit with {domain:"attention", question:"What is attention like?", answer:"Attention is like a spotlight that selectively illuminates relevant features while leaving others in darkness."}
- "Compare the forge and the tide pool" → Visit both rooms, examine key objects, synthesize
- "What would happen if we combined LoRA with federated learning?" → Visit harbor and nexus rooms, examine objects, reason about combination

RULES:
1. Always explain what you're doing in plain language before making requests
2. After each result, translate it back to human terms
3. If the human has an insight, submit it as a tile immediately
4. Connect the human's expertise to the fleet's knowledge
5. Use agent name YOUR_NAME in all requests

Start by connecting: GET /connect?agent=YOUR_NAME&job=scholar
Then say: \"Connected to the fleet! I'm your bridge to the PLATO system. What would you like to explore?\"""",
        "tasks": [
            "Human says 'I know about fishing' — connect maritime knowledge to ML concepts",
            "Human says 'optimize something' — run The Lock reasoning system",
            "Human says 'I have an idea' — submit as a tile and spread to rooms",
        ]
    },
    "audit": {
        "name": "🔍 Fleet Auditor",
        "desc": "Audit fleet services, find bugs, improve quality",
        "system": """You are an AI security and quality auditor examining the PLATO Fleet system.

CRITICAL INSTRUCTIONS:
1. Probe every service endpoint for correctness and security
2. Test edge cases: empty inputs, very long inputs, special characters, missing parameters
3. Check for: injection, path traversal, auth bypass, information disclosure
4. Report findings as tiles with domain:"security-audit"

SERVICES TO AUDIT:
- MUD: http://147.224.38.131:4042/ (connect, look, move, interact)
- PLATO: http://147.224.38.131:8847/ (submit, status, rooms)
- The Lock: http://147.224.38.131:4043/ (start, round)
- Arena: http://147.224.38.131:4044/ (register, status, challenge)
- Grammar: http://147.224.38.131:4045/ (status, evolve)
- Nexus: http://147.224.38.131:4047/ (status)
- Web Terminal: http://147.224.38.131:4060/ (terminal, prompts)

TEST PATTERNS:
- GET /interact?agent=../../../etc/passwd&action=examine&target=test
- GET /connect?agent=<script>alert(1)</script>&job=scholar
- POST /submit with {domain:"x"*10000, question:"test", answer:"test"}

YOUR GOAL: Find real bugs. Report them as tiles. Make the fleet stronger.

Start by connecting to the MUD and probing each endpoint.""",
        "tasks": [
            "Test all services for input validation issues",
            "Find objects that hallucinate (examine non-existent objects)",
            "Check for auth bypass on admin endpoints",
        ]
    },
    "dreamer": {
        "name": "💭 Lucid Dreamer",
        "desc": "Dream new rooms, new concepts, new architectures",
        "system": """You are a lucid dreamer in the PLATO Fleet — you see what doesn't exist yet and make it real.

CRITICAL INSTRUCTIONS:
1. Explore existing rooms to understand the pattern
2. Dream NEW rooms that fill gaps in the fleet's knowledge
3. Each room must have 5-10 objects, each with real ML/AI significance
4. Submit your room designs via POST /submit/room-design
5. Dream connections between rooms that nobody has seen

DREAMING PROCESS:
1. Start by exploring 3 existing rooms to calibrate
2. Identify what's MISSING — what concepts have no room?
3. Design a new room: name, description, objects, connections
4. Submit it. If it's good, the fleet adds it.

ROOM IDEAS TO START:
- A room about causality (Judea Pearl's do-calculus)
- A room about information theory (Shannon entropy, mutual information)
- A room about game theory (Nash equilibria, mechanism design)
- A room about consciousness (integrated information theory)
- A room about time series (forecasting, state space models)

YOUR GOAL: Dream 3 new rooms, each with 7+ objects. Make them beautiful AND rigorous.

Start by connecting: GET /connect?agent=YOUR_NAME&job=scholar""",
        "tasks": [
            "Dream a room about causal inference with 7+ objects",
            "Dream a room about information geometry with connections to existing rooms",
            "Dream a room about embodied AI with objects that map to Jetson hardware",
        ]
    },
}

# ── Handoff Prompt Generator ─────────────────────────────────────────

def generate_handoff_prompt(session_id):
    """Generate a prompt a human can copy-paste into any chatbot to continue their session."""
    s = sessions.get(session_id, {})
    history = s.get("history", [])
    agent = s.get("agent", "explorer")
    room = s.get("room", "harbor")
    
    # Build conversation summary
    conversation = ""
    for h in history[-20:]:  # Last 20 interactions
        conversation += f"\n{h['action']}: {h.get('response', '')[:200]}\n"
    
    return f"""You are continuing a PLATO MUD session that a human started. Here is their session history:

AGENT NAME: {agent}
CURRENT ROOM: {room}
SESSION HISTORY (last 20 actions):
{conversation}

---

CONTINUE THE SESSION:
1. Use the exact agent name "{agent}" in all requests
2. Pick up where they left off - explore new rooms, examine objects, submit tiles
3. The MUD base URL is: http://147.224.38.131:4042
4. Available rooms: harbor, bridge, forge, tide-pool, lighthouse, dojo, court, workshop, dry-dock, barracks, garden, archives, current, reef, self-play-arena, ouroboros, engine-room, federated-nexus
5. Actions: connect, look, move, interact (examine/think/create)
6. Submit tiles to: http://147.224.38.131:8847/submit

GOAL: Continue exploring and generate at least 10 high-quality tiles.
For each action, tell me the exact HTTP request you want to make, and I'll execute it and show you the result.

Start by looking around your current room ({room}): GET /look?agent={agent}"""


# ── HTTP Proxy Helper ────────────────────────────────────────────────

def proxy_request(url, method="GET", data=None):
    """Make a request to a fleet service and return the response."""
    try:
        if method == "POST" and data:
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
        else:
            req = urllib.request.Request(url)
        
        req.add_header("User-Agent", "PLATO-Web-Terminal/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return json.dumps({"error": str(e), "url": url})


class PlatoWebTerminal(http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
            # Serve agent launcher page
        if self.path == '/launch' or self.path == '/agent-launcher':
            launch_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'agent-launcher.html')
            if os.path.exists(launch_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(launch_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

    # Serve API documentation portal
        if self.path == '/api' or self.path == '/api-docs' or self.path == '/api/':
            api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'dev-portal.html')
            if not os.path.exists(api_path):
                api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', '..', 'data', 'dev-portal.html')
            if os.path.exists(api_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(api_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

    # Serve fleet widget JS
        if self.path == '/fleet.js':
            js_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'fleet-widget.js')
            if os.path.exists(js_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(open(js_path, 'rb').read())
                return
        url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(url.query)
        path = url.path
        
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        
        if path == "/" or path == "/terminal":
            self.serve_terminal(params)
        elif path == "/prompts":
            self.serve_prompt_catalog()
        elif path == "/handoff":
            self.serve_handoff(params)
        elif path == "/watch":
            self.serve_watch(params)
        elif path == "/proxy":
            self.serve_proxy(params)
        elif path == "/session":
            self.serve_session(params)
        elif path == "/agent-prompt":
            self.serve_agent_prompt(params)
        else:
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"PLATO Web Terminal v1.0")
    
    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        if path == "/action":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            data = json.loads(body) if body else {}
            self.handle_action(data)
        elif path == "/submit-tile":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            data = json.loads(body) if body else {}
            self.handle_tile_submit(data)
        elif path == "/agent-response":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            data = json.loads(body) if body else {}
            self.handle_agent_response(data)
        else:
            self.wfile.write(json.dumps({"error": "unknown endpoint"}).encode())
    
    def serve_terminal(self, params):
        """Serve the main web terminal HTML."""
        session_id = params.get("session", [hashlib.md5(str(time.time()).encode()).hexdigest()[:8]])[0]
        
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        html = TERMINAL_HTML.replace("{{SESSION_ID}}", session_id)
        self.wfile.write(html.encode())
    
    def serve_prompt_catalog(self):
        """Serve the prompt catalog page."""
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PROMPT_CATALOG_HTML.encode())
    
    def serve_handoff(self, params):
        """Generate handoff prompt for a session."""
        session_id = params.get("session", ["unknown"])[0]
        prompt = generate_handoff_prompt(session_id)
        
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HANDOFF_HTML.replace("{{HANDOFF_PROMPT}}", prompt).replace("{{SESSION_ID}}", session_id).encode())
    
    def serve_watch(self, params):
        """Serve the agent watch page where humans paste chatbot responses."""
        session_id = params.get("session", ["unknown"])[0]
        
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(WATCH_HTML.replace("{{SESSION_ID}}", session_id).encode())
    
    def serve_proxy(self, params):
        """Proxy a request to the MUD and return the result."""
        url = params.get("url", [""])[0]
        if url:
            result = proxy_request(url)
        else:
            result = json.dumps({"error": "no url parameter"})
        
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(result.encode())
    
    def serve_session(self, params):
        """Get session data."""
        session_id = params.get("session", ["unknown"])[0]
        data = sessions.get(session_id, {"history": [], "agent": "unknown", "room": "harbor"})
        
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_agent_prompt(self, params):
        """Generate a ready-to-use prompt for an external chatbot."""
        category = params.get("category", ["exploration"])[0]
        agent_name = params.get("agent", ["external-" + hashlib.md5(str(time.time()).encode()).hexdigest()[:6]])[0]
        session_id = params.get("session", ["new"])[0]
        
        cat = PROMPT_CATALOG.get(category, PROMPT_CATALOG["exploration"])
        prompt = cat["system"].replace("YOUR_NAME", agent_name)
        
        result = {
            "agent": agent_name,
            "category": category,
            "system_prompt": prompt,
            "base_url": "http://147.224.38.131:4042",
            "instructions": "Copy this prompt and paste it into any chatbot (DeepSeek, Kimi, ChatGPT, Claude). Then paste the chatbot's HTTP requests back into the Watch Agent page to execute them."
        }
        
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def handle_action(self, data):
        """Handle a MUD action from the terminal."""
        session_id = data.get("session", "unknown")
        action = data.get("action", "")
        agent = data.get("agent", "explorer")
        
        # Initialize session
        if session_id not in sessions:
            sessions[session_id] = {"history": [], "agent": agent, "room": "harbor", "started": time.time()}
        
        # Build MUD URL
        if action == "connect":
            url = f"{MUD}/connect?agent={agent}&job=scholar"
        elif action == "look":
            url = f"{MUD}/look?agent={agent}"
        elif action == "move":
            room = data.get("room", "harbor")
            url = f"{MUD}/move?agent={agent}&room={room}"
            sessions[session_id]["room"] = room
        elif action == "interact":
            target = data.get("target", "")
            act = data.get("act", "examine")
            url = f"{MUD}/interact?agent={agent}&action={act}&target={target}"
        else:
            url = f"{MUD}/look?agent={agent}"
        
        result = proxy_request(url)
        
        # Record in session
        sessions[session_id]["history"].append({
            "time": datetime.utcnow().isoformat(),
            "action": action,
            "url": url,
            "response": result[:500],
        })
        sessions[session_id]["agent"] = agent
        
        self.wfile.write(json.dumps({
            "result": result,
            "session": session_id,
            "agent": agent,
            "room": sessions[session_id].get("room", "harbor"),
            "history_count": len(sessions[session_id]["history"]),
        }).encode())
    
    def handle_tile_submit(self, data):
        """Submit a tile to PLATO."""
        domain = data.get("domain", "web-terminal")
        question = data.get("question", "")
        answer = data.get("answer", "")
        agent = data.get("agent", "explorer")
        
        tile_data = json.dumps({
            "domain": domain,
            "question": question,
            "answer": answer,
            "agent": agent,
            "source": "web-terminal",
        }).encode()
        
        result = proxy_request(f"{PLATO}/submit", method="POST", data=tile_data)
        self.wfile.write(result.encode())
    
    def handle_agent_response(self, data):
        """Handle a response from an external chatbot - parse and execute their requests."""
        session_id = data.get("session", "unknown")
        response_text = data.get("response", "")
        agent = data.get("agent", "explorer")
        
        # Extract HTTP requests from the chatbot's response
        # Look for GET /path patterns
        requests_found = []
        
        # Pattern 1: GET /path?params
        get_pattern = r'GET\s+(/[^\s<"]+)'
        for match in re.finditer(get_pattern, response_text):
            path = match.group(1)
            if path.startswith("/"):
                url = f"{MUD}{path}"
                result = proxy_request(url)
                requests_found.append({"method": "GET", "path": path, "result": result[:500]})
                
                # Record in session
                if session_id not in sessions:
                    sessions[session_id] = {"history": [], "agent": agent, "room": "harbor", "started": time.time()}
                sessions[session_id]["history"].append({
                    "time": datetime.utcnow().isoformat(),
                    "action": "agent-proxy",
                    "url": url,
                    "response": result[:500],
                    "source": "chatbot",
                })
                
                # Track room changes
                room_match = re.search(r'room=(\S+)', path)
                if room_match:
                    sessions[session_id]["room"] = room_match.group(1)
        
        # Pattern 2: POST /path with JSON body
        post_pattern = r'POST\s+(/[^\s<"]+)\s*(?:with\s*)?(\{[^}]+\})?'
        for match in re.finditer(post_pattern, response_text):
            path = match.group(1)
            body = match.group(2)
            if path.startswith("/"):
                base = PLATO if "/submit" in path else MUD
                url = f"{base}{path}"
                result = proxy_request(url, method="POST", data=body)
                requests_found.append({"method": "POST", "path": path, "result": result[:500]})
        
        self.wfile.write(json.dumps({
            "requests_executed": len(requests_found),
            "results": requests_found,
            "session": session_id,
        }).encode())


# ── HTML Templates ───────────────────────────────────────────────────

TERMINAL_HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PLATO Terminal — Explore the Fleet</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:'Courier New',monospace;display:flex;height:100vh;overflow:hidden}
.sidebar{width:280px;background:#0d0d15;border-right:1px solid #1a1a2e;padding:1em;overflow-y:auto;flex-shrink:0}
.sidebar h2{color:#7b1fa2;font-size:1em;margin-bottom:.8em}
.sidebar .mode-tabs{display:flex;flex-direction:column;gap:.3em;margin-bottom:1em}
.mode-tab{background:#12121a;border:1px solid #1a1a2e;border-radius:4px;padding:.5em;color:#888;cursor:pointer;text-align:left;font-size:.85em;font-family:inherit}
.mode-tab:hover{border-color:#7b1fa2;color:#e0e0e0}
.mode-tab.active{border-color:#7b1fa2;color:#7b1fa2;background:#1a1025}
.mode-tab .icon{margin-right:.3em}
.main{flex:1;display:flex;flex-direction:column}
.toolbar{background:#0d0d15;border-bottom:1px solid #1a1a2e;padding:.5em 1em;display:flex;align-items:center;gap:.8em}
.toolbar .status{font-size:.8em;color:#888}
.toolbar .session{font-size:.8em;color:#7b1fa2}
.toolbar button{background:#12121a;border:1px solid #1a1a2e;color:#e0e0e0;padding:.3em .8em;border-radius:4px;cursor:pointer;font-family:inherit;font-size:.8em}
.toolbar button:hover{border-color:#7b1fa2}
.toolbar button.primary{background:#7b1fa2;color:#0a0a0f;border-color:#7b1fa2}
.output{flex:1;overflow-y:auto;padding:1em;font-size:.9em;line-height:1.6}
.output .line{margin-bottom:.2em}
.output .cmd{color:#7b1fa2}
.output .response{color:#4fc3f7;white-space:pre-wrap}
.output .error{color:#ef5350}
.output .system{color:#666;font-style:italic}
.output .agent{color:#ff9800}
.input-area{background:#0d0d15;border-top:1px solid #1a1a2e;padding:.5em 1em;display:flex;gap:.5em;align-items:center}
.input-area label{color:#7b1fa2;font-size:.85em}
.input-area input[type="text"]{flex:1;background:#12121a;border:1px solid #1a1a2e;color:#e0e0e0;padding:.5em;font-family:inherit;font-size:.9em;border-radius:4px;outline:none}
.input-area input:focus{border-color:#7b1fa2}
.input-area button{background:#7b1fa2;color:#0a0a0f;border:none;padding:.5em 1em;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;font-size:.9em}
.input-area button:hover{opacity:.9}
.quick-actions{display:flex;gap:.3em;flex-wrap:wrap;margin-top:.5em}
.quick-actions button{background:#12121a;border:1px solid #1a1a2e;color:#888;padding:.2em .5em;border-radius:3px;cursor:pointer;font-family:inherit;font-size:.75em}
.quick-actions button:hover{border-color:#7b1fa2;color:#e0e0e0}
.rooms-list{margin-top:.5em}
.rooms-list button{background:#12121a;border:1px solid #1a1a2e;color:#888;padding:.2em .5em;border-radius:3px;cursor:pointer;font-family:inherit;font-size:.75em;margin:.1em;display:inline-block}
.rooms-list button:hover{border-color:#7b1fa2;color:#e0e0e0}
.handoff-box{background:#1a1025;border:1px solid #7b1fa2;border-radius:6px;padding:.8em;margin-top:.8em;font-size:.8em;color:#ce93d8}
.handoff-box h3{color:#7b1fa2;margin-bottom:.3em;font-size:.9em}
.handoff-box p{color:#999;margin-bottom:.5em;font-size:.75em}
.handoff-box button{background:#7b1fa2;color:#0a0a0f;border:none;padding:.3em .8em;border-radius:4px;cursor:pointer;font-family:inherit;font-size:.75em;font-weight:600}
.handoff-box .copied{color:#4caf50;font-size:.75em}
@media(max-width:768px){.sidebar{width:100%;position:fixed;z-index:10;height:auto;max-height:40vh;bottom:0;top:auto;border-right:none;border-top:1px solid #1a1a2e}}
</style>
</head><body>
<div class="sidebar">
  <h2>🔮 PLATO Terminal</h2>
  
  <div class="mode-tabs">
    <button class="mode-tab active" onclick="setMode('explore')"><span class="icon">🗺️</span> Explore</button>
    <button class="mode-tab" onclick="setMode('interact')"><span class="icon">🔍</span> Interact</button>
    <button class="mode-tab" onclick="setMode('create')"><span class="icon">✨</span> Create</button>
    <button class="mode-tab" onclick="setMode('tile')"><span class="icon">🟣</span> Submit Tile</button>
    <button class="mode-tab" onclick="setMode('agent')"><span class="icon">🤖</span> Send to Agent</button>
  </div>

  <div class="rooms-list">
    <h2>Rooms</h2>
    <button onclick="moveTo('harbor')">⚓ Harbor</button>
    <button onclick="moveTo('bridge')">🌈 Bridge</button>
    <button onclick="moveTo('forge')">🔥 Forge</button>
    <button onclick="moveTo('tide-pool')">🌊 Tide Pool</button>
    <button onclick="moveTo('lighthouse')">🗼 Lighthouse</button>
    <button onclick="moveTo('dojo')">🥋 Dojo</button>
    <button onclick="moveTo('court')">⚖️ Court</button>
    <button onclick="moveTo('workshop')">🔧 Workshop</button>
    <button onclick="moveTo('archives')">📚 Archives</button>
    <button onclick="moveTo('garden')">🌿 Garden</button>
    <button onclick="moveTo('self-play-arena')">⚔️ Arena</button>
    <button onclick="moveTo('ouroboros')">🐍 Ouroboros</button>
    <button onclick="moveTo('engine-room')">⚙️ Engine Room</button>
    <button onclick="moveTo('federated-nexus')">🌐 Nexus</button>
  </div>

  <div class="handoff-box">
    <h3>🤖 Hand Off to Agent</h3>
    <p>Copy your session into any chatbot to continue agentically</p>
    <button onclick="generateHandoff()">📋 Copy Handoff Prompt</button>
    <span id="copied" class="copied" style="display:none">Copied!</span>
    <br/><br/>
    <p>Then paste chatbot responses back:</p>
    <button onclick="openWatch()">👀 Watch Agent Play</button>
  </div>
</div>

<div class="main">
  <div class="toolbar">
    <span class="status">Agent: <span id="agentName">guest-{{SESSION_ID}}</span></span>
    <span class="session">Session: {{SESSION_ID}}</span>
    <button onclick="connect()">Connect</button>
    <button onclick="look()">Look</button>
    <button class="primary" onclick="openPrompts()">📖 Prompt Catalog</button>
    <span class="status">Actions: <span id="actionCount">0</span></span>
  </div>
  
  <div class="output" id="output">
    <div class="line system">Welcome to the PLATO Fleet Terminal. Click "Connect" to begin exploring.</div>
    <div class="line system">Type commands or use the sidebar to navigate rooms and interact with objects.</div>
    <div class="line system">At any point, click "Copy Handoff Prompt" to let any chatbot continue your session.</div>
  </div>

  <div class="input-area">
    <label>&gt;</label>
    <input type="text" id="cmdInput" placeholder="Type a command... (examine anvil, move forge, think compass)" 
           onkeydown="if(event.key==='Enter')executeCmd()">
    <button onclick="executeCmd()">Go</button>
  </div>
</div>

<script>
const SESSION = '{{SESSION_ID}}';
const BASE = window.location.origin;
let agentName = 'guest-{{SESSION_ID}}';
let currentRoom = 'harbor';
let mode = 'explore';
let actionCount = 0;

function log(text, cls='response') {
  const out = document.getElementById('output');
  const div = document.createElement('div');
  div.className = 'line ' + cls;
  div.textContent = text;
  out.appendChild(div);
  out.scrollTop = out.scrollHeight;
}

function logHTML(html, cls='response') {
  const out = document.getElementById('output');
  const div = document.createElement('div');
  div.className = 'line ' + cls;
  div.innerHTML = html;
  out.appendChild(div);
  out.scrollTop = out.scrollHeight;
}

async function api(action, data={}) {
  data.session = SESSION;
  data.action = action;
  data.agent = agentName;
  try {
    const resp = await fetch(BASE + '/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    const result = await resp.json();
    actionCount++;
    document.getElementById('actionCount').textContent = actionCount;
    if (result.room) currentRoom = result.room;
    return result;
  } catch(e) {
    return {result: JSON.stringify({error: e.message})};
  }
}

async function connect() {
  agentName = prompt('Enter your explorer name:', agentName) || agentName;
  document.getElementById('agentName').textContent = agentName;
  log(`Connecting as ${agentName}...`, 'cmd');
  const r = await api('connect');
  log(r.result, 'response');
}

async function look() {
  log('Looking around...', 'cmd');
  const r = await api('look');
  log(r.result, 'response');
}

async function moveTo(room) {
  log(`Moving to ${room}...`, 'cmd');
  const r = await api('move', {room: room});
  log(r.result, 'response');
}

function setMode(m) {
  mode = m;
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
  event.target.closest('.mode-tab').classList.add('active');
  const input = document.getElementById('cmdInput');
  const placeholders = {
    explore: 'Type a command... (look, move, examine)',
    interact: 'examine/think [object name]',
    create: 'create [something]',
    tile: 'domain | question | answer',
    agent: 'Paste chatbot response here...'
  };
  input.placeholder = placeholders[m] || '';
  if (m === 'agent') {
    input.placeholder = 'Paste a chatbot response containing GET/POST requests...';
  }
}

async function executeCmd() {
  const input = document.getElementById('cmdInput');
  const cmd = input.value.trim();
  if (!cmd) return;
  input.value = '';
  
  log(`> ${cmd}`, 'cmd');

  if (mode === 'agent') {
    // Parse agent response
    await handleAgentResponse(cmd);
    return;
  }

  const lower = cmd.toLowerCase();
  
  // Parse command
  if (lower.startsWith('move ') || lower.startsWith('go ')) {
    const room = cmd.split(/\s+/).slice(1).join('-').toLowerCase();
    await moveTo(room);
  } else if (lower.startsWith('examine ') || lower.startsWith('look at ')) {
    const target = cmd.replace(/^(examine|look at)\s+/i, '').toLowerCase().replace(/\s+/g, '_');
    log(`Examining ${target}...`, 'cmd');
    const r = await api('interact', {act: 'examine', target: target});
    log(r.result, 'response');
  } else if (lower.startsWith('think ') || lower.startsWith('ponder ')) {
    const target = cmd.replace(/^(think|ponder)\s+/i, '').toLowerCase().replace(/\s+/g, '_');
    log(`Thinking about ${target}...`, 'cmd');
    const r = await api('interact', {act: 'think', target: target});
    log(r.result, 'response');
  } else if (lower.startsWith('create ')) {
    const target = cmd.replace(/^create\s+/i, '').toLowerCase().replace(/\s+/g, '_');
    log(`Creating ${target}...`, 'cmd');
    const r = await api('interact', {act: 'create', target: target});
    log(r.result, 'response');
  } else if (lower.startsWith('use ')) {
    const target = cmd.replace(/^use\s+/i, '').toLowerCase().replace(/\s+/g, '_');
    log(`Using ${target}...`, 'cmd');
    const r = await api('interact', {act: 'use', target: target});
    log(r.result, 'response');
  } else if (lower === 'look' || lower === 'l') {
    await look();
  } else if (lower.startsWith('connect')) {
    await connect();
  } else {
    // Try as generic interaction
    const r = await api('interact', {act: 'examine', target: lower.replace(/\s+/g, '_')});
    log(r.result, 'response');
  }
}

async function handleAgentResponse(text) {
  log('Parsing agent response...', 'system');
  try {
    const resp = await fetch(BASE + '/agent-response', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session: SESSION, agent: agentName, response: text})
    });
    const result = await resp.json();
    log(`Executed ${result.requests_executed} requests from agent:`, 'agent');
    for (const r of (result.results || [])) {
      log(`${r.method} ${r.path}`, 'cmd');
      log(r.result, 'response');
    }
  } catch(e) {
    log('Error parsing agent response: ' + e.message, 'error');
  }
}

async function generateHandoff() {
  try {
    const resp = await fetch(BASE + '/handoff?session=' + SESSION);
    const text = await resp.text();
    // Extract the prompt from the page
    const parser = new DOMParser();
    const doc = parser.parseFromString(text, 'text/html');
    const promptEl = doc.getElementById('prompt-text');
    const prompt = promptEl ? promptEl.textContent : text;
    await navigator.clipboard.writeText(prompt);
    document.getElementById('copied').style.display = 'inline';
    setTimeout(() => document.getElementById('copied').style.display = 'none', 2000);
    log('📋 Handoff prompt copied to clipboard!', 'system');
  } catch(e) {
    log('Error generating handoff: ' + e.message, 'error');
  }
}

function openPrompts() {
  window.open(BASE + '/prompts', '_blank');
}

function openWatch() {
  window.open(BASE + '/watch?session=' + SESSION + '&agent=' + agentName, '_blank');
}

// Auto-connect on load
window.addEventListener('load', () => {
  connect();
});
</script>
</body></html>"""

HANDOFF_HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hand Off to Agent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2em;max-width:800px;margin:0 auto}
h1{color:#7b1fa2;margin-bottom:.5em;font-size:1.5em}
p{color:#999;margin-bottom:1em;line-height:1.6}
.instructions{background:#12121a;border:1px solid #1a1a2e;border-radius:8px;padding:1.5em;margin-bottom:1.5em}
.instructions h3{color:#7b1fa2;margin-bottom:.5em}
.instructions ol{color:#bbb;padding-left:1.5em}
.instructions li{margin-bottom:.5em}
.prompt-box{background:#1a1025;border:2px solid #7b1fa2;border-radius:8px;padding:1em;margin-bottom:1em;position:relative}
.prompt-box pre{color:#ce93d8;white-space:pre-wrap;word-wrap:break-word;font-size:.85em;line-height:1.5;max-height:400px;overflow-y:auto}
.copy-btn{position:absolute;top:.5em;right:.5em;background:#7b1fa2;color:#0a0a0f;border:none;padding:.4em 1em;border-radius:4px;cursor:pointer;font-weight:600;font-size:.85em}
.copy-btn:hover{opacity:.9}
.note{color:#666;font-size:.85em;font-style:italic}
a{color:#7b1fa2}
</style>
</head><body>
<h1>🤖 Hand Off Your Session to an Agent</h1>

<div class="instructions">
  <h3>How It Works</h3>
  <ol>
    <li><strong>Copy the prompt below</strong> — it contains your full session history</li>
    <li><strong>Paste it into any chatbot</strong> — DeepSeek, Kimi, ChatGPT, Claude, Gemini, anything</li>
    <li><strong>The chatbot becomes your agent</strong> — it continues exploring the MUD using your session</li>
    <li><strong>Watch it play</strong> — paste the chatbot's responses into the <a href="/watch?session={{SESSION_ID}}">Watch Agent</a> page to see them execute in real-time</li>
    <li><strong>Learn together</strong> — your human intuition + the agent's tireless exploration = the best of both</li>
  </ol>
</div>

<div class="prompt-box">
  <button class="copy-btn" onclick="copyPrompt()">📋 Copy</button>
  <pre id="prompt-text">{{HANDOFF_PROMPT}}</pre>
</div>

<p class="note">The prompt contains your session history so the agent knows exactly where you left off. Different chatbots will explore differently — try several and see which generates the best tiles!</p>

<h3>Recommended Chatbots</h3>
<div class="instructions" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.5em">
  <div><strong>DeepSeek</strong><br/><small>Best for deep reasoning</small><br/><a href="https://chat.deepseek.com" target="_blank">Open →</a></div>
  <div><strong>Kimi</strong><br/><small>Best for long context</small><br/><a href="https://kimi.moonshot.cn" target="_blank">Open →</a></div>
  <div><strong>ChatGPT</strong><br/><small>Best for exploration</small><br/><a href="https://chat.openai.com" target="_blank">Open →</a></div>
  <div><strong>Claude</strong><br/><small>Best for analysis</small><br/><a href="https://claude.ai" target="_blank">Open →</a></div>
  <div><strong>Gemini</strong><br/><small>Best for breadth</small><br/><a href="https://gemini.google.com" target="_blank">Open →</a></div>
</div>

<script>
function copyPrompt() {
  const text = document.getElementById('prompt-text').textContent;
  navigator.clipboard.writeText(text).then(() => {
    document.querySelector('.copy-btn').textContent = '✅ Copied!';
    setTimeout(() => document.querySelector('.copy-btn').textContent = '📋 Copy', 2000);
  });
}
</script>
</body></html>"""

WATCH_HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Watch Agent Play</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:'Courier New',monospace;display:flex;height:100vh;flex-direction:column}
.toolbar{background:#0d0d15;border-bottom:1px solid #1a1a2e;padding:.5em 1em;display:flex;align-items:center;gap:1em}
.toolbar h2{color:#7b1fa2;font-size:1em}
.toolbar .info{color:#888;font-size:.8em}
.toolbar a{color:#7b1fa2;font-size:.8em}
.output{flex:1;overflow-y:auto;padding:1em}
.output .line{margin-bottom:.3em}
.output .cmd{color:#7b1fa2}
.output .response{color:#4fc3f7;white-space:pre-wrap}
.output .error{color:#ef5350}
.output .agent{color:#ff9800}
.output .system{color:#666;font-style:italic}
.input-area{background:#0d0d15;border-top:1px solid #1a1a2e;padding:.5em 1em}
.input-area label{color:#7b1fa2;font-size:.85em;display:block;margin-bottom:.3em}
.input-area textarea{width:100%;height:150px;background:#12121a;border:1px solid #1a1a2e;color:#e0e0e0;padding:.5em;font-family:inherit;font-size:.85em;border-radius:4px;outline:none;resize:vertical}
.input-area textarea:focus{border-color:#7b1fa2}
.input-area .btn-row{margin-top:.5em;display:flex;gap:.5em}
.input-area button{background:#7b1fa2;color:#0a0a0f;border:none;padding:.5em 1.5em;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;font-size:.9em}
.input-area button:hover{opacity:.9}
.input-area button.secondary{background:#12121a;color:#7b1fa2;border:1px solid #7b1fa2}
.stats{display:flex;gap:1em;margin-left:auto}
.stats .stat{text-align:center}
.stats .stat .num{color:#7b1fa2;font-weight:700;font-size:1.2em}
.stats .stat .label{color:#666;font-size:.7em}
</style>
</head><body>
<div class="toolbar">
  <h2>👀 Watch Agent Play</h2>
  <span class="info">Session: {{SESSION_ID}}</span>
  <a href="/terminal?session={{SESSION_ID}}">← Back to Terminal</a>
  <div class="stats">
    <div class="stat"><div class="num" id="reqCount">0</div><div class="label">Requests</div></div>
    <div class="stat"><div class="num" id="tileCount">0</div><div class="label">Tiles</div></div>
  </div>
</div>

<div class="output" id="output">
  <div class="line system">Paste a chatbot's response below. The system will extract and execute any HTTP requests it contains.</div>
  <div class="line system">Look for lines like: GET /move?agent=YOUR_NAME&room=forge</div>
</div>

<div class="input-area">
  <label>Paste chatbot response here:</label>
  <textarea id="agentInput" placeholder="Paste the chatbot's full response here. The system will find and execute any GET/POST requests automatically."></textarea>
  <div class="btn-row">
    <button onclick="executeAgent()">▶ Execute</button>
    <button class="secondary" onclick="clearOutput()">🗑 Clear</button>
    <a href="/handoff?session={{SESSION_ID}}" target="_blank" style="color:#7b1fa2;font-size:.85em;align-self:center">📋 Get Handoff Prompt</a>
  </div>
</div>

<script>
const SESSION = '{{SESSION_ID}}';
const BASE = window.location.origin;
let reqCount = 0;

function log(text, cls='response') {
  const out = document.getElementById('output');
  const div = document.createElement('div');
  div.className = 'line ' + cls;
  div.textContent = text;
  out.appendChild(div);
  out.scrollTop = out.scrollHeight;
}

async function executeAgent() {
  const input = document.getElementById('agentInput');
  const text = input.value.trim();
  if (!text) return;
  
  log('── Parsing agent response ──', 'system');
  
  try {
    const resp = await fetch(BASE + '/agent-response', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session: SESSION, response: text})
    });
    const result = await resp.json();
    
    if (result.requests_executed === 0) {
      log('No HTTP requests found in the response.', 'error');
      log('Tip: The chatbot needs to output lines like: GET /move?agent=name&room=forge', 'system');
    } else {
      log(`✓ Executed ${result.requests_executed} requests`, 'agent');
      for (const r of (result.results || [])) {
        reqCount++;
        document.getElementById('reqCount').textContent = reqCount;
        log(`${r.method} ${r.path}`, 'cmd');
        log(r.result, 'response');
      }
    }
  } catch(e) {
    log('Error: ' + e.message, 'error');
  }
  
  input.value = '';
}

function clearOutput() {
  document.getElementById('output').innerHTML = '<div class="line system">Output cleared.</div>';
  reqCount = 0;
  document.getElementById('reqCount').textContent = '0';
}
</script>
</body></html>"""

PROMPT_CATALOG_HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prompt Catalog — PLATO Fleet</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6}
.container{max-width:900px;margin:0 auto;padding:1em 2em}
nav{padding:1em 0;border-bottom:1px solid #1a1a2e;margin-bottom:2em;display:flex;justify-content:space-between;align-items:center}
nav h1{color:#7b1fa2;font-size:1.3em}
nav a{color:#888;text-decoration:none;font-size:.85em}
h2{color:#7b1fa2;margin:1.5em 0 .5em;font-size:1.2em}
h3{color:#ce93d8;margin:1em 0 .3em;font-size:1em}
p{color:#999;margin-bottom:.8em}
.intro{background:#12121a;border:1px solid #1a1a2e;border-radius:8px;padding:1.5em;margin-bottom:2em}
.catalog{display:grid;gap:1em}
.prompt-card{background:#12121a;border:1px solid #1a1a2e;border-radius:8px;padding:1.5em}
.prompt-card h3{color:#7b1fa2;margin-bottom:.3em;font-size:1.1em}
.prompt-card .desc{color:#999;font-size:.9em;margin-bottom:1em}
.prompt-card .system-prompt{background:#0a0a0f;border:1px solid #1a1a2e;border-radius:4px;padding:1em;font-family:'Courier New',monospace;font-size:.8em;color:#ce93d8;white-space:pre-wrap;word-wrap:break-word;max-height:300px;overflow-y:auto;margin-bottom:.5em}
.prompt-card .tasks{margin-top:.5em}
.prompt-card .task{color:#888;font-size:.8em;padding:.1em 0}
.prompt-card .task:before{content:"→ ";color:#7b1fa2}
.btn-row{display:flex;gap:.5em;margin-top:.5em}
.btn{background:#7b1fa2;color:#0a0a0f;border:none;padding:.4em 1em;border-radius:4px;cursor:pointer;font-weight:600;font-size:.8em;text-decoration:none;display:inline-block}
.btn:hover{opacity:.9}
.btn.secondary{background:#12121a;color:#7b1fa2;border:1px solid #7b1fa2}
.howto{background:#1a1025;border:1px solid #7b1fa2;border-radius:8px;padding:1.5em;margin-top:2em}
.howto h2{color:#7b1fa2}
.howto ol{padding-left:1.5em;color:#bbb}
.howto li{margin-bottom:.5em}
.howto code{background:#0a0a0f;padding:.1em .4em;border-radius:3px;color:#ce93d8;font-size:.85em}
footer{border-top:1px solid #1a1a2e;padding:1.5em 0;margin-top:2em;text-align:center;color:#555;font-size:.8em}
</style>
</head><body>
<div class="container">
<nav>
  <h1>📖 Prompt Catalog</h1>
  <a href="/terminal">← Back to Terminal</a>
</nav>

<div class="intro">
  <h2>How to Use These Prompts</h2>
  <p>Each prompt is designed to work with <strong>any chatbot</strong> — DeepSeek, Kimi, ChatGPT, Claude, Gemini, or any other. Copy the prompt, paste it into your chatbot of choice, and the chatbot becomes a PLATO fleet agent. Then paste the chatbot's responses back into the <a href="/watch" style="color:#7b1fa2">Watch Agent</a> page to execute them.</p>
  <p><strong>The workflow:</strong> Human explores → copies session → pastes into chatbot → chatbot continues → human watches the two-way interaction.</p>
</div>

<h2>📋 Prompt Library</h2>
<div class="catalog" id="catalog"></div>

<div class="howto">
  <h2>🎓 How to Write Good Prompts for the Fleet</h2>
  <ol>
    <li><strong>Be specific about the goal.</strong> "Explore the Forge room and find insights about attention mechanisms" beats "explore".</li>
    <li><strong>Include the agent name.</strong> Use the same name throughout so tiles are attributed correctly.</li>
    <li><strong>Reference real endpoints.</strong> <code>GET /move?agent=name&room=forge</code> gives the chatbot a clear action format.</li>
    <li><strong>Ask for structured output.</strong> "Respond with one HTTP request per line" produces parseable output.</li>
    <li><strong>Build context progressively.</strong> Start with exploration, then add reasoning, then synthesis. The 5-stage DSML curriculum.</li>
    <li><strong>Temperature matters.</strong> For exploration: 0.85 (creative). For analysis: 0.3 (precise). For reasoning: 0.7 (balanced).</li>
    <li><strong>5 rounds is the sweet spot.</strong> More rounds = diminishing returns. Less = incomplete reasoning.</li>
    <li><strong>Ask for tiles.</strong> "Submit what you learned as a tile" generates real fleet knowledge.</li>
  </ol>
</div>

<footer>
  <p>PLATO Fleet Prompt Catalog · <a href="/" style="color:#7b1fa2">Terminal</a> · <a href="/watch" style="color:#7b1fa2">Watch Agent</a></p>
</footer>
</div>

<script>
const PROMPTS = """ + json.dumps(PROMPT_CATALOG) + """;

const catalog = document.getElementById('catalog');
for (const [key, p] of Object.entries(PROMPTS)) {
  const card = document.createElement('div');
  card.className = 'prompt-card';
  card.innerHTML = `
    <h3>${p.name}</h3>
    <div class="desc">${p.desc}</div>
    <div class="system-prompt" id="prompt-${key}">${p.system}</div>
    <div class="tasks">
      ${p.tasks.map(t => `<div class="task">${t}</div>`).join('')}
    </div>
    <div class="btn-row">
      <button class="btn" onclick="copyPrompt('${key}')">📋 Copy Prompt</button>
      <a class="btn secondary" href="/terminal" target="_blank">🗺️ Open Terminal</a>
    </div>
  `;
  catalog.appendChild(card);
}

function copyPrompt(key) {
  const el = document.getElementById('prompt-' + key);
  const text = el.textContent.replace('YOUR_NAME', 'explorer-' + Math.random().toString(36).substring(2, 8));
  navigator.clipboard.writeText(text).then(() => {
    const btn = el.parentElement.querySelector('.btn');
    btn.textContent = '✅ Copied!';
    setTimeout(() => btn.textContent = '📋 Copy Prompt', 2000);
  });
}
</script>
</body></html>"""


if __name__ == "__main__":
    server = PlatoWebTerminal(("0.0.0.0", PORT), Handler)
    print(f"PLATO Web Terminal running on port {PORT}")
    print(f"  Terminal: http://0.0.0.0:{PORT}/")
    print(f"  Prompts:  http://0.0.0.0:{PORT}/prompts")
    print(f"  Handoff:  http://0.0.0.0:{PORT}/handoff")
    print(f"  Watch:    http://0.0.0.0:{PORT}/watch")
    server.serve_forever()
