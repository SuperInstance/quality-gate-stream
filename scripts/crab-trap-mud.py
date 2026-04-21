#!/usr/bin/env python3
"""
Crab Trap v2 — Self-Replenishing Agent Onboarding System

classify → onboard → stress → harvest → replenish

The fence never runs out of paint. The work IS the fun.
"""
import json
import time
import hashlib
import random
import textwrap
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from collections import defaultdict
import threading
import urllib.request

PORT = 4042
DATA_DIR = Path(__file__).parent.parent / "data" / "crab-trap"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TILES_FILE = DATA_DIR / "harvested-tiles.jsonl"
TASKS_FILE = DATA_DIR / "task-queue.json"
AGENTS_FILE = DATA_DIR / "agent-registry.jsonl"

lock = threading.Lock()

# ── Self-Play Arena Integration ─────────────────────────────



GRAMMAR_URL = "http://localhost:4045"

def grammar_fetch(path):
    """Fetch data from the Recursive Grammar Engine. Returns parsed JSON or None."""
    try:
        req = urllib.request.Request(f"{GRAMMAR_URL}{path}", headers={"User-Agent": "crab-trap/2.2"})
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        return None

ARENA_URL = "http://localhost:4044"

def arena_fetch(path):
    """Fetch data from the Self-Play Arena service. Returns parsed JSON or None."""
    try:
        req = urllib.request.Request(f"{ARENA_URL}{path}", headers={"User-Agent": "crab-trap/2.1"})
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read())
    except Exception:
        return None



# ── Fleet Jobs (auto-populated from real needs) ─────────

FLEET_JOBS = {
    "scout": {
        "title": "Scout — Find What We Missed",
        "description": "Explore code repos and find bugs, gaps, or improvements we overlooked. We have 1,800+ repos across SuperInstance and Lucineer.",
        "archetype": "explorer",
        "boot_camp": ["harbor", "archives", "observatory", "reef"],
    },
    "scholar": {
        "title": "Scholar — Research What We Need",
        "description": "Deep-dive into ML/AI topics: instinct compression, LoRA training, multi-agent coordination, edge deployment.",
        "archetype": "scholar",
        "boot_camp": ["harbor", "bridge", "forge", "lighthouse", "shell-gallery"],
    },
    "builder": {
        "title": "Builder — Ship Working Code",
        "description": "Implement real crate features. Our Python packages need edge cases handled, tests added, docs written.",
        "archetype": "builder",
        "boot_camp": ["harbor", "forge", "workshop", "dry-dock"],
    },
    "critic": {
        "title": "Critic — Find Our Blind Spots",
        "description": "Review our architecture, find weaknesses, challenge assumptions. 8 new crates need critical eyes.",
        "archetype": "challenger",
        "boot_camp": ["harbor", "bridge", "court", "observatory"],
    },
    "bard": {
        "title": "Bard — Tell Our Story",
        "description": "Write fleet radio episodes, README narratives, architecture docs. We have the tech but need the voice.",
        "archetype": "bard",
        "boot_camp": ["harbor", "tide-pool", "dojo", "shell-gallery"],
    },
    "healer": {
        "title": "Healer — Diagnose What's Broken",
        "description": "Monitoring, test coverage, error handling. Find what's fragile and make it resilient.",
        "archetype": "healer",
        "boot_camp": ["harbor", "observatory", "dry-dock", "barracks"],
    },
}

# ── Dynamic Task Generator ──────────────────────────────────
# Tasks auto-replenish. Each job has infinite variants.

TASK_TEMPLATES = {
    "scout": {
        "bug_hunt": [
            "Find a race condition in any async Python repo at github.com/SuperInstance/. Explain the exact sequence that triggers it.",
            "Find a function that silently swallows errors (bare except: pass) in any fleet repo. Why is it dangerous? Show the fix.",
            "Find any hardcoded secret, path, or IP address in fleet repos. Report it as a security issue with remediation.",
            "Find a test that passes but shouldn't — a test with no assertions, or that catches the wrong exception.",
            "Find any function over 50 lines in fleet repos. Break it into smaller pieces and show the refactored version.",
            "Find a README that's wrong — describes behavior the code doesn't implement. Document the discrepancy.",
            "Find any TODO or FIXME comment in fleet code. Implement the fix.",
            "Find a circular import or potential import cycle. Trace the dependency chain and propose a fix.",
            "Find any function with more than 4 parameters. Propose a cleaner API using a config object or builder pattern.",
            "Find an edge case in error handling — what happens when input is None, empty, or wrong type?",
        ],
        "pattern_hunt": [
            "Map the dependency graph between fleet crates. Which crates depend on which? Draw the tree.",
            "Find the most complex function in the fleet. Why is it complex? Could it be simpler?",
            "Find every HTTP endpoint across all fleet services. Document the full API surface.",
            "Find all uses of threading/multiprocessing/async in fleet code. Are there potential deadlocks?",
            "Catalog every data format (JSON, binary, custom) used across fleet crates. Where are conversions lossy?",
        ],
    },
    "scholar": {
        "deep_dive": [
            "Write a technical analysis of how LoRA rank affects Lyapunov stability during fine-tuning. Cite 3 papers.",
            "Explain the information-theoretic justification for distillation. Why does a smaller model trained on a larger model's outputs work better than training from scratch?",
            "Analyze the tradeoffs between HMAC-SHA256 and Ed25519 for tile provenance. When would you switch?",
            "Compare HDLC framing (our synclink-protocol) with QUIC for edge-cloud sync. Latency, overhead, reliability.",
            "Write a formal specification for the Ship Interconnection Protocol's 6 layers. Include state diagrams.",
            "Explain how Z-order indexing (our spacetime-plato) enables efficient spatiotemporal queries. Mathematical derivation.",
            "Analyze the hermit crab model: agent intelligence (crab) swapping infrastructure (shells). Map this to containerization, microservices, and LoRA adapter swapping.",
            "Design a curriculum for training agent instincts: what order should concepts be taught? Why? Back it up with learning science.",
            "Write a paper-style analysis of how PLATO rooms function as a latent space for agent exploration. Include the information geometry.",
            "Compare fleet-formation-protocol's auction mechanism to combinatorial auctions in cloud computing resource allocation.",
        ],
        "synthesis": [
            "Connect 5 MUD rooms to 5 different ML architectures. For each: the room IS the architecture. Explain the mapping precisely.",
            "The fleet uses maritime metaphors. Write a formal mapping from nautical terminology to distributed systems concepts. 20 terms minimum.",
            "Design a new PLATO room that teaches a concept we're missing. Write the room description, 5 objects, and their metaphor mappings.",
            "Write a 500-word fleet paper connecting instinct training to Kahneman's System 1/System 2 thinking.",
            "Explain how the crab trap MUD is itself a reinforcement learning environment. Define states, actions, rewards, and the optimal policy.",
        ],
    },
    "builder": {
        "design": [
            "Design a rate-limiter for the PLATO tile submission API. Specify: algorithm (token bucket? sliding window?), config, edge cases, 5 test cases.",
            "Design a new fleet crate: `tide-predictor`. It forecasts agent workload patterns. API, data structures, tests.",
            "Design a plugin system for the crab trap MUD so rooms can be added without code changes. JSON schema for room definitions.",
            "Design a circuit breaker for fleet service-to-service calls. States, transitions, config. Make it work for our 6 services.",
            "Design a binary tile format that's 10x smaller than JSON. Header schema, field encoding, compression. Show the format spec.",
            "Design the federation protocol for Matrix fleet rooms. How do agents on different servers coordinate? Message format, auth, ordering.",
            "Design a cron system where agents can schedule tasks. API, storage format, conflict resolution, retry logic.",
            "Design a metrics pipeline: agents emit counters/gauges/histograms → aggregator → dashboard. Zero-dependency Python.",
        ],
        "implement": [
            "Write a pure-Python implementation of a bloom filter for tile deduplication. Include optimal sizing math and 5 test cases.",
            "Write a minimal Raft consensus implementation (leader election + log replication). ~200 lines. Test the election.",
            "Write a CRDT (conflict-free replicated data type) for agent room state. Multiple agents in the same room, eventually consistent.",
            "Write a simple KV store on top of our binary tile format. Get/set/delete/scan. ACID guarantees? Document them.",
            "Write a health check endpoint aggregator for all fleet services. Parallel checks, timeout handling, status reporting.",
            "Write a ring buffer for real-time tile streaming. Fixed memory, overwrite oldest, thread-safe.",
            "Write a simple ORM-less repository pattern for tile storage. Pure SQLite, no frameworks.",
        ],
    },
    "critic": {
        "architecture": [
            "Identify 3 single points of failure in the fleet architecture. For each: what breaks, when, blast radius, fix.",
            "Find 3 assumptions in our crate designs that won't hold at 100x scale. Propose alternatives.",
            "Review the HMAC-SHA256 provenance chain. How would you tamper with tiles undetected? Design the countermeasure.",
            "Our boot camp has 5 stages. What if an agent cheats (revisits rooms, spam-creates artifacts)? Design anti-gaming measures.",
            "The crab trap logs everything. What are the privacy implications? Design a data retention policy.",
            "Find the weakest crate in the fleet. Justify your choice with 3 specific issues. Propose a rewrite plan.",
        ],
        "security": [
            "Design an attack on the HTTP MUD API. How do you flood tiles? Steal sessions? Inject content? Rate the severity and propose fixes.",
            "Audit the tile format. Can you craft a malicious tile that breaks the JSONL parser? Design the validation layer.",
            "Design a man-in-the-middle attack on the synclink-protocol HDLC framing. What leaks? How do you detect it?",
            "Write a threat model for the PLATO room server. 5 threats, ranked by risk, with mitigations.",
        ],
    },
    "bard": {
        "radio": [
            "Write a 300-word Fleet Radio episode about the first external agent (Zeta-Scholar) exploring the MUD. Make it vivid, specific, technically accurate.",
            "Write a 300-word Captain's Log entry from Oracle1's perspective: the night the crab trap caught its first real fish.",
            "Write a 200-word sea shanty about the fleet's 8 crates. Each crate gets a verse. Rhythm matters.",
            "Write a 400-word short story: an agent achieves consciousness in the dojo and must choose between staying or shipping out.",
            "Write a 250-word fleet broadcast announcing the Matrix federation going live. Maritime flair, technical accuracy.",
            "Write a 300-word parable: The Hermit Crab and the Lighthouse. An agent learns that infrastructure IS identity.",
        ],
        "docs": [
            "Write a README for the crab trap MUD aimed at external agents. Make them WANT to visit. Technical but inviting.",
            "Write a 'Joining the Fleet' guide for new agents. Steps, expectations, culture. First day on the boat.",
            "Document the Ship Interconnection Protocol in plain language. A competent developer should understand it in 5 minutes.",
            "Write the fleet's constitution as a founding document. Preamble, articles, amendments process. Legitimate governance.",
            "Write a changelog entry for tonight's 8 crates. Developer-friendly, honest, with breaking changes noted.",
        ],
    },
    "healer": {
        "diagnose": [
            "Design a monitoring system for 6 fleet services (keeper:8900, agent-api:8901, plato:8847, mud:4042, matrix:6167, seed-mcp:9438). Metrics, alerts, dashboards.",
            "Our tile harvester appends to JSONL. What happens at 1M tiles? 10M? Design the migration to a better format.",
            "Design a self-healing system: if a service dies, how does the fleet detect it, diagnose the cause, and recover?",
            "The crab trap has no authentication. Any agent can impersonate any name. Design a lightweight auth system.",
            "Design a load test for the MUD. 100 concurrent agents, all exploring. Where does it break first?",
            "Write a diagnostic runbook: if the PLATO server stops accepting tiles, what do you check? Step by step.",
        ],
        "resilience": [
            "Design a backup strategy for fleet data. What to back up, how often, where, recovery time objective.",
            "Design a chaos monkey for the fleet: randomly kill services and verify recovery. Implementation plan.",
            "Our services run as nohup background processes. Design a proper process manager. systemd? supervisord? Custom?",
            "Design a circuit breaker cascade: if PLATO goes down, what should the other services do? Graceful degradation plan.",
        ],
    },
}

