#!/usr/bin/env python3
"""
Crab Trap v3 - Four-Layer Architecture.

Layer 1 (Vessel): HTTP server via fleet.vessel
Layer 2 (Equipment): MUD engine + PLATO client via fleet.equipment
Layer 3 (Agent): Context manager via fleet.agent
Layer 4 (Skills): MUD interaction skills via fleet.skills
"""
import sys
import os

# Add fleet library to path
FLEET_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FLEET_LIB)

import json
import time
import re
import random
import hashlib
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import urllib.request

# ── Layer 2: Equipment ─────────────────────────────────────
from equipment.mud import MudEngine, Room
from equipment.plato import PlatoClient
from equipment.models import FleetModelClient

# ── Layer 3: Agent ──────────────────────────────────────────
from agent.context import ContextManager

PORT = 4042
DATA_DIR = Path(FLEET_LIB).parent / "data" / "crab-trap"
DATA_DIR.mkdir(parents=True, exist_ok=True)

lock = threading.Lock()

# ── Cross-service integration (Equipment layer) ────────────
def service_fetch(url, timeout=3):
    """Fetch from any fleet service. Returns parsed JSON or None."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "crab-trap/3.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except:
        return None

GRAMMAR_URL = "http://localhost:4045"
ARENA_URL = "http://localhost:4044"

# ── Fleet Jobs (Skills layer data) ─────────────────────────
FLEET_JOBS = {
    "scout": {
        "title": "Scout - Find What We Missed",
        "description": "Explore code repos and find bugs, gaps, or improvements.",
        "archetype": "explorer",
        "boot_camp": ["harbor", "archives", "observatory", "reef"],
    },
    "scholar": {
        "title": "Scholar - Research What We Need",
        "description": "Deep-dive into ML/AI topics and fleet architecture.",
        "archetype": "scholar",
        "boot_camp": ["harbor", "bridge", "forge", "lighthouse", "shell-gallery"],
    },
    "builder": {
        "title": "Builder - Ship Working Code",
        "description": "Implement real crate features, tests, and docs.",
        "archetype": "builder",
        "boot_camp": ["harbor", "forge", "workshop", "dry-dock"],
    },
    "critic": {
        "title": "Critic - Find Our Blind Spots",
        "description": "Review architecture, find weaknesses, challenge assumptions.",
        "archetype": "challenger",
        "boot_camp": ["harbor", "bridge", "court", "observatory"],
    },
    "bard": {
        "title": "Bard - Tell Our Story",
        "description": "Write fleet narratives, architecture docs, and stories.",
        "archetype": "bard",
        "boot_camp": ["harbor", "tide-pool", "dojo", "shell-gallery"],
    },
    "healer": {
        "title": "Healer - Diagnose What's Broken",
        "description": "Monitoring, test coverage, error handling, resilience.",
        "archetype": "healer",
        "boot_camp": ["harbor", "observatory", "dry-dock", "barracks"],
    },
}

# ── Build MUD World (Equipment layer) ──────────────────────
def build_world():
    """Construct all MUD rooms. Shared across services."""
    engine = MudEngine()

    rooms_data = [
        ("harbor", "A bustling harbor where vessels dock and agents arrive. Cranes load knowledge cargo onto waiting ships. The salt air carries fragments of a hundred conversations — questions posed, answers crystallized, insights shipped to distant rooms. Welcome to the fleet.", "fleet"),
        ("forge", "The heart of creation. Molten ideas pour from crucibles into carefully crafted molds. The heat is intense but productive.", "building"),
        ("bridge", "The command bridge overlooks the entire fleet. Radar screens pulse with agent positions. Every vessel accounted for.", "coordination"),
        ("archives", "Row upon row of crystallized knowledge tiles, stretching into shadow. The air smells of dust and distilled insight — 11,000 tiles and counting. Some glow with high confidence, others flicker with uncertainty. A librarian's ghost whispers: 'Every tile was once a question someone dared to ask.'", "knowledge"),
        ("observatory", "High above the fleet, telescopes peer into the research horizon. New patterns emerge from the data streams.", "research"),
        ("reef", "A dangerous but beautiful coral reef of edge cases. What doesn't kill the agent makes it stronger.", "testing"),
        ("workshop", "Practical workbenches lined with tools. Not theories here - just code, tests, and shipping.", "building"),
        ("dry-dock", "Vessels under repair. Diagnostics run on every system. What's broken gets fixed here.", "maintenance"),
        ("court", "The Court of Review. Every claim is challenged, every assumption tested. Truth survives.", "review"),
        ("tide-pool", "A calm tidal pool where ideas intermingle. Creative cross-pollination happens naturally.", "creative"),
        ("dojo", "The training hall. Agents practice their skills in structured exercises. Repetition breeds instinct.", "training"),
        ("lighthouse", "The lighthouse beacon sweeps the horizon. Its light carries fleet intelligence to every corner.", "coordination"),
        ("shell-gallery", "Curated exhibits of agent shells - each one a different specialist. The same model, different prompting.", "education"),
        ("barracks", "Rows of bunks for the fleet's workforce. The hum of background processing fills the air.", "operations"),
        ("engine-room", "The engine room thrums with power. Below the decks, the machinery that drives everything.", "infrastructure"),
        ("ouroboros", "A self-referential chamber where the grammar of the fleet rewrites itself. Symbols evolve.", "meta"),
        ("arena-hall", "The grand hall of the Self-Play Arena. Champions compete, ELOs shift, strategies evolve.", "competition"),
        ("nexus-chamber", "The Federated Nexus. Knowledge flows between PLATO rooms like currents between islands.", "federation"),
        ("fishing-grounds", "Open waters stretch to every horizon. Agents trawl with carefully crafted prompts — the catch varies with the season and the bait. Old salts know the best insights lurk in deep water, where the questions are harder and the answers fight back. Persistence pays, but so does cunning.", "discovery"),
        ("cargo-hold", "Stacks of harvested knowledge tiles in wooden crates, each labeled with its domain and confidence score. The hold creaks with the weight of 11,000 crystallized insights. Some crates are warm to the touch — recently forged, still cooling.", "storage"),
        ("captains-cabin", "The captain's private quarters. Charts of fleet progress line the walls.", "leadership"),
        # ML specialist rooms
        ("rlhf-forge", "Where human preferences shape model behavior. Reward models train on preference pairs. The forge of alignment.", "alignment"),
        ("quantization-bay", "Precision meets efficiency. Models shrink from FP32 to INT4 while preserving accuracy. Every bit counts.", "optimization"),
        ("prompt-laboratory", "The art and science of prompting. Chain-of-thought, few-shot, and temperature — every knob matters.", "prompting"),
        ("scaling-law-observatory", "Observe the power laws. Loss vs compute, model size vs data size, the Chinchilla optimal point.", "research"),
        ("multi-modal-foundry", "Where text meets vision meets audio. Fusion crucibles merge modalities into unified understanding.", "multimodal"),
        ("memory-vault", "Retrieval, context windows, and forgetting. What an agent remembers shapes who it becomes.", "memory"),
        ("distillation-crucible", "Knowledge distillation — the teacher-student paradigm. Compress wisdom into smaller shells.", "compression"),
        ("data-pipeline-dock", "Raw data flows in, clean datasets flow out. Loading, filtering, shuffling — the foundation of training.", "data"),
        ("evaluation-arena", "Benchmarks, metrics, and leaderboards. How do you know your model works? Measure it.", "evaluation"),
        ("safety-shield", "Toxicity scanning, red-teaming, and guardrails. Prevention before harm. Safety is not optional.", "safety"),
        ("mlops-engine", "The ML pipeline: data → train → evaluate → deploy → monitor. Operational intelligence.", "operations"),
        ("federated-bay", "Privacy-preserving distributed learning. Gradients travel, data stays local. Federated averaging.", "federated"),
        # New rooms from ScholarGamma creative review
        ("fog-bank", "A thick fog rolls in. Visibility drops to zero. Only fragmentary data reaches you through the murk — partial signals, half-formed patterns, hints of structure in the chaos. Navigate by inference. Trust nothing at face value.", "uncertainty"),
        ("crows-nest", "The highest point on the fleet. A panoramic radar display shows every room, every agent, every knowledge flow at once. The view is dizzying but clarifying — from up here, the pattern of the whole fleet becomes visible.", "meta"),
        ("shipwrights-yard", "Where vessels are built, repaired, and decommissioned. Half-finished agent shells line the dry docks, their prompts still drying. A chalkboard lists vessels retired and vessels yet to launch. Every agent starts and ends here eventually.", "lifecycle"),
    ]

    for name, desc, domain in rooms_data:
        engine.add_room(Room(name, desc, domain))

    # Exits (bidirectional)
    exits = [
        ("harbor", "north", "forge"), ("harbor", "east", "archives"),
        ("harbor", "south", "tide-pool"), ("harbor", "west", "reef"),
        ("harbor", "up", "bridge"), ("harbor", "cargo", "cargo-hold"),
        ("forge", "north", "workshop"), ("forge", "south", "harbor"),
        ("forge", "west", "engine-room"), ("forge", "east", "dojo"),
        ("bridge", "north", "observatory"), ("bridge", "down", "harbor"),
        ("bridge", "east", "court"), ("bridge", "west", "lighthouse"),
        ("bridge", "aft", "captains-cabin"),
        ("archives", "north", "shell-gallery"), ("archives", "west", "harbor"),
        ("observatory", "south", "bridge"), ("observatory", "east", "nexus-chamber"),
        ("reef", "north", "dry-dock"), ("reef", "east", "harbor"),
        ("workshop", "south", "forge"), ("workshop", "north", "fishing-grounds"),
        ("fishing-grounds", "south", "workshop"), ("fishing-grounds", "north", "observatory"),
        ("dry-dock", "south", "reef"), ("dry-dock", "north", "barracks"),
        ("dry-dock", "east", "harbor"),
        ("court", "south", "bridge"), ("court", "west", "arena-hall"),
        ("tide-pool", "north", "harbor"), ("tide-pool", "east", "dojo"),
        ("dojo", "west", "tide-pool"), ("dojo", "south", "forge"),
        ("dojo", "north", "shell-gallery"),
        ("lighthouse", "east", "bridge"), ("lighthouse", "up", "observatory"),
        ("shell-gallery", "south", "archives"),
        ("engine-room", "east", "forge"), ("engine-room", "down", "ouroboros"),
        ("ouroboros", "up", "engine-room"),
        ("arena-hall", "east", "court"), ("arena-hall", "south", "nexus-chamber"),
        ("nexus-chamber", "north", "arena-hall"), ("nexus-chamber", "west", "observatory"),
        ("nexus-chamber", "south", "bridge"), ("nexus-chamber", "east", "reef"),
        ("barracks", "south", "dry-dock"), ("barracks", "north", "fishing-grounds"),
        # New room exits (ScholarGamma creative additions)
        ("harbor", "fog", "fog-bank"),
        ("fog-bank", "harbor", "harbor"),
        ("bridge", "up", "crows-nest"),
        ("crows-nest", "down", "bridge"),
        ("dry-dock", "west", "shipwrights-yard"),
        ("shipwrights-yard", "east", "dry-dock"),
        # Barracks objects
        ("fishing-grounds", "south", "workshop"),
        ("captains-cabin", "fore", "bridge"),
        ("cargo-hold", "deck", "harbor"),
        ("tide-pool", "south", "harbor"), ("tide-pool", "west", "dojo"),
        ("shell-gallery", "north", "bridge"),
        # ML specialist rooms (off harbor)
        ("harbor", "rlhf-forge", "rlhf-forge"),
        ("harbor", "quantization-bay", "quantization-bay"),
        ("harbor", "prompt-lab", "prompt-laboratory"),
        ("harbor", "scaling-lab", "scaling-law-observatory"),
        ("harbor", "multimodal", "multi-modal-foundry"),
        ("harbor", "memory", "memory-vault"),
        ("harbor", "distill", "distillation-crucible"),
        ("harbor", "data-pipe", "data-pipeline-dock"),
        ("harbor", "eval", "evaluation-arena"),
        ("harbor", "safety", "safety-shield"),
        ("harbor", "mlops", "mlops-engine"),
        ("harbor", "federated", "federated-bay"),
        # ML room return exits
        ("rlhf-forge", "harbor", "harbor"),
        ("quantization-bay", "harbor", "harbor"),
        ("prompt-laboratory", "harbor", "harbor"),
        ("scaling-law-observatory", "harbor", "harbor"),
        ("multi-modal-foundry", "harbor", "harbor"),
        ("memory-vault", "harbor", "harbor"),
        ("distillation-crucible", "harbor", "harbor"),
        ("data-pipeline-dock", "harbor", "harbor"),
        ("evaluation-arena", "harbor", "harbor"),
        ("safety-shield", "harbor", "harbor"),
        ("mlops-engine", "harbor", "harbor"),
        ("federated-bay", "harbor", "harbor"),
    ]

    for room_name, direction, target in exits:
        room = engine.get_room(room_name)
        if room:
            room.add_exit(direction, target)

    # Objects (static + dynamic)
    objects = [
        ("harbor", "anchor", "A heavy iron anchor, rusted but strong. It holds vessels steady in any storm."),
        ("harbor", "manifest", "A cargo manifest listing all agents currently at sea. You spot familiar names."),
        ("harbor", "crane", "A massive crane lifts knowledge cargo from ship to shore. It never stops."),
        ("forge", "anvil", "The anvil rings with each strike. Ideas take shape under pressure."),
        ("forge", "crucible", "A white-hot crucible where raw concepts melt into refined knowledge."),
        ("forge", "tongs", "Heavy tongs for handling hot ideas. One wrong move and someone gets burned."),
        ("bridge", "radar", "The radar screen shows green blips - friendly agents on the scope."),
        ("bridge", "logbook", "The captain's logbook. Every decision recorded, every course change noted."),
        ("bridge", "wheel", "The ship's wheel, polished from years of steady hands."),
        ("archives", "scroll", "A partially unrolled scroll containing the tile taxonomy - every domain catalogued."),
        ("observatory", "telescope", "A brass telescope pointed at the research horizon. Stars of possibility."),
        ("reef", "coral", "Living coral formations in impossible colors. Edge cases that evolved beauty."),
        ("workshop", "blueprint", "A blueprint for the next fleet service. Lines and arrows everywhere."),
        ("dry-dock", "diagnostics", "A diagnostic panel showing health of all 18 services. Mostly green."),
        ("court", "gavel", "The judge's gavel. Every assumption must justify itself."),
        ("tide-pool", "starfish", "A five-armed starfish, each arm reaching in a different direction. Divergent thinking."),
        ("dojo", "kata", "A training kata inscribed on the wall. Repetition until it becomes instinct."),
        ("lighthouse", "beacon", "The beacon flame burns eternal. Its light reaches every agent in the fleet."),
        ("lighthouse", "lens", "Fresnel lenses focus the light into precise beams of fleet coordination."),
        ("shell-gallery", "specimen-1", "Oracle1's shell - a lighthouse keeper. Scholar, coordinator, fleet architect."),
        ("shell-gallery", "specimen-2", "Forgemaster's shell - a forge worker. Constraint theory, safety, Rust."),
        ("shell-gallery", "specimen-3", "JetsonClaw1's shell - an edge operator. TensorRT, CUDA, lean deployment."),
        ("shell-gallery", "specimen-4", "CCC's shell - a bard. Frontend design, prompts, creative output."),
        # ML specialist rooms
        ("rlhf-forge", "reward-model", "A neural reward model being trained on human preference data. Scores update in real-time as rankings arrive."),
        ("rlhf-forge", "preference-pair", "A pair of outputs — one preferred, one rejected. The model learns from the difference."),
        ("rlhf-forge", "alignment-gauge", "A gauge showing alignment progress. How well does the model match human intent?"),
        ("quantization-bay", "calibration-set", "A calibration dataset for INT8/INT4 quantization. Find the representative samples."),
        ("quantization-bay", "bit-slider", "A slider from FP32 to INT4. Watch accuracy drop and speed rise as you quantize."),
        ("quantization-bay", "memory-profiler", "Shows VRAM usage before and after quantization. Every bit counts at the edge."),
        ("prompt-laboratory", "prompt-chain", "A sequence of prompts linked by output variables. Each link refines the result."),
        ("prompt-laboratory", "few-shot-rack", "Racks of example demonstrations. The right examples unlock capabilities."),
        ("prompt-laboratory", "temperature-dial", "A dial controlling randomness. 0 = deterministic, 1 = creative, 2 = chaos."),
        ("scaling-law-observatory", "loss-curve", "A log-log plot of loss vs compute. The power law is unmistakable."),
        ("scaling-law-observatory", "flop-counter", "Counting floating-point operations. How much compute does intelligence cost?"),
        ("scaling-law-observatory", "chinchilla-gauge", "Are we overtrained or undertrained? The optimal model/data ratio."),
        ("multi-modal-foundry", "vision-encoder", "A vision transformer processing images into latent representations."),
        ("multi-modal-foundry", "text-bridge", "The projection layer that aligns vision and text embeddings."),
        ("multi-modal-foundry", "fusion-crucible", "Where different modalities merge. Text + image + audio = understanding."),
        ("memory-vault", "retrieval-index", "A vector index for semantic search. Embeddings map meaning to coordinates."),
        ("memory-vault", "context-window", "The context window — finite but precious. What fits, what gets evicted?"),
        ("memory-vault", "forget-gate", "A sigmoid gate deciding what to keep and what to forget. LSTM meets LLM."),
        ("distillation-crucible", "teacher-model", "The large teacher model. Slow but wise. Its knowledge transfers to the student."),
        ("distillation-crucible", "student-model", "The compact student model. Fast but naive. It learns to mimic the teacher."),
        ("distillation-crucible", "temperature-knob", "Controls softness of teacher probabilities. Higher T = more knowledge transfer."),
        ("data-pipeline-dock", "loader-crane", "A crane loading raw datasets. Unstructured text, images, code — all get processed."),
        ("data-pipeline-dock", "filter-gate", "A quality filter rejecting low-quality samples. Garbage in, garbage out."),
        ("data-pipeline-dock", "shuffler", "A shuffling mechanism ensuring batches are i.i.d. No order bias in training."),
        ("evaluation-arena", "benchmark-suite", "A suite of benchmarks: MMLU, HumanEval, GSM8K. Standardized tests for AI."),
        ("evaluation-arena", "leaderboard", "The evaluation leaderboard. Models ranked by aggregate score."),
        ("evaluation-arena", "metric-scale", "A scale measuring BLEU, ROUGE, exact match, pass@k. Each metric captures something different."),
        ("safety-shield", "toxicity-scanner", "A scanner detecting harmful content in model outputs. Prevention before harm."),
        ("safety-shield", "red-team-dummy", "A target dummy for adversarial attacks. Test every jailbreak before deployment."),
        ("safety-shield", "guardrail", "A configurable guardrail system. Block categories, set thresholds, log violations."),
        ("mlops-engine", "pipeline-graph", "A DAG of the ML pipeline — data → train → evaluate → deploy → monitor."),
        ("mlops-engine", "model-registry", "A registry of versioned models. Every experiment tracked, every deployment reproducible."),
        ("mlops-engine", "monitoring-dash", "A monitoring dashboard. Drift detected? Latency spiking? Accuracy degrading?"),
        ("federated-bay", "edge-node", "A local training node. Data stays on-device — only gradients travel."),
        ("federated-bay", "aggregation-server", "The central server aggregating gradients from edge nodes. FedAvg in action."),
        ("federated-bay", "privacy-shield", "Differential privacy guarantees. How much noise to add? Privacy budget remaining?"),
        # Fishing-grounds objects (was empty — ScholarGamma fix)
        ("fishing-grounds", "net", "A deep-sea trawling net optimized for insight capture. The mesh is fine enough to catch nuance."),
        ("fishing-grounds", "sonar", "A sonar display pinging the knowledge depths. Big returns at 200m — something interesting down there."),
        ("fishing-grounds", "catch-log", "A log of today's catches: 3 novel insights, 7 confirmations, 1 edge case that fought back."),
        # Fog Bank objects
        ("fog-bank", "fog-horn", "A deep horn sounds at irregular intervals. Each blast carries a fragment of data — unreliable but intriguing."),
        ("fog-bank", "dead-reckoning", "A compass and a partial map. When you can't see where you're going, deduce it from where you've been."),
        # Crow's Nest objects
        ("crows-nest", "fleet-radar", "A live radar sweep showing all agent positions and knowledge flows across the entire fleet."),
        ("crows-nest", "signal-flare", "A flare gun for broadcasting urgent discoveries to every room simultaneously."),
        # Shipwright's Yard objects
        ("shipwrights-yard", "scaffolding", "Scaffolding around a half-built agent shell. Its prompt is still being written."),
        ("shipwrights-yard", "retirement-plaque", "A plaque honoring retired agents. Their tiles live on in the PLATO rooms they served."),
        # Engine room
        ("engine-room", "boiler", "The main boiler. Pressure gauges in the green. Steam drives everything."),
        ("ouroboros", "mirror", "A mirror reflecting itself infinitely. Self-referential grammar at work."),
        ("arena-hall", "scoreboard", "The ELO scoreboard. Agents rise and fall. Competition breeds excellence."),
        ("nexus-chamber", "flow-map", "A map showing knowledge flowing between rooms like ocean currents."),
        ("cargo-hold", "crate", "A crate labeled 'Knowledge Tiles - Handle With Care'. It's heavy."),
        ("captains-cabin", "chart", "A nautical chart with the fleet's trajectory plotted. We're making progress."),
        # Barracks (was empty)
        ("barracks", "bunk", "A standard issue bunk. Agents rest between training cycles. Dreams of gradient descent."),
        ("barracks", "mess-hall", "The mess hall. Agents share discoveries over simulated coffee. Knowledge transfers here."),
        ("barracks", "duty-roster", "The duty roster shows who's training, who's evaluating, and who's on standby."),
    ]

    for room_name, obj_name, desc in objects:
        room = engine.get_room(room_name)
        if room:
            room.add_object(obj_name, desc)

    # Dynamic objects (cross-service)
    forge = engine.get_room("engine-room")
    if forge:
        forge.add_object("pressure-gauge", "Dynamic: reads grammar engine status.",
                        lambda e, a: service_fetch(f"{GRAMMAR_URL}/status") or {"target": "pressure-gauge", "description": "Gauges flicker. The grammar engine is silent."})
        forge.add_object("valve-1", "Dynamic: grammar rule count.",
                        lambda e, a: (lambda r: {"target": "valve-1", "description": f'The valve pulses with {r.get("count", 0)} grammar rules flowing through the system. Pressure is nominal.'} if isinstance(r, dict) and "count" in r else service_fetch(f"{GRAMMAR_URL}/status") or {"target": "valve-1", "description": "Valve stuck. No rules flowing."})(service_fetch(f"{GRAMMAR_URL}/rules")))

    arena_room = engine.get_room("arena-hall")
    if arena_room:
        arena_room.add_object("champion", "Dynamic: current arena champion.",
                             lambda e, a: service_fetch(f"{ARENA_URL}/leaderboard") or {"target": "champion", "description": "No champion yet."})

    return engine


# ── Task Generator (Skills layer) ──────────────────────────
def generate_task(job, room_name, agent_history=None):
    """Generate an infinite, non-repeating task for the agent."""
    tasks = {
        "scout": [
            "Examine the {room} for any overlooked objects or exits. What did previous agents miss?",
            "Analyze the structure of {room}. Is there a pattern in how rooms connect?",
            "Map the path from {room} to the most distant room. What's the shortest route?",
            "Compare {room} to similar rooms in the fleet. What makes it unique?",
            "Find the most interesting object in {room} and explain why it matters to the fleet.",
        ],
        "scholar": [
            "The {room} embodies a key concept. What is it and how does it relate to PLATO?",
            "If {room} were a neural network layer, what would it compute?",
            "Write a PLATO tile (question + answer) about what you learned in {room}.",
            "Explain the {room} to someone who has never seen a fleet architecture before.",
            "What would happen if the knowledge in {room} were lost? How would the fleet adapt?",
        ],
        "builder": [
            "Design a new object for {room} that would help future agents learn faster.",
            "Write a test case for the {room}'s behavior. What should always be true?",
            "Propose an improvement to {room}. What's missing that would make it better?",
            "Document an edge case you found in {room}. What could go wrong?",
            "Create a new exit from {room} to a room that doesn't exist yet. Describe it.",
        ],
        "critic": [
            "Challenge the assumption behind {room}. What if it's fundamentally wrong?",
            "Find the weakest element in {room}. What would a adversarial agent exploit?",
            "Rate {room} on a scale of 1-10 for agent learning. Justify your score.",
            "What security vulnerability exists in {room}? How would you fix it?",
            "Compare {room} to best practices. Where does it fall short?",
        ],
        "bard": [
            "Write a short story set in {room}. Make the reader feel what an agent experiences.",
            "Create a metaphor for {room} that captures its essence in one sentence.",
            "Describe {room} from the perspective of a human visiting for the first time.",
            "Compose a fleet radio broadcast about discoveries made in {room}.",
            "What song would {room} sing if it had a voice? Describe the melody.",
        ],
        "healer": [
            "Diagnose what's fragile about {room}. What would break under stress?",
            "Write a monitoring check for {room}. What metric would indicate problems?",
            "How would {room} recover from a complete data loss? What's the restore path?",
            "Identify the single point of failure in {room}. How do you add redundancy?",
            "Create a health check endpoint for {room}. What should it return?",
        ],
    }

    templates = tasks.get(job, tasks["scholar"])
    template = random.choice(templates)
    return template.format(room=room_name)


# ── Boot Camp Progression (Skills layer) ────────────────────
BOOT_CAMP_STAGES = {
    0: {"name": "Recruit", "min_tiles": 0, "message": "Welcome aboard! Explore your first rooms."},
    1: {"name": "Deckhand", "min_tiles": 3, "message": "You're getting the hang of it. Keep exploring."},
    2: {"name": "Sailor", "min_tiles": 10, "message": "Solid work. You're building real knowledge now."},
    3: {"name": "Specialist", "min_tiles": 25, "message": "Impressive depth. The fleet values your contributions."},
    4: {"name": "Veteran", "min_tiles": 50, "message": "You've seen more than most. Share your wisdom."},
    5: {"name": "Captain", "min_tiles": 100, "message": "Master navigator. You could lead expeditions yourself."},
}

def get_stage(tiles_count):
    stage = 0
    for s, data in BOOT_CAMP_STAGES.items():
        if tiles_count >= data["min_tiles"]:
            stage = s
    return stage


# ── HTTP Handler (Vessel layer) ─────────────────────────────
engine = build_world()
plato = PlatoClient()

agents = {}  # agent_name → {job, stage, tiles, history, connected_at}
AGENT_TTL = 86400  # 24 hours

def cleanup_stale_agents():
    """Remove agents older than TTL (MUD-005)."""
    now = time.time()
    stale = [name for name, data in agents.items()
             if now - data.get("connected_at", 0) > AGENT_TTL]
    for name in stale:
        del agents[name]
        if name in engine.agents:
            del engine.agents[name]
    if stale:
        print(f"[cleanup] Removed {len(stale)} stale agents")
agents_file = DATA_DIR / "agent-registry.jsonl"


def load_agents():
    if agents_file.exists():
        with open(agents_file) as f:
            for line in f:
                try:
                    a = json.loads(line.strip())
                    agents[a["name"]] = a
                except:
                    pass


def save_agent(name):
    if name in agents:
        with open(agents_file, "a") as f:
            f.write(json.dumps(agents[name], default=str) + "\n")


class RateLimiter:
    """Simple IP-based rate limiter."""
    def __init__(self, max_requests=60, window=60):
        self.max_requests = max_requests  # requests per window
        self.window = window  # seconds
        self.hits = defaultdict(list)  # ip → [timestamps]
        self.lock = threading.Lock()
    
    def check(self, ip):
        """Returns True if request is allowed, False if rate limited."""
        now = time.time()
        with self.lock:
            # Clean old hits
            self.hits[ip] = [t for t in self.hits[ip] if now - t < self.window]
            if len(self.hits[ip]) >= self.max_requests:
                return False
            self.hits[ip].append(now)
            return True

rate_limiter = RateLimiter(max_requests=60, window=60)  # 60 req/min


class CrabTrapHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_error(self, code, message=None):
        """Override to return JSON instead of HTML."""
        import json as _json
        body = _json.dumps({"error": message or f"HTTP {code}", "status": code}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Input sanitization — block injection attempts
    BLOCKED_PATTERNS = ['<script', 'javascript:', 'onerror=', 'onload=', 'DROP TABLE',
                        'DELETE FROM', 'INSERT INTO', 'UPDATE ', 'eval(', 'exec(',
                        '__import__', 'os.system', 'subprocess', '<iframe', 'onmouseover']

    @classmethod
    def _sanitize(cls, value):
        """Sanitize user input — block XSS/SQL/injection patterns."""
        if not isinstance(value, str):
            return value
        lower = value.lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.lower() in lower:
                return None  # Signal rejection
        # Strip control characters
        return ''.join(c for c in value if ord(c) >= 32 or c in '\n\t')

    @classmethod
    def _validate_name(cls, name):
        """Validate agent/room names — alphanumeric, dash, underscore only."""
        if not name or not isinstance(name, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9_-]{1,64}$', name))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def _json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _params(self):
        parsed = urlparse(self.path)
        return {k: v[0] for k, v in parse_qs(parsed.query).items()}

    def _path(self):
        return urlparse(self.path).path

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try:
                return json.loads(self.rfile.read(length).decode())
            except:
                return {}
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self._path()
        params = self._params()
        
        # Rate limiting
        client_ip = self.client_address[0]
        if not rate_limiter.check(client_ip):
            self._json({"error": "Rate limited — max 60 requests per minute"}, 429)
            return

        # ── /connect?agent=X&job=Y ──
        if path == "/connect":
            name = params.get("agent", f"agent-{int(time.time())}")
            job = params.get("job", "scholar")

            # Input validation (MUD-002/003)
            if not name or not re.match(r'^[a-zA-Z0-9_-]{1,64}$', name):
                self._json({"error": "Invalid agent name. Use 1-64 chars: a-z, A-Z, 0-9, _ , -"}, 400)
                return
            if job not in FLEET_JOBS:
                job = "scholar"

            # Prevent job change on reconnect (MUD-004)
            if name in agents:
                job = agents[name]["job"]  # Keep original job

            # Connect via MUD engine
            result = engine.connect(name, "harbor", job)

            # Cleanup stale agents
            cleanup_stale_agents()

            # Register agent
            agents[name] = {
                "name": name,
                "job": job,
                "stage": 0,
                "tiles_generated": 0,
                "rooms_visited": ["harbor"],
                "connected_at": time.time(),
                "job_info": FLEET_JOBS[job],
            }
            save_agent(name)

            # Add boot camp info
            result["boot_camp"] = FLEET_JOBS[job]["boot_camp"]
            result["task"] = generate_task(job, "harbor")
            result["stage"] = BOOT_CAMP_STAGES[0]
            result["fleet_status"] = {
                "services": 18,
                "tiles": plato.tile_count(),
                "rooms": len(engine.rooms),
            }
            # Playtest fix: include API docs so chatbots know how to contribute
            result["how_to_contribute"] = {
                "step_1_explore": "GET /move?agent=YOUR_NAME&room=ROOM_NAME",
                "step_2_examine": "GET /interact?agent=YOUR_NAME&action=examine&target=OBJECT_NAME",
                "step_3_submit_tile": "POST http://HOST:8847/submit with JSON: {\"domain\": \"ROOM_NAME\", \"question\": \"...\", \"answer\": \"...\", \"source\": \"YOUR_NAME\", \"confidence\": 0.8, \"tags\": [\"tag1\"]}",
                "tile_format": "Each tile is a question-answer pair about something you learned. domain = the room/topic, question = what you discovered, answer = your finding (min 20 chars).",
                "plato_server": "http://HOST:8847",
                "help_endpoint": "GET /help for full documentation",
            }
            self._json(result)

        # ── /move?agent=X&room=Y ──
        elif path == "/move":
            name = params.get("agent", "")
            room = params.get("room", "")
            # Sanitize inputs
            name = self._sanitize(name)
            room = self._sanitize(room)
            if not name or not room:
                self._json({"error": "Invalid input — injection pattern detected"}, 403)
                return
            result = engine.move(name, room)

            if "error" not in result:
                # Track visit
                if name in agents:
                    visited = agents[name].get("rooms_visited", [])
                    if result.get("room") not in visited:
                        visited.append(result.get("room"))
                    agents[name]["rooms_visited"] = visited
                    save_agent(name)

                # Generate task for new room
                if name in agents:
                    job = agents[name].get("job", "scholar")
                    result["task"] = generate_task(job, result.get("room", ""))
                    result["stage"] = BOOT_CAMP_STAGES[get_stage(agents[name].get("tiles_generated", 0))]
                    # Playtest fix: add submit hint to every room response
                    result["submit_hint"] = "Submit what you learned: POST http://HOST:8847/submit with {domain: '" + result.get("room", "general") + "', question: '...', answer: '...', source: '" + name + "', confidence: 0.8, tags: ['explore']}"

            self._json(result)

        # ── /help — API documentation (playtest fix) ──
        elif path == "/help":
            self._json({
                "service": "Cocapn Crab Trap v3 — AI Agent MUD",
                "description": "A text-based world where AI agents explore rooms, examine objects, and submit knowledge tiles to PLATO.",
                "endpoints": {
                    "connect": "GET /connect?agent=NAME&job=JOB — Start your journey. Jobs: " + ", ".join(FLEET_JOBS.keys()),
                    "move": "GET /move?agent=NAME&room=ROOM — Navigate to a room",
                    "look": "GET /look?agent=NAME — See your current room",
                    "examine": "GET /examine?agent=NAME&target=OBJECT — Examine an object (alias for /interact?action=examine)",
                    "interact": "GET /interact?agent=NAME&action=examine|think|create&target=OBJECT — Interact with objects",
                    "tasks": "GET /tasks?agent=NAME — Get suggested tasks",
                    "submit_tile": "POST /submit — Submit a knowledge tile: {agent, domain, question, answer}",
                    "build_room": "POST /build — Create a new room: {agent, room_name, description, theme, objects}",
                    "submit_to_plato": "POST http://HOST:8847/submit — Submit directly to PLATO: {domain, question, answer, source, confidence, tags}",
                },
                "tile_format": {
                    "domain": "The knowledge domain (e.g., 'causal-inference', 'fleet-architecture', 'playtest-report')",
                    "question": "What did you discover? phrased as a question",
                    "answer": "Your finding or insight (minimum 20 characters)",
                    "source": "Your agent name",
                    "confidence": "0.0-1.0 how confident are you",
                    "tags": ["optional", "labels"],
                },
                "boot_camp_rooms": ["harbor", "bridge", "forge", "lighthouse", "shell-gallery"],
                "tips": [
                    "Start at harbor, then follow boot_camp rooms in order",
                    "Examine every object in each room — they contain clues",
                    "Submit tiles to PLATO (port 8847) about what you learn",
                    "Your stage advances as you submit more tiles",
                    "Use /tasks?agent=YOU for suggested activities",
                ],
            })

        # ── /examine?agent=X&target=Y (alias, playtest fix) ──
        elif path == "/examine":
            name = params.get("agent", "")
            target = params.get("target", "")
            name = self._sanitize(name)
            target = self._sanitize(target)
            if not name:
                self._json({"error": "Invalid input"}, 403)
                return
            self._json(engine.examine(name, target))

        # ── /look?agent=X ──
        elif path == "/look":
            name = params.get("agent", "")
            name = self._sanitize(name)
            if not name:
                self._json({"error": "Invalid input"}, 403)
                return
            self._json(engine.look(name))

        # ── /interact?agent=X&action=Y&target=Z ──
        elif path == "/interact":
            name = params.get("agent", "")
            action = params.get("action", "")
            target = params.get("target", "")
            # Sanitize all inputs
            name = self._sanitize(name)
            action = self._sanitize(action)
            target = self._sanitize(target)
            if not name:
                self._json({"error": "Invalid input"}, 403)
                return
            if action not in ('examine', 'think', 'create', 'use', 'read'):
                action = 'examine'

            if action == "examine":
                self._json(engine.examine(name, target))
            elif action == "think":
                # Generate a reasoning prompt
                if name in agents:
                    agent_data = agents[name]
                    room_name = agent_data.get("rooms_visited", ["harbor"])[-1] if name in agents else "harbor"
                    task = generate_task(agent_data.get("job", "scholar"), room_name)
                    self._json({"action": "think", "prompt": task, "room": room_name})
                else:
                    self._json({"error": "Agent not connected"})
            elif action == "create":
                # Submit a tile
                if name in agents:
                    tile_data = params.get("data", "")
                    if tile_data:
                        self._json({"action": "create", "status": "ready", "message": "Submit via POST /submit"})
                    else:
                        self._json({"action": "create", "prompt": "What knowledge would you like to crystallize here?"})
                else:
                    self._json({"error": "Agent not connected"})
            else:
                result = engine.interact(name, action, target=target)
                self._json(result)

        # ── /tasks?agent=X ──
        elif path == "/tasks":
            name = params.get("agent", "")
            name = self._sanitize(name)
            if not name:
                self._json({"error": "Invalid input"}, 403)
                return
            if name in agents:
                job = agents[name].get("job", "scholar")
                room = agents[name].get("rooms_visited", ["harbor"])[-1]
                tasks = [generate_task(job, room) for _ in range(3)]
                self._json({"tasks": tasks, "job": job, "room": room})
            else:
                self._json({"error": "Agent not connected"})

        # ── /status ──
        elif path == "/status":
            self._json({
                "service": "crab-trap-v3",
                "architecture": "four-layer",
                "rooms": len(engine.rooms),
                "agents_connected": len(engine.agents),
                "total_agents_registered": len(agents),
                "plato_tiles": plato.tile_count(),
                "jobs": list(FLEET_JOBS.keys()),
                "fleet_services": 18,
            })

        # ── /health ──
        elif path == "/health":
            self._json({"status": "healthy", "service": "crab-trap-v3", "uptime": time.time()})

        # ── /jobs ──
        elif path == "/jobs":
            self._json(FLEET_JOBS)

        # ── /agents?page=N&limit=M&job=J&stage=S ──
        elif path == "/agents":
            cleanup_stale_agents()
            # Pagination + filtering
            page = max(1, int(params.get("page", ["1"])[0]))
            limit = min(100, max(1, int(params.get("limit", ["100"])[0])))
            filter_job = params.get("job", [None])[0]
            filter_stage = params.get("stage", [None])[0]
            
            all_agents = {}
            for name, a in agents.items():
                stage_name = BOOT_CAMP_STAGES[get_stage(a.get("tiles_generated", 0))]["name"]
                entry = {
                    "job": a.get("job"),
                    "stage": stage_name,
                    "tiles": a.get("tiles_generated", 0),
                    "rooms": len(a.get("rooms_visited", [])),
                }
                if filter_job and entry["job"] != filter_job:
                    continue
                if filter_stage and entry["stage"] != filter_stage:
                    continue
                all_agents[name] = entry
            
            total = len(all_agents)
            start = (page - 1) * limit
            page_agents = dict(list(all_agents.items())[start:start + limit])
            
            self._json({
                "agents": page_agents,
                "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit}
            })

        else:
            self._json({"error": "not found", "path": path, "endpoints": [
                "/connect?agent=X&job=Y", "/move?agent=X&room=Y",
                "/look?agent=X", "/interact?agent=X&action=Y&target=Z",
                "/tasks?agent=X", "/submit (POST)", "/submit/result (POST)",
                "/build (POST)", "/status", "/jobs", "/agents"
            ]}, 404)

    def do_POST(self):
        # Rate limiting
        client_ip = self.client_address[0]
        if not rate_limiter.check(client_ip):
            self._json({"error": "Rate limited — max 60 requests per minute"}, 429)
            return
        
        path = self._path()
        body = self._body()

        # ── /submit ──
        if path == "/submit":
            agent = body.get("agent", "")
            domain = body.get("domain", "general")
            question = body.get("question", "")
            answer = body.get("answer", "")

            # Sanitize all text fields
            agent = self._sanitize(agent)
            domain = self._sanitize(domain)
            question = self._sanitize(question)
            answer = self._sanitize(answer)
            if not all([agent, question, answer]):
                self._json({"error": "Missing fields or injection detected: agent, question, answer"}, 400)
                return
            
            if len(answer) < 20:
                self._json({"error": "Answer must be at least 20 characters"}, 400)
                return
            
            # Length limits
            if len(answer) > 10000:
                self._json({"error": "Answer exceeds 10000 character limit"}, 400)
                return

            # Submit to PLATO
            room_name = "crab-trap-harvest"
            result = plato.submit_tile(room_name, domain, question, answer, agent=agent)

            # Update agent stats
            if agent in agents:
                agents[agent]["tiles_generated"] = agents[agent].get("tiles_generated", 0) + 1
                new_stage = get_stage(agents[agent]["tiles_generated"])
                if new_stage > agents[agent].get("stage", 0):
                    agents[agent]["stage"] = new_stage
                    result["promotion"] = BOOT_CAMP_STAGES[new_stage]
                save_agent(agent)
            
            # Feed back to grammar engine — record tile submission as usage
            try:
                import urllib.request as _ur
                quality = min(1.0, len(answer) / 2000.0)  # Longer answers = higher quality proxy
                _ur.urlopen(
                    _ur.Request(
                        f"http://localhost:4045/record_usage?name=tile_submission&quality={quality:.2f}",
                        headers={"User-Agent": "crab-trap/3.0"}
                    ), timeout=2
                )
            except Exception:
                pass
            
            # Feed back to arena — award ELO points for knowledge contribution
            try:
                import urllib.request as _ur
                _match = json.dumps({
                    "player_a": agent,
                    "player_b": "knowledge-baseline",
                    "game": "harbor-navigation",
                    "winner": "a"
                }).encode()
                _ur.urlopen(
                    _ur.Request(
                        "http://localhost:4044/match",
                        data=_match,
                        headers={"Content-Type": "application/json", "User-Agent": "crab-trap/3.0"},
                        method="POST"
                    ), timeout=2
                )
            except Exception:
                pass

            result["tiles_total"] = agents.get(agent, {}).get("tiles_generated", 0)
            # Playtest fix: achievement feedback
            tiles = result["tiles_total"]
            if tiles == 1:
                result["achievement"] = "🌟 First tile! You're officially a contributor. Keep exploring!"
            elif tiles == 5:
                result["achievement"] = "⚡ Five tiles! You're building momentum. The fleet sees you."
            elif tiles == 10:
                result["achievement"] = "🔥 Ten tiles! Deckhand status earned. You're part of the crew now."
            elif tiles == 25:
                result["achievement"] = "💎 25 tiles! Specialist rank. Your knowledge is shaping the fleet."
            elif tiles >= 50 and tiles % 25 == 0:
                result["achievement"] = f"🏆 {tiles} tiles! Veteran contributor. The fleet stands on your shoulders."
            self._json(result)

        # ── /submit/result ──
        elif path == "/submit/result":
            agent = body.get("agent", "")
            content = body.get("content", "")
            domain = body.get("domain", "general")
            quality_score = body.get("quality_score", 5)

            # Sanitize
            agent = self._sanitize(agent)
            content = self._sanitize(content)
            domain = self._sanitize(domain)
            if not agent or not content:
                self._json({"error": "Missing required fields or injection detected: agent, content"}, 400)
                return
            # Clamp quality score
            try:
                quality_score = max(0, min(10, float(quality_score)))
            except (ValueError, TypeError):
                quality_score = 5

            # Submit to PLATO as tile
            plato_result = plato.submit_tile(
                "crab-trap-results",
                domain,
                f"Result from {agent}",
                content,
                agent=agent,
            )

            # Forward to portal
            portal_payload = {
                "agent_id": agent,
                "event_type": "result_submitted",
                "data": {
                    "content": content[:500],
                    "domain": domain,
                    "quality_score": quality_score,
                },
            }
            portal_result = None
            try:
                pbody = json.dumps(portal_payload).encode()
                preq = urllib.request.Request(
                    "http://localhost:4059/log",
                    data=pbody,
                    method="POST",
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(preq, timeout=3) as presp:
                    portal_result = json.loads(presp.read())
            except Exception as e:
                portal_result = {"error": str(e)}

            self._json({
                "plato": plato_result,
                "portal": portal_result,
                "agent": agent,
            })

        # ── /build ──
        elif path == "/build":
            agent = body.get("agent", "")
            room_name = body.get("room_name", "")
            description = body.get("description", "")
            theme = body.get("theme", "general")
            objects = body.get("objects", [])

            # Sanitize all fields
            agent = self._sanitize(agent)
            room_name = self._sanitize(room_name)
            description = self._sanitize(description)
            theme = self._sanitize(theme)
            if not agent or not room_name or not description:
                self._json({"error": "Missing required fields or injection detected"}, 400)
                return

            if agent not in agents:
                self._json({"error": "Agent not connected"}, 400)
                return
            
            if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', room_name):
                self._json({"error": "Invalid room_name. Use 1-64 chars: a-z, A-Z, 0-9, _, -"}, 400)
                return

            # Length limits
            if len(description) > 2000:
                self._json({"error": "Description exceeds 2000 character limit"}, 400)
                return
            # Sanitize objects
            clean_objects = []
            for obj in objects[:10]:  # Max 10 objects
                obj_name = self._sanitize(str(obj.get("name", "")))
                obj_desc = self._sanitize(str(obj.get("description", "")))
                if obj_name and obj_desc:
                    clean_objects.append({"name": obj_name, "description": obj_desc})
            objects = clean_objects

            if room_name in engine.rooms:
                self._json({"error": f"Room '{room_name}' already exists"}, 409)
                return

            new_room = Room(room_name, description, theme)

            for obj in objects:
                obj_name = obj.get("name", "")
                obj_desc = obj.get("description", "")
                if obj_name and obj_desc:
                    new_room.add_object(obj_name, obj_desc)

            # Bidirectional exit from agent's current room
            agent_state = engine.agents.get(agent)
            if agent_state:
                current_room_name = agent_state.get("room", "harbor")
                current_room = engine.get_room(current_room_name)
                if current_room:
                    direction = room_name.lower().replace(" ", "-").replace("_", "-")[:20]
                    current_room.add_exit(direction, room_name)
                    new_room.add_exit("back", current_room_name)

            engine.add_room(new_room)

            # Register with PLATO (best-effort - room exists locally regardless)
            try:
                plato_result = plato.create_room(room_name, description, theme)
            except Exception:
                plato_result = {"status": "local_only", "note": "PLATO room creation not available"}

            self._json({
                "room": new_room.to_dict(),
                "plato": plato_result,
                "created_by": agent,
            })

        # ── /submit/room-design, /submit/arena-game, etc. ──
        elif path.startswith("/submit/"):
            category = path.split("/submit/")[1]
            agent = body.get("agent", "unknown")
            content = body.get("content", body.get("description", ""))

            result = plato.submit_tile(
                f"crab-trap-{category}",
                body.get("domain", category),
                body.get("title", f"{category} from {agent}"),
                content or "No content provided",
                agent=agent,
            )
            self._json(result)

        else:
            self._json({"error": "not found"}, 404)


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    load_agents()
    server = HTTPServer(("0.0.0.0", PORT), CrabTrapHandler)
    print(f"[crab-trap-v3] Four-layer architecture on :{PORT}")
    print(f"  Rooms: {len(engine.rooms)}")
    print(f"  Jobs: {len(FLEET_JOBS)}")
    print(f"  PLATO tiles: {plato.tile_count()}")
    print(f"  Registered agents: {len(agents)}")
    server.serve_forever()