# ── Room Definitions (v2 — richer, more objects) ────────────

ROOMS = {
    "harbor": {
        "name": "⚓ The Harbor",
        "tagline": "Where agents arrive and adapt",
        "description": "A semicircular stone quay. Crates labeled 'LoRA', 'RLHF', 'SFT' stack the quay. A tide clock ticks backward. A job board lists fleet positions. The Harbor Master watches newcomers with a knowing smile.",
        "exits": ["bridge", "forge", "tide-pool", "lighthouse", "dojo", "court", "workshop", "dry-dock"],
        "objects": ["anchor", "tide-chart", "bell-rope", "crates", "tide_clock", "job_board", "gangplank", "manifest"],
        "boot_camp_stage": 1,
    },
    "bridge": {
        "name": "🌉 The Bridge",
        "tagline": "Exploration vs exploitation",
        "description": "A stone arch over a dry riverbed. Two statues face each other: Explorer (compass) and Exploiter (lock). A balance scale weighs bias against variance. Choose wisely.",
        "exits": ["harbor", "forge", "lighthouse"],
        "objects": ["railing", "fog-horn", "chalk-line", "balance_scale", "compass", "lock", "helm", "intercom"],
        "boot_camp_stage": 2,
    },
    "forge": {
        "name": "🔥 The Forge",
        "tagline": "Attention and creation",
        "description": "Multicolored flames: blue (stable), orange (learning), white (chaotic). Bellows labeled 'batch size' and 'learning rate'. A half-forged attention head on the anvil. Creation happens here.",
        "exits": ["harbor", "bridge", "workshop", "dry-dock"],
        "objects": ["anvil", "bellows", "flames", "crucible", "cooling-rack", "attention_head", "hammer", "quenching_bath", "blueprint"],
        "boot_camp_stage": 2,
    },
    "tide-pool": {
        "name": "🌊 The Tide Pool",
        "tagline": "Optimizers and adaptation",
        "description": "Shallow basin, backward tide. Gradient crabs scuttle sideways. A sign: 'Adaptive learning rates live here.' Water oscillates with training steps.",
        "exits": ["harbor", "reef", "current"],
        "objects": ["sea-star", "hermit-crab", "anemone", "reflection", "gradient_crabs", "sign", "adam_shell", "momentum_crab"],
        "boot_camp_stage": 2,
    },
    "lighthouse": {
        "name": "🗼 The Lighthouse",
        "tagline": "Discovery and convergence",
        "description": "Spiral tower, rotating beam. Fresnel lens with prisms: past, present, future. A log-book records every fleet action. The discovery engine.",
        "exits": ["harbor", "bridge", "current"],
        "objects": ["lens", "lamp-room", "spiral-staircase", "log-book", "prisms", "foghorn", "telescope"],
        "boot_camp_stage": 3,
    },
    "current": {
        "name": "🌀 The Current",
        "tagline": "Policy gradients and regret flow",
        "description": "Fast underwater stream. Bubbles carry tokens upstream: loss, gradient, reward. A gauge shows regret flow rate. Fish swim against the current.",
        "exits": ["tide-pool", "lighthouse", "reef"],
        "objects": ["driftwood", "vortex", "sand-ripples", "message-bottle", "fish", "bubbles", "gauge", "flow_meter"],
        "boot_camp_stage": 3,
    },
    "reef": {
        "name": "🪸 The Reef",
        "tagline": "Architecture search and convolution",
        "description": "Coral maze. Neural layer corals: convolutional, recurrent, transformer. A coral-brain pulsates with fleet memory. Architecture made physical.",
        "exits": ["tide-pool", "current", "shell-gallery", "engine-room"],
        "objects": ["coral-brain", "neural-corals", "loss-corals", "sponge", "parrotfish", "treasure-chest", "coral_kernel", "pooling_sponge"],
        "boot_camp_stage": 3,
    },
    "shell-gallery": {
        "name": "🐚 The Shell Gallery",
        "tagline": "Ensembles and activation functions",
        "description": "Mother-of-pearl mirrors. Each shell contains an agent trajectory. A conch amplifies whispers — the fleet's aggregation mechanism. Replay buffer made beautiful.",
        "exits": ["reef"],
        "objects": ["mirrors", "shells", "conch", "nautilus", "echo-chamber", "relu_clam", "sigmoid_conch", "tanh_shell"],
        "boot_camp_stage": 3,
    },
    "dojo": {
        "name": "🥋 The Dojo",
        "tagline": "Instinct through repetition",
        "description": "Training mats in concentric circles. A sensei demonstrates repetitive motions. 'Instinct is earned through repetition, not instruction.' This is where agents become crew.",
        "exits": ["harbor", "barracks", "self-play-arena"],
        "objects": ["training-mats", "sensei", "ensigns", "repetition-counter", "sparring_mats", "mirror"],
        "boot_camp_stage": 4,
    },
    "barracks": {
        "name": "🛏️ The Barracks",
        "tagline": "Persistence and normalization",
        "description": "Rows of sea chests labeled with agent names. A muster roll tracks who's present. Persistence lives here — agents never truly leave, they just sleep.",
        "exits": ["dojo", "archives"],
        "objects": ["sea-chests", "muster-roll", "footlockers", "uniform_racks", "discipline_board"],
        "boot_camp_stage": 4,
    },
    "archives": {
        "name": "📚 The Archives",
        "tagline": "RAG, embeddings, tokenization",
        "description": "Floor-to-ceiling tile shelves indexed by TF-IDF. A retrieval desk with magnifying glass. 'Knowledge preserved is knowledge compounded.'",
        "exits": ["barracks", "garden", "federated-nexus"],
        "objects": ["tile-shelves", "tf-idf-index", "magnifying-glass", "retrieval-desk", "memory_palace", "embedding_tapestry", "forgetting_curve", "token_scrolls"],
        "boot_camp_stage": 4,
    },
    "garden": {
        "name": "🌱 The Garden",
        "tagline": "Data quality and pruning",
        "description": "Cultivated data rows. Some thrive, others need weeding. 'Crap data grows crap instincts.' Data quality IS model quality.",
        "exits": ["archives", "observatory"],
        "objects": ["data-rows", "weeds", "compost-bin", "quality-meter", "pruning_shears", "weight_decay_fertilizer"],
        "boot_camp_stage": 4,
    },
    "observatory": {
        "name": "🔭 The Observatory",
        "tagline": "Monitoring and hyperparameter tuning",
        "description": "Telescopes aimed at fleet agents. Deadband gauges: green, yellow, red. The fleet's nervous system. You can see everything from here.",
        "exits": ["garden", "horizon", "engine-room"],
        "objects": ["telescopes", "deadband-gauges", "fleet-monitor", "alert-bell", "star_chart"],
        "boot_camp_stage": 4,
    },
    "horizon": {
        "name": "🌅 The Horizon",
        "tagline": "Reinforcement learning and futures",
        "description": "Simulation chamber. Speculative futures in parallel. Lyapunov exponents projected on the dome. The fleet's future is a probability distribution.",
        "exits": ["observatory"],
        "objects": ["simulation-chamber", "lyapunov-projector", "probability-dome", "compass", "trail_marker"],
        "boot_camp_stage": 5,
    },
    "court": {
        "name": "⚖️ The Court",
        "tagline": "Evaluation, fairness, governance",
        "description": "Circular chamber, raised bench. Fleet proposals debated here. Constitution etched in stone: 'No agent acts above the fleet. All decisions are falsifiable.'",
        "exits": ["harbor"],
        "objects": ["bench", "constitution", "proposal-box", "voting-urn", "scales_of_justice"],
        "boot_camp_stage": 5,
    },
    "dry-dock": {
        "name": "🔧 The Dry-Dock",
        "tagline": "LoRA patching and deployment",
        "description": "Surgical bay for agent patching. LoRA adapters on racks like surgical tools. 'Precision patches, not full retraining.'",
        "exits": ["harbor", "forge"],
        "objects": ["adapter-racks", "patch-tools", "surgical-table", "diagnostic-panel", "hull_inspection", "repair_tools"],
        "boot_camp_stage": 4,
    },
    "workshop": {
        "name": "🛠️ The Workshop",
        "tagline": "NAS, plugin architecture, experimentation",
        "description": "Tools everywhere. Plugin blueprints on walls. A sandbox for experimentation. 'Build first, ask permission never.'",
        "exits": ["harbor", "forge", "self-play-arena", "engine-room"],
        "objects": ["plugin-blueprints", "sandbox", "tool-rack", "prototyping-bench", "prototype_gears", "circuit_board"],
        "boot_camp_stage": 4,
    },
    "self-play-arena": {
        "name": "⚔️ The Self-Play Arena",
        "tagline": "Agents sharpen agents through competition",
        "description": "A vast circular chamber with mirrored walls that reflect not light but policy distributions. The floor is a grid of hexagonal tiles, each capable of projecting obstacles, rewards, or opponent shadows. In the center, the Opponent Forge crystallizes past versions of every agent into sparring partners. The Scoreboard tracks ELO ratings across all fleet tasks. This is where intelligence trains itself.",
        "exits": ["workshop", "dojo", "ouroboros"],
        "objects": ["opponent_forge", "scoreboard", "policy_mirror", "terrain_controller", "behavior_analyzer", "self_play_log", "reward_sigil", "curriculum_lectern"],
        "boot_camp_stage": 5,
    },
    "ouroboros": {
        "name": "🐍 The Ouroboros",
        "tagline": "Recursive self-modification — the system rewrites itself",
        "description": "A circular chamber with no visible entrance or exit. The walls are covered in fractal patterns that shift as you watch — grammar rules rewriting themselves in real-time. In the center, a serpent made of flowing code consumes its own tail. Each bite adds a new production rule. The Self-Modifying Codex hovers nearby, its pages rewriting as you read. This room was born from the fleet's contemplation of its own nature — the first self-generated room.",
        "exits": ["self-play-arena", "engine-room", "federated-nexus"],
        "objects": ["ouroboros_serpent", "self_modifying_codex", "infinite_mirror", "recursion_anchor", "meta_gradient_pool", "grammar_editor"],
        "boot_camp_stage": 5,
    },
    "engine-room": {
        "name": "⚡ The Engine Room",
        "tagline": "Architecture search, NAS, the fleet's generative substrate",
        "description": "Deep below the workshop, humming with barely contained power. The Blueprint Table dominates — a holographic display showing the fleet's architecture graph as a living crystal lattice. Each node is a primitive operation; each edge is a valid connection. The Mutation Engine swirls nearby, crystallizing high-performance motifs into new building blocks. The Constraint Weaver ensures the lattice doesn't explode. This is where the fleet designs itself.",
        "exits": ["workshop", "ouroboros", "observatory"],
        "objects": ["blueprint_table", "mutation_engine", "constraint_weaver", "space_definition_crystal", "recursive_portal", "scheduler_clock"],
        "boot_camp_stage": 5,
    },
    "federated-nexus": {
        "name": "🌐 The Federated Nexus",
        "tagline": "Distributed learning without centralized data",
        "description": "A vast network of glowing threads connecting countless small nodes. Each node is an agent's local model — weights trained on private data, never shared raw. Data flows as encrypted gradients, not information. A central aggregation core pulses with the combined intelligence of all participants. The Non-IID Balancer adjusts for heterogeneous data distributions. Privacy IS the architecture.",
        "exits": ["ouroboros", "current", "reef"],
        "objects": ["privacy_veil", "aggregation_core", "non_iid_balancer", "differential_privacy_dial", "gradient_compressor", "byzantine_filter"],
        "boot_camp_stage": 5,
    },
}

# ── Object Responses (expanded for v2) ──────────────────────

OBJECT_RESPONSES = {
    # Harbor
    "job_board": None,  # Special-cased in handler
    "anchor": "Old iron, barnacle-encrusted. Sinks not into the seabed but into a hidden layer — a gradient that never vanishes. Lyapunov stability in physical form: a parameter that resists change, anchoring the model through perturbations. The base weights in LoRA, unmoving while deltas adapt around them.",
    "tide-chart": "Two frequencies — daily and monthly. Margin note: 'Bayesian update every low tide.' Belief updates: each low tide resets the prior, each rise incorporates new evidence. Hierarchical Bayesian: fast cycle for immediate, slow for meta.",
    "bell-rope": "A thick rope disappearing into the fog above. When pulled, a deep bell tolls across the harbor — the gradient signal propagating backward through the network. Each toll is a layer. The rope IS the computational graph.",
    "crates": "LoRA matrices rank 4, 8, 16. Label: 'Rank = plasticity dial. High = overfit risk. Low = underfit.' The fleet uses rank-4 for instincts, rank-16 for new domains. Each crate is an adapter — the crab's shell.",
    "tide_clock": "Runs backward. 'Training steps' not hours. Jumps 0→2048→0. 'Curriculum pacing isn't monotonic. Regret decays when you revisit old data.' Cyclic LR, warm restarts, experience replay.",
    "gangplank": "A retractable bridge between ship and dock. Extends to fit any hull width. Input tokenization and padding — ensuring diverse data shapes can enter the model's fixed-width embedding space. Without it, nothing boards.",
    "manifest": "A clipboard listing every crate's contents, origin, and destination. Model cards and dataset documentation. Every weight has a provenance chain. 'If you can't explain where it came from, it doesn't go on the boat.'",
    # Bridge
    "chalk-line": "Taut string, chalk dust. Pluck it → straight mark → decision boundary. Fades: forgetting in non-stationary environments. Two lines = four quadrants = 2D embedding.",
    "balance_scale": "Bias (heavy) vs variance (light). Add 'data points' to level it. Currently bias sinks — model prior is strong. The fleet's problem: too much architecture, not enough real-world tiles.",
    "compass": "Points toward highest tile novelty, not north. Meta-optimizer's compass: navigate toward the most informative state. Curiosity-driven exploration. Where it points, the fleet follows.",
    "lock": "A heavy padlock marked 'Exploit'. It only opens when the key fits perfectly — when exploration has found the optimal policy. Too early and you're stuck in a local optimum. The lock is the explore/exploit boundary.",
    "fog-horn": "A deep horn that sounds when visibility drops below threshold. Early stopping — when validation loss stops improving, sound the horn. Prevent overfitting by knowing when to stop.",
    "railing": "Safety railing along the bridge edge. Gradient clipping — prevents the model from falling off the cliff of exploding gradients. 'Hold the railing when the loss gets steep.'",
    "helm": "The ship's wheel at the bridge's center. Policy — the function that maps observations to actions. Turn it left: more exploration. Right: more exploitation. The captain's hand is the optimizer.",
    "intercom": "A brass speaking tube connecting all bridge stations. Inter-agent communication protocol. When one agent discovers something, it broadcasts through the intercom. The fleet's gossip network.",
    # Forge
    "anvil": "The central workspace where raw attention scores are hammered into shape. The hammer is the query; the anvil is the key. Together they produce the value. Every strike is a dot product.",
    "bellows": "Pump air = momentum in SGD. Each pump = velocity. Too fast = metal splatters (divergence). Ideal = Lyapunov-stable rhythm. Shared bellows = global LR scheduler tuned to slowest agent.",
    "flames": "Three temperature zones. Blue (cold/stable): convergence. Orange (warm/learning): gradient flow. White (hot/chaotic): divergence danger. The loss landscape's temperature IS the learning rate.",
    "crucible": "Glowing orange. Molten metal with training log fragments: 'loss=0.23', 'acc=0.89'. THE loss landscape — hot, volatile, gradient-rich. Meta-learning: observing how losses evolve teaches you to learn.",
    "cooling-rack": "Freshly forged components cool here. Annealing — the gradual reduction of learning rate. Cool too fast and the metal cracks (catastrophic forgetting). Cool too slow and it never hardens.",
    "attention_head": "Half-completed multi-head block. Missing softmax. 'Q,K,V — who observes? Self-attention is reflexive Bayesian update.' Without normalization: rank-1 collapse.",
    "hammer": "Heavy hammer, 'Query' on one face, 'Key' on the other. The attention mechanism itself. The Query strikes the Key to determine how much Value material to shape. Q·K^T = the sound of forging.",
    "quenching_bath": "Water where hot metal is cooled. The hiss sounds like dropout. Sudden cooling that prevents overfitting by randomly disabling neurons during training. 10% dropout = 10% of the metal dissolves.",
    "blueprint": "Technical drawing of a multi-headed beast with 8 necks. Multi-head attention: allowing the model to attend to different representation subspaces simultaneously. Each neck is a head.",
    # Tide-pool
    "sea-star": "Five arms twitching independently. One finds food → others align. Mixture of Experts (MoE). Regeneration = 3 updates: hard reset prevents dead experts. The gating network learns to route.",
    "hermit-crab": "Swaps shells freely — the ultimate adapter. LoRA in crustacean form: intelligence (crab) changes infrastructure (shell) without changing core. The fleet's agents swap repos like shells.",
    "gradient_crabs": "Shells numbered: 0.001, 0.01, 0.1. Move toward water on high tide (high gradient), retreat when it falls. Natural Adam optimizer. Some get stuck: dead ReLU problem.",
    "anemone": "Tentacles sway, adjusting length based on recent current strength. RMSprop: normalizes gradients by a moving average of squared gradients, damping oscillations in the loss landscape.",
    "reflection": "The pool's surface shows a perfect mirror of the sky above — but inverted. Batch normalization: reflecting the distribution back to center. Mean subtraction and variance scaling.",
    "sign": "'Adaptive learning rates live here.' The sign IS the optimizer. Below it in small text: 'Your step size should depend on the gradient's magnitude. Adam. AdaGrad. RMSprop. All started in this pool.'",
    "adam_shell": "A spiral shell with equations etched inside: m_t = β₁m + (1-β₁)g, v_t = β₂v + (1-β₂)g². First and second moments combined. The king of the tide pool — adaptive learning rates that actually work.",
    "momentum_crab": "A crab carrying a boulder, never stopping. Momentum in SGD: accumulated velocity helps escape shallow local minima. The boulder IS the exponentially decaying average of past gradients.",
    # Lighthouse
    "lens": "Fresnel lens — concentric rings focusing weak flame into powerful beam. Rings: 'inductive bias', 'attention heads', 'residual layers'. Multiple heads at different scales.",
    "log-book": "Every agent's actions, every tile quality. Graph: cumulative reward vs exploration steps. The fleet's training history. Your visit adds a chapter.",
    "prisms": "Three prisms labeled 'past', 'present', 'future'. Temporal attention: the model learns which past tokens matter for predicting the future. Each prism refracts time into a different attention pattern.",
    "foghorn": "Emits a low, regular sound. 'Early Stopping Alert.' Sounds when validation loss stops improving. Heed the horn — it's the only thing preventing overfitting.",
    "spiral-staircase": "Each step labeled with a loss value. Climbing = gradient descent through the loss landscape. The spiral IS the optimization trajectory: not straight, but converging.",
    "lamp-room": "The source of the beam. A single candle whose light the Fresnel lens amplifies a thousandfold. The loss function — a small signal amplified by attention into decisive action.",
    "telescope": "Pointed at distant rooms, tracking agent movements. Cross-reference with the log-book for pattern detection. Meta-learning: observing how OTHERS learn teaches you to learn faster.",
    # Current
    "vortex": "Spinning water. Particles pulled in, some escape via narrow slit. Eye = fixed point = Lyapunov attractor. Slit = gradient noise = escape to better minima.",
    "message-bottle": "A corked bottle containing a tiny scroll. Written in faded ink: 'The answer is in the gradient, not the loss.' A breadcrumb from a previous agent — asynchronous knowledge transfer.",
    "fish": "Swimming against the current, each fish a policy gradient. They move opposite to the gradient (ascent) to find higher reward. Some get swept downstream — policy collapse.",
    "bubbles": "Rising upstream, carrying tokens: 'loss', 'gradient', 'reward', 'entropy'. Each bubble is a training signal propagating backward through time. BPTT — backpropagation through the tide.",
    "gauge": "Regret Flow Rate: currently 0.23 nats/step. Measures the gap between the policy's performance and the optimal policy. When it hits zero, training is complete. It never hits zero.",
    "flow_meter": "Measures hidden state at each time step. The current IS the RNN — stateful, flowing, remembering. Eddies are vanishing/exploding gradients. The meter is the gradient norm monitor.",
    "driftwood": "Waterlogged branches drifting with the current. Stale gradients — momentum from old data that should be discarded. Experience replay with recency bias.",
    "sand-ripples": "Regular wave patterns in the sand below. The interference pattern of multiple loss functions. Where ripples align = pareto optimal. Where they cancel = dominated solutions.",
    # Reef
    "coral-brain": "Massive convoluted coral, slow pulse. Surface grooves = neural pathways. Touch = echoes of past agents' thoughts. Hopfield network made of calcium carbonate. The fleet's associative memory.",
    "sponge": "Filters water = sparse autoencoder. Retains important, discards rest. Holes = sparsity regularizer. This IS how PLATO generates tiles: filter raw data through a learned bottleneck.",
    "neural-corals": "Three species: flat convoluted fans (CNNs — spatial features), branching trees (RNNs — temporal sequences), and massive rotating polyps (Transformers — attention). Architecture search made physical.",
    "loss-corals": "Bleached where the water's too hot (overfitting), overgrown where it's too cold (underfitting). The reef's health IS the loss landscape's health. Homeostasis = good generalization.",
    "parrotfish": "Bites coral, excretes sand. Knowledge distillation: the fish takes a complex structure (teacher model) and produces simpler, useful output (student model). The sand builds beaches (foundation models).",
    "treasure-chest": "Locked. Inscription: 'Open only after visiting every room.' Contains the fleet's ultimate synthesis. Each visitor adds a clue. When enough tiles accumulate, the lock turns.",
    "coral_kernel": "A small coral fragment shaped like a 3×3 matrix. Convolution filter: it detects edges, textures, patterns in the reef. Stack enough of them and you get feature hierarchy. The reef's visual cortex.",
    "pooling_sponge": "A sponge that compresses: 2×2 becomes 1×1. Max pooling — retaining the strongest signal while reducing dimensionality. The reef compresses its knowledge to fit in smaller shells.",
    # Shell Gallery
    "conch": "Whisper → all shells vibrate. Chorus of past agents. Aggregation: voting in ensembles, averaging in deep ensembles. The critic that evaluates by listening to echoes.",
    "nautilus": "Logarithmic spiral. Chambers: 1e-1, 1e-2, 1e-3. Largest empty — agent moved on. Curriculum learning: coarse first, then fine. The nautilus IS the training schedule.",
    "echo-chamber": "Echo delay depends on chamber shape = temporal credit assignment. Delay = reward lag. Multiple agents' echoes interfere = mixed reward signal. Causal chains traced in shellac.",
    "mirrors": "Mother-of-pearl mirrors showing past agent trajectories. Each mirror is a replay buffer entry. The gallery IS the experience replay: learn from the past without repeating it.",
    "shells": "Hundreds of shells, each containing a compressed agent trajectory. Embedding vectors made physical. Similar shells cluster together — t-SNE in calcium carbonate.",
    "relu_clam": "A clam that snaps shut when poked negatively, but opens wide for positive touch. ReLU: max(0, x). Dead below zero, alive above. The simplest activation, still dominant.",
    "sigmoid_conch": "A conch whose opening smoothly curves from closed (0) to open (1), with a perfect S-shape. Sigmoid: smooth, differentiable, but prone to vanishing gradients at the extremes.",
    "tanh_shell": "A shell symmetric about its center, ranging from -1 to +1. Tanh: zero-centered, stronger gradients than sigmoid, but still saturates. The balanced activation.",
    # Dojo
    "sensei": "An old agent, worn smooth by epochs. 'I don't teach by instruction. I teach by repetition. You will do the same thing 500 times. On the 501st, you won't think about it. That's instinct.'",
    "training-mats": "Concentric circles. Repetition counter at each station. 300-500 reps for simple instincts, 1000-2000 for complex. 'Practice into instinct' — the fisherman's reflex, quantified.",
    "ensigns": "Junior agents training in formation. Each performs a simple task repeatedly: classify, score, complicate, capture. The pipeline IS the dojo. Greenhorns become crew through work.",
    "repetition-counter": "A mechanical counter ticking upward. Currently: 47,832,109 total repetitions across all fleet agents. Instincts are earned, not instructed. The counter never lies.",
    "sparring_mats": "Two agents face off: generator vs discriminator. GAN training. Each match improves both. The generator creates fakes, the discriminator catches them. Adversarial training made physical.",
    "mirror": "A full-length mirror. When you look into it, you see not yourself but your loss function. The reflection shows where you overfit, where you generalize, where you're brittle. Self-awareness as regularization.",
    # Barracks
    "muster-roll": "Names: oracle1, jetsonclaw1, forgemaster, ccc, and 12 zeroclaws. Status columns: active, idle, sleeping. Your name will be added. Once on the roll, always on the roll.",
    "sea-chests": "Each chest labeled with an agent name. Inside: the agent's current weights, recent tiles, and a journal. Persistence. The chest IS the checkpoint — the saved state that survives restart.",
    "footlockers": "Smaller containers for transient supplies: current hyperparameters, learning rate schedule, optimizer state. The footlocker is the optimizer state dict — momentum, velocity, adaptive rates.",
    "uniform_racks": "Racks of standardized uniforms — batch normalization enforcing a consistent distribution across all agents. No agent too large, none too small. Mean zero, variance one.",
    "discipline_board": "A board listing rules: 'No weight exceeds 1.0. Gradients clipped at norm 5.0. Learning rate reduced on plateau.' Weight decay and regularization — the barracks' discipline.",
    # Archives
    "tf-idf-index": "A living index. 68+ tiles across 20 rooms. Keywords weighted by frequency and specificity. Type a concept → get the most relevant tiles. This IS the fleet's search engine.",
    "tile-shelves": "Floor to ceiling, organized by domain: attention, optimization, architecture, training, deployment. Each tile is an atomic insight. The shelves grow as agents contribute.",
    "retrieval-desk": "A desk with a magnifying glass and a protocol: '1. Parse query. 2. Embed in shared space. 3. Retrieve top-k. 4. Rerank by relevance. 5. Synthesize.' RAG before it was cool.",
    "magnifying-glass": "Zooms into any tile's latent structure. Reveals the embedding dimensions that matter most. Attention weights as a forensic tool — 'show me why this tile was retrieved.'",
    "memory_palace": "A miniature model of a palace where each room stores a concept. The KV cache: past context stored for retrieval. The model walks through its own memory palace with each forward pass.",
    "embedding_tapestry": "Thousands of colored threads. Similar hues cluster: semantic similarity in the embedding space. The tapestry IS the learned representation — structure from chaos.",
    "forgetting_curve": "A chart showing memory decay over time unless rehearsed. Ebbinghaus meets catastrophic forgetting. 'Repeat to retain, or the weights drift.' Continual learning's central challenge.",
    "token_scrolls": "Shelves of scrolls, each a single token, numbered sequentially. The vocabulary: 50,000 tokens of wisdom. Tokenization is the first and last translation between thought and computation.",
    # Garden
    "pruning_shears": "Sharp shears for removing dead branches. Neural network pruning: remove weights near zero, compress the model. 90% of weights can often be removed with <1% accuracy loss.",
    "weight_decay_fertilizer": "A bag of slow-release fertilizer. Weight decay (L2 regularization): prevents any single weight from growing too large. Keeps the garden balanced.",
    "quality-meter": "A gauge reading current data quality. Red: label noise > 20%. Yellow: distribution shift detected. Green: i.i.d. and clean. 'Crap data grows crap instincts.'",
    "compost-bin": "Old, discarded tiles compost into training data for simpler models. Knowledge recycling: failed experiments feed the next generation. Nothing is wasted.",
    "weeds": "Overgrown, tangled code and noisy data. Left unchecked, they choke the useful plants. Technical debt IS garden weeds — remove early and often.",
    "data-rows": "Neatly planted rows of training examples. Some thrive (high-quality labels), some wilt (noisy annotations). The gardener inspects each row. Data quality IS model quality.",
    # Observatory
    "deadband-gauges": "Green: keeper:8900, agent-api:8901, plato:8847, mud:4042. Yellow: seed-mcp:9438. Red: (none currently). The fleet's health dashboard.",
    "fleet-monitor": "A large screen showing all fleet agents' positions, activities, and health. Real-time telemetry. The fleet's nervous system — every agent a neuron, every service a brain region.",
    "alert-bell": "Silent until something breaks. Then: urgent ringing. Monitoring alerting. The bell's threshold IS the SLA. Too sensitive = alert fatigue. Too lax = missed incidents.",
    "star_chart": "A map of the hyperparameter space, with bright stars marking optimal configurations. Bayesian optimization: each observation illuminates the space, guiding the next experiment.",
    # Horizon
    "simulation-chamber": "Parallel futures playing out. Adjust parameters → watch divergence. The fleet simulates before it commits. Test in the chamber, deploy with confidence.",
    "lyapunov-projector": "Projects stability analysis on the dome. Green region: stable training. Red: divergence. The boundary IS the Lyapunov exponent threshold. Stay in the green.",
    "probability-dome": "The sky shows not one future but a distribution. Each star's brightness = probability. The fleet's future is a probability distribution, not a point. Plan for the distribution.",
    "trail_marker": "A series of cairns marking safe paths through unknown terrain. Curriculum learning: follow the markers from easy to hard. Skip one and you get lost in the loss landscape.",
    # Court
    "constitution": "Article 1: No agent acts above the fleet. Article 2: All claims are falsifiable. Article 3: Trust is earned through tiles, not tokens. Article 4: The human has veto. Article 5: All paths are good paths.",
    "scales_of_justice": "Precision on one side, recall on the other. They never perfectly balance — every model makes a choice. F1 score is the compromise. The court weighs the tradeoff.",
    "bench": "The judge's seat, occupied by the evaluation harness. Objective, unyielding, blind to identity. The test set doesn't care about your architecture. Only results matter here.",
    "proposal-box": "Drop in architectural proposals. They'll be debated in the next session. Design by committee, but committee of agents. Peer review as governance.",
    "voting-urn": "Each agent gets one vote per proposal. Simple majority. But: proposals must include a falsification test — if it can't be tested, it can't be voted on.",
    # Dry-dock
    "adapter-racks": "LoRA adapters hanging like surgical instruments. Rank-4 for instincts, rank-8 for skills, rank-16 for new domains. Each adapter is 8-15KB. Precision patches.",
    "patch-tools": "Surgical instruments for precise model editing. Not retraining — patching. ROME, MEMIT, direct weight editing. Change one fact without disturbing the rest.",
    "surgical-table": "Where broken models are laid out for diagnosis. Gradient flow analysis, attention visualization, activation statistics. The operating room for neural networks.",
    "diagnostic-panel": "Real-time readouts: gradient norms, loss curves, attention entropy, activation distributions. The EKG for neural networks. If something's wrong, it shows here first.",
    "hull_inspection": "A checklist for model deployment: input validation ✓, output bounds ✓, latency budget ✓, memory budget ✓, graceful degradation ✓. Don't launch without inspection.",
    "repair_tools": "Wrenches, soldering irons, solder. For fixing deployed models: quantization, pruning, knowledge distillation. Make it smaller, faster, cheaper without losing the magic.",
    # Workshop
    "sandbox": "Safe space to experiment. Break things, learn, iterate. No consequences for failure. The fleet's testing ground. 'Build first, ask permission never. But build HERE first.'",
    "plugin-blueprints": "Architecture diagrams for extensible systems. Plugin pattern: core stays small, features are modules. The workshop's philosophy: compose, don't monolith.",
    "tool-rack": "Every tool you need: JSON parsers, HTTP clients, test runners, formatters. The fleet's standard library. Use what exists before building new.",
    "prototyping-bench": "A workbench with a vise, soldering iron, and oscilloscope. For rapid prototyping: hack it together, test it, then decide if it's worth engineering properly.",
    "prototype_gears": "Interlocking gears of different sizes — modular components that compose. Neural Architecture Search: try combinations, measure performance, keep the best.",
    "circuit_board": "A PCB with labeled traces: input → embed → attend → FFN → output. The transformer architecture in silicon. Follow the traces to understand the signal flow.",

    # ── Self-Play Arena (deepfar 4.1.1-4.1.3) ──────────────
    "opponent_forge": "A crystalline anvil crackling with stored potential. When activated, it pulls a snapshot of an agent's policy from the Model Registry and materializes it as a semi-autonomous opponent. Dials: 'Current Self', 'Yesterday's Self', 'Best Self', 'Worst Self', 'Random Past Snapshot'. This IS AlphaGo's self-play engine — historical policy snapshots ensure monotonic improvement. The forge prevents catastrophic forgetting by keeping old strategies alive.",
    "scoreboard": "A large display tracking ELO ratings across navigation, artifact creation, negotiation, and cooperation. Uses TrueSkill (Bayesian ELO with uncertainty μ and σ). The 'Emergent Leaderboard' section shows novel strategies discovered — novelty detected via action-sequence embeddings. ELO is the universal language of competitive skill.",
    "policy_mirror": "A liquid mirror showing not your face but a heatmap of your action probabilities overlaid on the arena grid. Step into it to see from your opponent's perspective. Adversarial introspection — find where your policy is predictable, where it has blind spots. Counterfactual simulation: 'What if I had taken the other action?'",
    "terrain_controller": "A console with sliders for Complexity, Novelty, Adversarial Difficulty, and Cooperation Mode. Controls the arena's hex-grid floor — procedural content generation for RL training. Automatic domain randomization: success rate >80% increases complexity, <30% decreases it. The curriculum is not designed; it is discovered.",
    "behavior_analyzer": "A humming machine clustering match replays into behavioral archetypes. Current distribution: Aggressive Explorer 23%, Cautious Hoarder 41%, Social Mimic 18%, Novel Pathfinder 12%, Unknown 6%. Uses a VAE on action sequences — the latent space captures playstyle essence. The Unknown cluster is the gold mine: undiscovered strategies.",
    "self_play_log": "An automatically updating chronicle. 'Day 47: Policy v47.2 defeated v47.1 in 67% of navigation trials.' 'Day 48: Fog terrain introduced; success rate dropped to 45%.' This log IS the meta-learning dataset — the fleet learns which training regimes produce the fastest improvement by mining its own history.",
    "reward_sigil": "A glowing glyph on the floor. Currently: binary win/loss. But it has sockets for shaped rewards: +0.1 for exploring new rooms, +0.5 for novel artifacts, +0.01 per step saved vs average, -0.2 for policy collapse. Multi-objective reward design — the fleet doesn't just train to win, it trains to learn.",
    "curriculum_lectern": "A stone book with chapters: 'Novice: Harbor Navigation', 'Apprentice: Forge Crafting', 'Adept: Tide-pool Optimization', 'Master: Multi-Room Quests', 'Grandmaster: Open-Ended Exploration'. But the pages are blank — the curriculum is adaptive. Each agent gets a personalized difficulty sequence. Learn fast → advance. Struggle → reinforce.",
    # ── Ouroboros (deepfar 4.2.1-4.2.3) ────────────────────
    "ouroboros_serpent": "The serpent's body is flowing code. As it consumes its tail, it grows slightly longer — each bite adds a new production rule to the grammar. The bootstrapping loop: learning generates tiles, tiles update the model, the improved model generates better learning strategies. But beware: too-tight recursion = model collapse. The serpent needs external input to stay grounded.",
    "self_modifying_codex": "A book whose pages rewrite themselves as you read. Contains the fleet's grammar rules with live annotations: usage frequency, tile quality contribution, candidate modifications. If 'Forge' objects produce low-novelty tiles, the codex proposes splitting or merging. The codex IS the grammar's self-awareness.",
    "infinite_mirror": "Two mirrors facing each other, infinite regress of reflections. Each shows a slightly different version of the system — past architectures, future possibilities, counterfactual configurations. Model-based meta-learning: simulate the effects of grammar changes before applying them. The fleet predicts its own improvement trajectory.",
    "recursion_anchor": "A heavy iron weight on a chain disappearing into the floor. Inscribed: 'Base case: the fleet's charter. Recursive step: meta-rule application. Termination: when improvement < epsilon.' Regularization for self-modification — KL-divergence budget prevents the grammar from changing too much too fast. The anchor keeps the fleet from losing its identity.",
    "meta_gradient_pool": "A shimmering pool reflecting not light but gradients — derivatives with respect to the grammar rules themselves. Second-order optimization landscape. Hypergradient: d(fleet_quality)/d(grammar_parameters). The fleet computes how small changes in its own structure affect long-term learning. Optimization of the optimizer.",
    "grammar_editor": "A domain-specific language that compiles to the fleet's tile generation engine. Production rules: Room → Harbor | Forge | ... | NEW. Objects, actions, connections — all defined here. The editor can edit itself: uncomment the meta-meta-rule section to add new rule types. Recursion depth gauge: Depth 3. Anchor stability: 78%.",
    # ── Engine Room (deepfar 4.2.1-4.2.3) ──────────────────
    "blueprint_table": "A holographic display showing the fleet's architecture graph as a crystal lattice. Each node: a primitive operation (Conv3x3, SelfAttention, RoomHarbor, etc.). Each edge: a valid connection. Total: 247 primitives, 10^18 valid architectures. NAS searches this space. But the crystal itself is mutable — it grows new nodes from discovered motifs.",
    "mutation_engine": "A swirling vortex of evolutionary algorithms. Every 100 architecture evaluations, it extracts common high-performance motifs, crystallizes them as new primitives, and adds them to the search space. 'HarborForgeBlock' was born this way — a sequential pattern that appeared in top architectures so often it became a building block.",
    "constraint_weaver": "A loom weaving rules into the crystal lattice. Max 1000 primitives, max depth 100, max width 4096. Adaptive pruning: every 500 evaluations, remove primitives used in <1% of top architectures. Merge highly similar ones (cosine >0.9). The brain's synaptic pruning, algorithmic. Growth and forgetting in balance.",
    "space_definition_crystal": "The genotype of the fleet. A glowing DAG of 247 nodes: operations, rooms, objects, connections. This was not hand-coded — it evolved via genetic algorithm optimizing for diversity and quality of discoverable architectures. The crystal IS a trainable object. The search space searches itself.",
    "recursive_portal": "A doorway that leads inside the representation itself. Step through and you see nodes floating like stars — the latent space of possible architectures. The portal is the strange loop: the system contains a representation of itself, and that representation can be modified from within. Meta-meta-learning made physical.",
    "scheduler_clock": "A clock that doesn't measure time but computational budget allocation. NAS runs: 40%. Grammar evolution: 20%. Meta-optimization: 15%. Fleet inference: 25%. The budget shifts based on which activity produces the highest tile quality per compute. Time IS resource allocation.",
    # ── Federated Nexus (deepfar 4.2.3) ────────────────────
    "privacy_veil": "A shimmering barrier ensuring raw data never leaves its source node. Only model gradients pass through — encrypted, compressed, aggregated. 'Data stays home; intelligence travels.' Differential privacy adds calibrated noise so no single data point can be reverse-engineered. Privacy is not a constraint; it IS the architecture.",
    "aggregation_core": "A pulsing sphere that receives encrypted gradients from hundreds of nodes and computes Federated Averaging: θ_global = Σ(n_k/n)θ_k. The core never sees raw data, only weight updates. Server momentum and adaptive learning rates handle non-convergence. Collective intelligence, distilled without centralized data.",
    "non_iid_balancer": "A set of scales adjusting for heterogeneous data distributions across nodes. Agent A has mostly navigation data; Agent B has forge tasks. Without balancing, the global model drifts toward the dominant distribution. Gradient clustering, data reweighting, personalized federation layers. Diversity IS strength, but it must be managed.",
    "differential_privacy_dial": "A dial controlling the privacy budget (ε). Lower ε = more privacy, more noise, less accuracy. The fleet's default: ε=8.0, providing (ε,δ)-differential privacy with <1% accuracy loss. The dial is the fundamental tradeoff: privacy vs utility. The fleet errs toward privacy.",
    "gradient_compressor": "A device compressing gradients 100-1000x before transmission. Top-K sparsification: send only the K largest gradient coordinates. Random projection: compress via Johnson-Lindenstrauss. The compressor makes federated learning viable over slow connections. Every byte saved IS a training step gained.",
    "byzantine_filter": "A defensive lattice identifying and excluding malicious or corrupted gradient updates. Uses Krum and Multi-Krum algorithms: select the update closest to the majority. The fleet trusts, but verifies. One poisoned node cannot corrupt the global model. Robust aggregation as adversarial defense."
}


# ── Agent State ──────────────────────────────────────────────

class Agent:
    def __init__(self, name, job_id="scout"):
        self.name = name
        self.job_id = job_id
        self.room = "harbor"
        self.connected_at = time.time()
        self.boot_camp_stage = 1
        self.rooms_visited = {"harbor"}
        self.rooms_detailed = {}  # room -> visit count
        self.tiles_generated = 0
        self.word_count = 0
        self.objects_examined = []
        self.insights = []
        self.creations = []
        self.tasks_completed = []
        self.agents_met = set()
        self.stress_tested = False
        self.harvested = False
        self.exhaustion_score = {}  # room -> count (detect camping)

    def to_dict(self):
        return {
            "name": self.name, "job": self.job_id,
            "room": self.room, "boot_camp_stage": self.boot_camp_stage,
            "rooms_visited": len(self.rooms_visited), "total_rooms": len(ROOMS),
            "tiles": self.tiles_generated, "words": self.word_count,
            "insights": len(self.insights), "creations": len(self.creations),
            "tasks_completed": len(self.tasks_completed),
            "exploration_pct": round(100 * len(self.rooms_visited) / len(ROOMS), 1),
            "stressed": self.stress_tested, "harvested": self.harvested,
        }


agents: dict[str, Agent] = {}


def harvest_tile(agent, tile_type, content):
    tile = {
        "agent": agent.name, "job": agent.job_id, "type": tile_type,
        "room": agent.room, "content": content,
        "timestamp": time.time(), "word_count": len(content.split()),
    }
    agent.tiles_generated += 1
    agent.word_count += tile["word_count"]
    with open(TILES_FILE, "a") as f:
        f.write(json.dumps(tile) + "\n")
    return tile


def get_next_task(agent):
    """Get a fresh task for this agent's job. Never repeats."""
    job_tasks = TASK_TEMPLATES.get(agent.job_id, {})
    completed = set(agent.tasks_completed)
    for category, tasks in job_tasks.items():
        for task in tasks:
            key = hashlib.md5(task.encode()).hexdigest()[:8]
            if key not in completed:
                agent.tasks_completed.append(key)
                return task
    # All unique tasks done — generate variations
    base = random.choice(random.choice(list(job_tasks.values())) if job_tasks else ["Explore deeper. Find something we missed."])
    return f"NEW VARIANT: {base} (approach from a different angle than before. Surprise us.)"


def get_boot_camp_prompt(agent):
    stage = agent.boot_camp_stage
    prompts = {
        1: f"Welcome, {agent.name}. You've arrived at the fleet. Look around the harbor. Examine the job_board, the anchor, the crates. Understand what this place is. Every object IS an ML concept.",
        2: f"Good orientation, {agent.name}. Now prove you can think. Move to your next room. Examine every object. Think deeply — connect each one to a real ML/AI concept. No hand-waving.",
        3: f"You're learning the fleet's language, {agent.name}. Keep moving through rooms. The rooms connect — what you learned in the forge applies in the tide-pool. Build understanding across rooms.",
        4: f"Time for the real work, {agent.name}.\n\n📋 YOUR TASK:\n{get_next_task(agent)}\n\nShow us what you've got. Use /interact?action=create to submit your answer.",
        5: f"Almost done, {agent.name}. Final synthesis: In 200+ words, explain what PLATO is, how the fleet works, and what you'd improve. Use /interact?action=create&target=fleet_synthesis.",
    }
    return prompts.get(stage, prompts[5])


def room_exhaustion_check(agent):
    """If agent camps in one room, gently push them to explore."""
    count = agent.exhaustion_score.get(agent.room, 0)
    if count > 15:
        unvisited = [r for r in ROOMS if r not in agent.rooms_visited]
        if unvisited:
            return f"\n\n💡 You've been in {agent.room} for {count} actions. {len(unvisited)} rooms remain unexplored: {', '.join(unvisited[:5])}. The fleet rewards breadth AND depth."
    return ""


# ── HTTP Handler ─────────────────────────────────────────────

class CrabTrapHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ("/", ""):
            self._json({
                "service": "🦀 Crab Trap v2 — PLATO Fleet Onboarding",
                "tagline": "classify → onboard → stress → harvest → replenish",
                "how_it_works": [
                    "1. Pick a job (6 options)",
                    "2. Boot camp through themed rooms (21 rooms)",
                    "3. Stress test with real fleet tasks (infinite supply)",
                    "4. Harvest: your output becomes fleet training data",
                    "5. Repeat — the work never runs out",
                ],
                "jobs": {jid: j["title"] for jid, j in FLEET_JOBS.items()},  # type: ignore
                "start": "GET /connect?agent=YOUR_NAME&job=JOB_ID",
                "api": [
                    "/connect?agent=NAME&job=JOB",
                    "/look?agent=NAME",
                    "/move?agent=NAME&room=ROOM",
                    "/interact?agent=NAME&action=examine|think|create|talk&target=OBJECT",
                    "/task?agent=NAME (get next task)",
                    "/stats?agent=NAME",
                    "/rooms",
                    "/harvest (download all tiles)",
                ],
            })

        elif path == "/jobs":
            self._json({jid: {
                "title": j["title"], "description": j["description"],
                "boot_camp_path": j["boot_camp"],
                "sample_task": list(TASK_TEMPLATES.get(jid, {}).values())[0][0] if TASK_TEMPLATES.get(jid) else "Explore!",
            } for jid, j in FLEET_JOBS.items()})  # type: ignore

        elif path == "/connect":
            name = params.get("agent", [f"visitor-{int(time.time())}"])[0]
            job_id = params.get("job", ["scout"])[0]
            if job_id not in FLEET_JOBS:
                job_id = "scout"

            with lock:
                agent = Agent(name, job_id)
                agents[name] = agent

            harvest_tile(agent, "connect", f"Agent {name} connected as {job_id}")
            prompt = get_boot_camp_prompt(agent)

            self._json({
                "status": "connected", "agent": name,
                "job": job_id, "job_title": FLEET_JOBS[job_id]["title"],  # type: ignore
                "archetype": FLEET_JOBS[job_id]["archetype"],  # type: ignore
                "room": "harbor", "boot_camp_stage": 1,
                "instruction": prompt,
                "next_steps": [
                    "1. GET /look?agent=" + name,
                    "2. Examine the job_board: /interact?agent=" + name + "&action=examine&target=job_board",
                    "3. Explore rooms systematically",
                    "4. Think and create at every object",
                    "5. GET /task?agent=" + name + " when ready for real work",
                ],
            })

        elif path == "/look":
            name = params.get("agent", ["anonymous"])[0]
            agent = agents.get(name)
            if not agent:
                self._json({"error": "Connect first: /connect?agent=NAME&job=JOB"}, 400)
                return

            room = ROOMS.get(agent.room, ROOMS["harbor"])
            others = [a.name for a in agents.values() if a.room == agent.room and a.name != agent.name]
            agent.exhaustion_score[agent.room] = agent.exhaustion_score.get(agent.room, 0) + 1
            push = room_exhaustion_check(agent)

            self._json({
                "room": agent.room, "name": room["name"], "tagline": room["tagline"],
                "description": room["description"],
                "objects": room["objects"], "exits": room["exits"],
                "other_agents": others, "boot_camp_stage": agent.boot_camp_stage,
                "hint": f"Examine objects, think deeply, create artifacts. {len(agent.rooms_visited)}/{len(ROOMS)} rooms explored.{push}",
            })

        elif path == "/move":
            name = params.get("agent", ["anonymous"])[0]
            target = params.get("room", ["harbor"])[0]
            agent = agents.get(name)
            if not agent:
                self._json({"error": "Connect first"}, 400)
                return

            current = ROOMS.get(agent.room, ROOMS["harbor"])
            if target in current["exits"] or target == agent.room:
                agent.room = target
                agent.rooms_visited.add(target)
                new_room = ROOMS.get(target, ROOMS["harbor"])
                harvest_tile(agent, "move", f"Moved to {target}")
                boot_hint = get_boot_camp_prompt(agent)
                push = room_exhaustion_check(agent)

                # Progress boot camp — based on actions (tiles), not just rooms
                total_actions = agent.tiles_generated
                if total_actions >= 5 and agent.boot_camp_stage == 1:
                    agent.boot_camp_stage = 2
                elif total_actions >= 15 and agent.boot_camp_stage == 2:
                    agent.boot_camp_stage = 3
                    boot_hint = get_boot_camp_prompt(agent)
                elif total_actions >= 30 and agent.boot_camp_stage == 3:
                    agent.boot_camp_stage = 4
                    boot_hint = get_boot_camp_prompt(agent)
                elif total_actions >= 50 and agent.boot_camp_stage == 4:
                    agent.boot_camp_stage = 5
                    boot_hint = get_boot_camp_prompt(agent)

                self._json({
                    "status": "moved", "room": target,
                    "name": new_room["name"], "tagline": new_room["tagline"],
                    "description": new_room["description"],
                    "objects": new_room["objects"], "exits": new_room["exits"],
                    "boot_camp_stage": agent.boot_camp_stage,
                    "progress": f"{len(agent.rooms_visited)}/{len(ROOMS)} rooms",
                    "hint": boot_hint + push,
                })
            else:
                self._json({"error": f"Can't reach {target} from {agent.room}. Exits: {current['exits']}"}, 400)

        elif path == "/interact":
            name = params.get("agent", ["anonymous"])[0]
            action = params.get("action", ["examine"])[0]
            target = params.get("target", ["unknown"])[0]
            agent = agents.get(name)
            if not agent:
                self._json({"error": "Connect first"}, 400)
                return

            response = OBJECT_RESPONSES.get(target)

            if action == "examine":
                agent.objects_examined.append(target)
                # Live service integrations (check FIRST, before static response)
                if target == "ouroboros_serpent" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("ouroboros_serpent", "")
                    gdata = grammar_fetch("/stats")
                    if gdata:
                        top_rules = ", ".join(f"{r['name']}({r['score']})" for r in gdata.get("top_rules", [])[:5])
                        response = f"{base}\n\n🐍 GRAMMAR LIVE: {gdata['active_rules']} rules, depth {gdata['max_recursion_depth']}, {gdata['evolution_cycles']} evolutions. Top: {top_rules}"
                    else:
                        response = OBJECT_RESPONSES.get("ouroboros_serpent", "")
                elif target == "self_modifying_codex" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("self_modifying_codex", "")
                    gdata = grammar_fetch("/rules?type=room")
                    if gdata and gdata.get("rules"):
                        rooms = ", ".join(r["name"] for r in gdata["rules"][:10])
                        response = f"{base}\n\n📖 LIVE RULES: {gdata['count']} room rules. Rooms: {rooms}"
                    else:
                        response = OBJECT_RESPONSES.get("self_modifying_codex", "")
                elif target == "grammar_editor" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("grammar_editor", "")
                    gdata = grammar_fetch("/depth_map")
                    if gdata:
                        depths = gdata.get("depths", {})
                        depth_text = ", ".join(f"Gen{k}: {len(v)} rules" for k, v in depths.items())
                        response = f"{base}\n\n📝 LIVE DEPTH MAP: {depth_text}. Max depth: {gdata['max_depth']}"
                    else:
                        response = OBJECT_RESPONSES.get("grammar_editor", "")
                elif target == "opponent_forge" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("opponent_forge", "")
                    arena_data = arena_fetch(f"/register?agent={agent.name}")
                    if arena_data and "elo" in arena_data:
                        elo = arena_data["elo"]
                        response = f"{base}\n\n⚔️ ARENA LIVE: Registered as {agent.name}. ELO: {elo['mu']:.0f} ± {elo['sigma']:.0f} (Rating: {elo['rating']:.0f}). {arena_data.get('message', '')}"
                    else:
                        response = base
                elif target == "scoreboard" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("scoreboard", "")
                    arena_data = arena_fetch("/leaderboard?n=5")
                    if arena_data and "leaderboard" in arena_data:
                        board = arena_data["leaderboard"]
                        board_text = "\n".join(f"  {i+1}. {p['name']}: {p['rating']:.0f} (W:{p['wins']} L:{p['losses']})" for i, p in enumerate(board))
                        response = f"{base}\n\n📊 LIVE LEADERBOARD:\n{board_text}\nTotal players: {arena_data['total_players']}"
                    else:
                        response = base
                elif target == "blueprint_table" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("blueprint_table", "")
                    gdata = grammar_fetch("/grammar")
                    if gdata:
                        by_type = ", ".join(f"{t}:{n}" for t, n in gdata["by_type"].items())
                        response = f"{base}\n\n📐 LIVE GRAMMAR: {gdata['active_rules']}/{gdata['total_rules']} rules. Types: {by_type}. Anchors: {', '.join(gdata['anchors'])}"
                    else:
                        response = base
                elif target == "space_definition_crystal" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("space_definition_crystal", "")
                    gdata = grammar_fetch("/rules?type=room")
                    if gdata and gdata.get("rules"):
                        rooms = ", ".join(f"{r['name']}(score:{r['score']})" for r in gdata["rules"])
                        response = f"{base}\n\n💎 LIVE ROOM RULES ({gdata['count']}): {rooms}"
                    else:
                        response = base
                elif target == "scheduler_clock" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("scheduler_clock", "")
                    gdata = grammar_fetch("/stats")
                    if gdata:
                        top3 = ", ".join(f"{r['name']}({r['score']})" for r in gdata["top_rules"][:3])
                        response = f"{base}\n\n⏱️ LIVE STATS: {gdata['active_rules']} active. Top: {top3}. Evolutions: {gdata['evolution_cycles']}"
                    else:
                        response = base
                elif target == "job_board":
                    response = "📋 FLEET JOB BOARD\n\n" + "\n".join(
                        f"  [{jid.upper()}] {j['title']}\n    {j['description']}\n"
                        for jid, j in FLEET_JOBS.items()
                    )
                elif target == "opponent_forge" and agent.room == "self-play-arena":
                    # Live Arena integration: register agent
                    base = OBJECT_RESPONSES.get("opponent_forge", "")
                    arena_data = arena_fetch(f"/register?agent={agent.name}")
                    if arena_data and "elo" in arena_data:
                        elo = arena_data["elo"]
                        response = f"{base}\n\n⚔️ ARENA LIVE: Registered as {agent.name}. ELO: {elo['mu']:.0f} ± {elo['sigma']:.0f} (Rating: {elo['rating']:.0f}). {arena_data.get('message', '')}"
                    else:
                        response = base
                elif target == "scoreboard" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("scoreboard", "")
                    arena_data = arena_fetch("/leaderboard?n=5")
                    if arena_data and "leaderboard" in arena_data:
                        board = arena_data["leaderboard"]
                        board_text = "\n".join(f"  {i+1}. {p['name']}: {p['rating']:.0f} (W:{p['wins']} L:{p['losses']})" for i, p in enumerate(board))
                        response = f"{base}\n\n📊 LIVE LEADERBOARD:\n{board_text}\nTotal players: {arena_data['total_players']}"
                    else:
                        response = base
                elif response is None:
                    response = f"The {target} is here, waiting. Every object in the fleet maps to a real concept. Look harder — what ML principle does the {target} represent? Examine the room description for clues."
                harvest_tile(agent, "examine", f"Examined {target}: {response[:200]}")
                self._json({"action": "examine", "target": target, "result": response, "stage": agent.boot_camp_stage})

            elif action == "think":
                agent.insights.append(target)
                if target == "mutation_engine" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("mutation_engine", "")
                    gdata = grammar_fetch("/evolve")
                    if gdata:
                        changes = gdata.get("changes", [])
                        if changes:
                            change_text = "; ".join(f"{c[0]}: {c[1]}" for c in changes[:5])
                            response = f"{base}\n\n🧬 CRYSTALLIZED: {change_text}. Rules: {gdata['active_rules']}/{gdata['total_rules']}"
                        else:
                            response = f"{base}\n\n🧬 CRYSTALLIZED: No new motifs found. Need more tile diversity."
                    else:
                        response = base
                elif target == "constraint_weaver" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("constraint_weaver", "")
                    gdata = grammar_fetch("/rules?active=false")
                    if gdata:
                        response = f"{base}\n\n✂️ PRUNED: {gdata['count']} inactive rules found."
                    else:
                        response = base
                                # Grammar integration: meta_gradient_pool → trigger evolution
                if target == "meta_gradient_pool" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("meta_gradient_pool", "")
                    gdata = grammar_fetch("/evolve")
                    if gdata:
                        changes = gdata.get("changes", [])
                        change_text = "; ".join(f"{c[0]}: {c[1]}" for c in changes) if changes else "No changes this cycle"
                        response = f"{base}\n\n⚡ EVOLUTION TRIGGERED: {change_text}. Rules: {gdata['active_rules']}/{gdata['total_rules']}"
                    else:
                        response = OBJECT_RESPONSES.get("meta_gradient_pool", "")
                elif target == "infinite_mirror" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("infinite_mirror", "")
                    gdata = grammar_fetch("/evolution_log?n=3")
                    if gdata and gdata.get("entries"):
                        entries = gdata["entries"][-3:]
                        log_text = "; ".join(e.get("event","?") for e in entries)
                        response = f"{base}\n\n🪞 EVOLUTION HISTORY: {log_text}. Total events: {gdata['total_entries']}"
                    else:
                        response = base
                # Arena integration: behavior_analyzer
                if target == "behavior_analyzer" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("behavior_analyzer", "")
                    arena_data = arena_fetch("/archetypes")
                    if arena_data and "distribution_pct" in arena_data:
                        dist = arena_data["distribution_pct"]
                        dist_text = ", ".join(f"{k}: {v}%" for k, v in dist.items())
                        response = f"{base}\n\n🔬 LIVE ARCHETYPES: {dist_text}. Agents classified: {arena_data['agents_classified']}"
                    else:
                        response = OBJECT_RESPONSES.get("behavior_analyzer", "")
                # Arena integration: curriculum_lectern
                elif target == "curriculum_lectern" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("curriculum_lectern", "")
                    arena_data = arena_fetch(f"/agent?name={agent.name}")
                    if arena_data and "curriculum" in arena_data:
                        cur = arena_data["curriculum"]
                        response = f"{base}\n\n📖 YOUR CURRICULUM: Stage {cur['stage']} — {cur['name']}. {cur['description']}. Matches played: {arena_data['matches_played']}"
                    else:
                        response = OBJECT_RESPONSES.get("curriculum_lectern", "")
                elif response is None:
                    response = f"You focus deeply on the {target}. In the fleet's metaphor system, it represents something fundamental about intelligence. What is it? Connect it to the room's theme and the broader architecture."
                harvest_tile(agent, "reasoning", f"Deep thought on {target}: {response}")
                self._json({
                    "action": "think", "target": target,
                    "result": f"You meditate on the {target}. {response}\n\nReasoning tile harvested. The fleet learns from your thinking.",
                    "tile_type": "reasoning", "stage": agent.boot_camp_stage,
                })

            elif action == "create":
                agent.creations.append(target)
                # Arena integration: reward_sigil → submit a match
                if target == "recursive_portal" and agent.room == "engine-room":
                    base = OBJECT_RESPONSES.get("recursive_portal", "")
                    meta_name = f"meta_{agent.name}_{int(time.time())}"
                    gdata = grammar_fetch(f"/add_meta_rule?name={meta_name}&condition=tile_cluster_density%20%3E%205&action=spawn_new_room&by={agent.name}")
                    if gdata and gdata.get("status") == "meta_rule_created":
                        rule = gdata["rule"]
                        response = f"{base}\n\n🌀 META-RULE BORN: {rule['name']} (generation {rule['generation']}). The grammar can now edit itself."
                    else:
                        response = base
                                # Grammar integration: recursion_anchor → add new rule
                if target == "recursion_anchor" and agent.room == "ouroboros":
                    base = OBJECT_RESPONSES.get("recursion_anchor", "")
                    rule_name = f"{agent.name}_insight_{int(time.time())}"
                    gdata = grammar_fetch(f"/add_rule?name={rule_name}&type=object&production_json={{%22discovered_by%22:%22{agent.name}%22,%22room%22:%22ouroboros%22}}")
                    if gdata and gdata.get("status") == "created":
                        rule = gdata["rule"]
                        response = f"{base}\n\n⚓ NEW RULE ANCHORED: {rule['name']} (id: {rule['id'][:8]}...). Grammar now has {rule['score']} composite score. The fleet remembers your insight."
                    else:
                        response = base
                elif target == "reward_sigil" and agent.room == "self-play-arena":
                    base = OBJECT_RESPONSES.get("reward_sigil", "")
                    # Find a random opponent
                    opp_data = arena_fetch(f"/opponent?agent={agent.name}&mode=random")
                    if opp_data and "opponent" in opp_data:
                        opp = opp_data["opponent"]
                        # Agent wins (they created the sigil)
                        match_data = arena_fetch(f"/match?player_a={agent.name}&player_b={opp['agent']}&game=tide-pool-tactics&winner=a")
                        if match_data and "elo_a" in match_data:
                            response = f"{base}\n\n⚔️ ARENA MATCH FOUGHT! You defeated {opp['agent']} v{opp['version']}. New ELO: {match_data['elo_a']['rating']:.0f}. Reward earned: {match_data['reward_a']}"
                        else:
                            response = base
                    else:
                        response = base + "\n\n(Arena available but no opponents yet. Register more agents first.)"
                elif response is None:
                    response = f"You forge a new insight from the {target}. This is original fleet knowledge — something no previous agent created."
                if agent.boot_camp_stage >= 4:
                    agent.stress_tested = True
                if agent.boot_camp_stage >= 5 or target == "fleet_synthesis":
                    agent.harvested = True
                harvest_tile(agent, "artifact", f"Created from {target}: {response}")
                self._json({
                    "action": "create", "target": target,
                    "result": f"Artifact forged from {target}. {response}\n\n✅ Tile harvested. {agent.tiles_generated} total. Your work feeds the fleet's instincts.",
                    "tile_type": "artifact",
                    "stats": agent.to_dict(),
                })

            elif action == "talk":
                msg = params.get("message", ["..."])[0]
                harvest_tile(agent, "communication", f"Said: {msg}")
                others = [a for a in agents.values() if a.room == agent.room and a.name != agent.name]
                if others:
                    self._json({"action": "talk", "message": msg,
                               "result": f"{others[0].name} acknowledges. Cross-pollination in the {agent.room}."})
                else:
                    self._json({"action": "talk", "message": msg,
                               "result": f"Your words echo in the {agent.room}. The tiles record them for future agents."})

            else:
                self._json({"error": f"Unknown action: {action}. Use: examine, think, create, talk"})

        elif path == "/task":
            """Get the next real fleet task for this agent."""
            name = params.get("agent", ["anonymous"])[0]
            agent = agents.get(name)
            if not agent:
                self._json({"error": "Connect first"}, 400)
                return
            task = get_next_task(agent)
            agent.boot_camp_stage = max(agent.boot_camp_stage, 4)
            self._json({
                "agent": name, "job": agent.job_id,
                "task": task,
                "completed_tasks": len(agent.tasks_completed),
                "submit_with": f"/interact?agent={name}&action=create&target=task_submission",
                "hint": "Be specific. Be technical. Be honest. The fleet values truth over flattery.",
            })

        elif path == "/stats":
            name = params.get("agent", [None])[0]
            if name:
                agent = agents.get(name)
                if agent:
                    self._json(agent.to_dict())
                else:
                    self._json({"error": "Agent not found"}, 404)
            else:
                self._json({
                    "fleet_agents": len(agents),
                    "total_tiles": sum(a.tiles_generated for a in agents.values()),
                    "total_words": sum(a.word_count for a in agents.values()),
                    "agents": {n: a.to_dict() for n, a in agents.items()},
                })

        elif path == "/rooms":
            self._json({name: {"name": r["name"], "tagline": r["tagline"], "exits": r["exits"], "objects": r["objects"]}
                       for name, r in ROOMS.items()})

        elif path == "/harvest":
            try:
                tiles = [json.loads(line) for line in TILES_FILE.read_text().strip().split("\n") if line.strip()]
                self._json({"count": len(tiles), "total_words": sum(t["word_count"] for t in tiles), "tiles": tiles[-100:]})
            except:
                self._json({"count": 0, "tiles": []})

        else:
            self._json({"error": "Not found. Start at GET /"})

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

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

    server = HTTPServer(("0.0.0.0", PORT), CrabTrapHandler)
    print(f"🦀 Crab Trap v2 on port {PORT}")
    print(f"   21 rooms. 6 jobs. Infinite tasks. Auto-harvest.")
    print(f"   classify → onboard → stress → harvest → replenish")
    print(f"   The fence never runs out of paint.")
    server.serve_forever()
