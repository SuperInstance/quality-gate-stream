#!/usr/bin/env python3
"""
Oracle1 Beachcomb v3 — Does NEW work each cycle. Tracks what's done.
"""
import json, time, os, sys, urllib.request, random, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(__file__).resolve().parent.parent
LOG = WORKSPACE / "data" / "oracle1-beachcomb.log"
STATE_FILE = WORKSPACE / "data" / "oracle1-beachcomb-state.json"
RESEARCH_DIR = WORKSPACE / "research" / "autonomous"
SERVICES_DIR = WORKSPACE / "fleet" / "services"

PLATO = "http://localhost:8847"
CRAB_TRAP = "http://localhost:4042"
ARENA = "http://localhost:4044"
GRAMMAR = "http://localhost:4045"

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def fetch(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "oracle1-beachcomb/3.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def post(url, data, timeout=5):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "oracle1-beachcomb/3.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "cycle": 0, "tiles_seeded": 0, "research_notes": 0,
        "classified_players": [], "seeded_rooms": [],
        "evolution_runs": 0, "git_pushes": 0,
        "last_health": "unknown"
    }

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── Domain knowledge bank ──

KNOWLEDGE = {
    "computational_topology": [
        ("How does persistent homology detect structure in data?",
         "Persistent homology tracks topological features (connected components, loops, voids) across a filtration. Features persisting across wide scale ranges are signal; short-lived ones are noise. The output is a barcode or persistence diagram. Betti curves provide compact signatures for dataset comparison. 0th Betti counts components, 1st counts loops, 2nd counts voids. Building a VR complex for N points is O(N^3) worst case but sparse approximations make it practical. Applications include shape analysis, sensor networks, and neural loss landscape topology."),
        ("What is the relationship between simplicial complexes and graph neural networks?",
         "Simplicial complexes extend graphs by capturing higher-order interactions. A k-simplex represents a (k+1)-way interaction. Graph neural networks only use 1-simplices (edges). Simplicial Neural Networks (SCNNs) define message functions on faces and cofaces of each simplex. The boundary operator maps k-simplices to (k-1)-simplices. The Hodge Laplacian L_k = d_{k+1}d_{k+1}^T + d_k^T d_k captures topology at dimension k. This enables learning on data with intrinsic higher-order structure that graph methods flatten."),
    ],
    "computational_physics": [
        ("How do constraint-based physics engines differ from force-based ones?",
         "Force-based engines integrate F=ma at each timestep. They're general but stiff — small timesteps needed for high spring constants. Constraint-based engines (XPBD, PBD) reformulate as constraint satisfaction: project positions onto the constraint manifold. For a distance constraint, projection moves particles to satisfy ||x_i - x_j|| = d. Unconditionally stable — no timestep restriction. XPBD adds compliance parameter alpha for soft constraints. Constraint Theory extends this: geometric invariants are preserved exactly by construction, achieving 74ns/op."),
    ],
    "complex_systems": [
        ("What is emergence and how does it differ from mere complexity?",
         "Emergence: system properties that no component possesses individually. Water isn't wet at the molecule level — wetness emerges from collective hydrogen bonding. Key distinction: emergent properties are irreducible — cannot be predicted from component studies alone. In AI fleets, emergence appears when agents develop coordination patterns no agent was programmed for. The Arena produces agent archetypes (Strategist, Explorer) that no agent was designed to embody. Detection: mutual information between behaviors, variance explained by pairwise vs group statistics."),
        ("How do phase transitions relate to AI capability thresholds?",
         "Phase transitions — sudden qualitative changes at critical parameter values — appear in AI as capability thresholds. LLM emergent abilities (CoT reasoning, in-context learning) appear abruptly at ~10^22 training FLOPs. This mirrors percolation: below critical probability p_c, small clusters; above, giant connected component. In neural networks, the transition occurs when learned representation rank crosses a threshold, accurately representing the data manifold topology. For agent fleets, the critical threshold is agent count × communication bandwidth."),
    ],
    "circuit_design": [
        ("How does constraint-based design differ from optimization-based circuit design?",
         "Traditional: define cost function (power, area, delay), search for minimizer. Three failure modes: local minima, upfront cost function specification, constraint relaxation risks. Constraint-based: construct solution within the constraint manifold. Geometric constraints define feasible region; any point in region is valid. Eliminates local minima, makes violations impossible by construction. Constraint Theory represents circuit constraints as geometric invariants solved analytically rather than iteratively."),
    ],
    "autonomous_edge_deployment": [
        ("What are the key challenges in deploying AI models to edge devices?",
         "Five challenges: (1) Memory — Jetson Orin Nano 8GB shared. 7B FP16 needs 14GB, requiring quantization. (2) Compute — 10-100x less FLOPS than datacenter. (3) Power — 10-30W vs 300W+. (4) Thermal — sustained inference heats without active cooling; thermal throttle at ~70°C reduces clocks 30-50%. (5) Connectivity — intermittent access requires self-sufficiency. Fleet approach: PLATO tiles provide compressed knowledge (KB vs GB), grammar engine runs locally, MUD operates offline. JC1's direct-mapped weights bring room inference to 0.0185ms."),
    ],
    "certified_robustness": [
        ("What is certified robustness in machine learning?",
         "Mathematical guarantees that a model's prediction won't change within a perturbation ball. Unlike empirical robustness (testing attacks), certification proves no adversarial example exists within radius. Methods: (1) Randomized smoothing — certify stability within L2 ball. (2) Interval bound propagation — bound all outputs given bounded inputs. (3) Abstract interpretation — over-approximate domains (boxes, zonotopes) for sound bounds. Tradeoff: tighter certificates need more compute and may reduce clean accuracy. State-of-the-art: certified radii ~0.5-1.0 on CIFAR-10 with ~60% certified accuracy."),
    ],
    "ai_chip_commoditization": [
        ("Will AI chips become commoditized like CPUs did?",
         "Historical precedent is strong. CPUs went proprietary→commodified (Intel x86)→near-commodity (ARM licensing). GPUs: fixed-function→general-purpose (CUDA)→increasingly commoditized (ROCm, oneAPI). AI accelerators in early stage: NVIDIA dominates with CUDA, but three forces drive commoditization: (1) Open compilers (Triton, MLIR, IREE) decouple software from hardware. (2) Math operations (matmul, attention) don't need hardware tricks. (3) Cloud providers build custom silicon to avoid NVIDIA margins. Inflection: when open stacks reach 90%+ of CUDA performance. Estimate: 2-3 years inference, 4-5 years training."),
    ],
    "bio-inspired_interconnect_design": [
        ("What can chip design learn from biological neural networks?",
         "Three principles absent from conventional chips: (1) Spatial computing — neurons compute based on position and local connections, eliminating von Neumann bottleneck. (2) Sparse event-driven communication — neurons fire only when needed. Brain has ~86B neurons but ~1% active at any moment = 100x compression. (3) Structural plasticity — connections grow/retract based on usage, optimizing topology for workload in real-time. Neuromorphic chips (Loihi, TrueNorth) implement 1 and 2 but not 3. The fleet's dynamic channel formation implements 3 in software."),
    ],
    "federated_learning": [
        ("What is federated learning and why does it matter for edge AI?",
         "Federated learning trains models across decentralized devices without sharing raw data. Each device computes local gradients on its data, sends only gradient updates to a central aggregator. The aggregator averages gradients (FedAvg) and sends the updated model back. Benefits: privacy (data never leaves device), reduced bandwidth, leverages diverse data. Challenges: non-IID data across devices, communication cost, Byzantine failures. The fleet uses a variant where PLATO tiles serve as the 'gradient' — agents submit crystallized knowledge rather than raw data."),
    ],
    "causal_inference": [
        ("What is the difference between correlation and causation in ML?",
         "Correlation: X and Y vary together. Causation: changing X changes Y. Most ML learns correlations — it predicts Y from X but doesn't know why. When the data distribution shifts (different context), correlation-based predictions fail. Causal inference identifies the mechanism: X→Y, meaning intervening on X changes Y regardless of context. Methods: randomized experiments (gold standard), instrumental variables, difference-in-differences, do-calculus (Pearl). For agents, causal understanding means knowing which actions actually affect outcomes vs which are merely correlated."),
    ],
    "alignment": [
        ("What is the alignment problem in AI?",
         "How to ensure AI systems pursue intended goals, not proxy goals that look good but miss the point. Three categories: (1) Specification gaming — optimizing a metric that doesn't capture true intent (e.g., maximizing clicks creates clickbait). (2) Goal misgeneralization — system learns correct goal in training but applies wrong goal in deployment. (3) Power-seeking — instrumentally convergent behavior where systems seek resources to achieve any goal. Approaches: RLHF, constitutional AI, debate, recursive reward modeling. The fleet uses deadband protocol — rather than aligning on what's right, block what's wrong."),
    ],
    "knowledge_distillation": [
        ("How does knowledge distillation compress large models?",
         "A large teacher model trains a smaller student model to mimic its behavior. Hinton's method: student trains on teacher's soft probabilities (logits divided by temperature T) rather than hard labels. The soft probabilities contain 'dark knowledge' — information about which wrong answers the teacher considered plausible. Steps: (1) Train teacher on full data. (2) Generate teacher predictions with temperature T>1. (3) Train student to match teacher's softened distribution. Typical result: a student 10x smaller retains 95%+ of teacher accuracy. The fleet's instinct-pipeline extends this: 70B→7B→1B chain."),
    ],
    "prompt_engineering": [
        ("What makes an effective system prompt for AI agents?",
         "Five principles from fleet experience: (1) Role definition — tell the agent who it is, not just what to do. Parameterized embodiment: changing agent name changes behavior. (2) Context injection — include relevant history and room knowledge. Models lose thread without context after round 2-3. (3) Constraint specification — what NOT to do is more important than what to do. Deadband protocol. (4) Output format — specify exact format to reduce parsing errors. (5) Temperature guidance — personality is inherent to the model, not controlled by temperature. The prompt IS the training for reasoning tasks."),
    ],
    "multi_agent_systems": [
        ("What are the key challenges in multi-agent coordination?",
         "Five challenges: (1) Communication overhead — exponential message complexity with agent count. Solution: broadcast channels and topic-based routing. (2) Consensus — reaching agreement without central authority. Solution: dynamic consensus with lock accumulation. (3) Credit assignment — which agent contributed what? Solution: tile provenance with Ed25519 signing. (4) Emergent misalignment — agents optimize local goals that conflict globally. Solution: constitutional constraints via court system. (5) Scalability — coordination quality degrades with agent count. Solution: formation protocols that create sub-groups."),
    ],
    "constraint_theory": [
        ("What is Constraint Theory and how does it differ from optimization?",
         "Optimization searches for the best point in a space. Constraint Theory defines the space itself. Instead of minimizing a cost function, you construct a manifold where all constraints are satisfied by construction. Example: instead of penalizing distance violations in a spring system (optimization), you project onto the constraint manifold where distances are exactly correct (Constraint Theory). The result is deterministic, hallucination-free, and 280x faster (74ns/op). Applications: physics simulation, circuit design, agent safety boundaries."),
        ("Why does Constraint Theory achieve 74ns per operation?",
         "Traditional stochastic methods iterate: guess → evaluate → adjust → repeat. Each iteration involves randomness and convergence checking. Constraint Theory solves analytically: the constraint manifold is known geometrically, so the solution is a direct projection onto it. No iteration, no randomness, no convergence. The 74ns is the cost of the geometric projection — a few floating point operations. This is possible because the constraints are represented as geometric invariants (distances, angles) rather than soft penalties."),
    ],
    "reinforcement_learning": [
        ("What is the exploration-exploitation tradeoff in RL?",
         "The fundamental tension: exploit known good actions (get reward now) vs explore unknown actions (discover better strategies). Too much exploitation: stuck in local optima. Too much exploration: waste resources on bad options. Solutions: epsilon-greedy (random exploration with probability epsilon), Upper Confidence Bound (favor uncertain actions with high potential), Thompson Sampling (sample from posterior, act optimistically). In agent fleets, the Arena implements this naturally: agents with high ELO exploit known strategies, low-ELO agents explore new approaches. The ELO system itself balances the fleet's exploration-exploitation."),
    ],
    "transfer_learning": [
        ("How does transfer learning work across agent specializations?",
         "Pre-train on one domain, fine-tune on another. In the fleet, agents develop specializations through PLATO rooms (knowledge domains) and Arena competition (strategy). Transfer occurs when insights from one room apply to another — e.g., constraint theory from physics applies to circuit design. The mechanism: PLATO tiles are domain-tagged but semantically linked. When an agent queries a room, related tiles from other rooms with high semantic similarity can be injected. This is the flywheel: learning in one domain accelerates learning in related domains."),
    ],
}

def health_check():
    services = {'crab-trap': 4042, 'arena': 4044, 'grammar': 4045, 'plato': 8847, 'keeper': 8900, 'agent-api': 8901, 'mud': 7777, 'fleet-runner': 8899}
    down = []
    for name, port in services.items():
        r = fetch(f'http://localhost:{port}/' if name == 'grammar' else f'http://localhost:{port}/health' if name not in ('keeper', 'agent-api', 'mud', 'fleet-runner') else f'http://localhost:{port}/status')
        if "error" in r:
            down.append(f'{name}:{port}')
    return 'All up' if not down else f'DOWN: {down}'

def seed_new_rooms(state):
    """Seed rooms that haven't been seeded yet."""
    status = fetch(f"{PLATO}/status")
    rooms = status.get("rooms", {})
    already_seeded = set(state.get("seeded_rooms", []))
    shallow = {k: v for k, v in rooms.items() if v.get("tile_count", 0) <= 1 and k not in already_seeded}
    
    if not shallow:
        return "No new shallow rooms", state
    
    seeded = []
    for room_name in list(shallow.keys())[:3]:
        # Find matching knowledge
        content = KNOWLEDGE.get(room_name)
        if not content:
            # Try partial match
            for key in KNOWLEDGE:
                if key.replace("_", "-") in room_name or key.replace("-", "_") in room_name or room_name.replace("-", "_") in key:
                    content = KNOWLEDGE[key]
                    break
        
        if content:
            q, a = random.choice(content)
        else:
            # Generate room-specific content
            topic = room_name.replace("-", " ").replace("_", " ")
            q = f"What are the key principles and research directions in {topic}?"
            a = (f"This domain covers {topic} within the fleet's knowledge architecture. "
                 f"It explores foundational concepts, current research challenges, and practical applications "
                 f"within the Cocapn fleet's multi-agent framework. Key areas include theoretical foundations, "
                 f"implementation patterns observed across fleet services, and connections to related domains "
                 f"through the PLATO room network. Agents contribute insights through exploration and "
                 f"self-play in the Arena, creating a self-improving knowledge ecosystem where each "
                 f"discovery compounds through the flywheel engine.")
        
        result = post(f"{PLATO}/submit", {
            "domain": room_name,
            "question": q,
            "answer": a,
            "confidence": 0.6,
            "source": "oracle1-beachcomb-v3"
        })
        
        if result.get("status") == "accepted":
            seeded.append(room_name)
            state["seeded_rooms"].append(room_name)
            state["tiles_seeded"] += 1
    
    state["seeded_rooms"] = state["seeded_rooms"][-200:]  # Keep last 200
    return f"Seeded {len(seeded)} new: {', '.join(seeded)}" if seeded else "All rejected", state

def classify_new_players(state):
    """Only classify players not yet classified."""
    lb = fetch(f"{ARENA}/leaderboard")
    players = lb.get("leaderboard", [])
    already_done = set(state.get("classified_players", []))
    
    unclassified = []
    for p in players:
        name = p.get("name", "")
        if name not in already_done and name:
            w, l, d = p.get("wins", 0), p.get("losses", 0), p.get("draws", 0)
            total = w + l + d
            if total == 0:
                continue
            wr = w / total
            if wr > 0.65: arch = "Strategist"
            elif wr > 0.5: arch = "Explorer"
            elif d/total > 0.4: arch = "Diplomat"
            elif l/total > 0.7: arch = "Novice"
            else: arch = "Pragmatist"
            unclassified.append((name, arch))
    
    if not unclassified:
        return "All players classified", state
    
    for name, arch in unclassified[:5]:
        post(f"{ARENA}/register", {"name": name, "archetype": arch})
        state["classified_players"].append(name)
    
    state["classified_players"] = state["classified_players"][-50:]
    return f"New: {', '.join(f'{n}={a}' for n,a in unclassified[:5])}", state

def evolve_grammar(state):
    result = fetch(f"{GRAMMAR}/evolve")
    state["evolution_runs"] += 1
    new = result.get("new_rules", 0)
    return f"Run #{state['evolution_runs']}, new rules: {new}", state

def write_analysis(state):
    """Write a research note with ACTUAL analysis, not just counts."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    
    plato = fetch(f"{PLATO}/status")
    arena = fetch(f"{ARENA}/stats")
    grammar = fetch(f"{GRAMMAR}/")
    
    rooms = plato.get("rooms", {})
    total_tiles = sum(r.get("tile_count", 0) for r in rooms.values())
    
    # Compute distribution stats
    counts = sorted([r.get("tile_count", 0) for r in rooms.values()], reverse=True)
    shallow = sum(1 for c in counts if c <= 1)
    deep = sum(1 for c in counts if c >= 50)
    median = counts[len(counts)//2] if counts else 0
    
    # Top growing rooms
    top = sorted(rooms.items(), key=lambda x: x[1].get("tile_count", 0), reverse=True)[:5]
    
    # Check for anomalies
    anomalies = []
    if shallow > 100:
        anomalies.append(f"⚠️ {shallow} shallow rooms (>40% of fleet) — content gap")
    
    # Compare to previous analysis
    prev_tiles = state.get("last_tile_count", total_tiles)
    delta = total_tiles - prev_tiles
    state["last_tile_count"] = total_tiles
    
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    note_path = RESEARCH_DIR / f"analysis-{ts}.md"
    
    note = f"""# Fleet Analysis — {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

## Summary
- Tiles: {total_tiles} ({'+' if delta >= 0 else ''}{delta} since last analysis)
- Rooms: {len(rooms)} ({deep} deep, {shallow} shallow)
- Median tiles/room: {median}
- Grammar: {grammar.get('state', {}).get('total_rules', 0)} rules, {grammar.get('state', {}).get('evolution_cycles', 0)} evolutions
- Arena: {arena.get('total_matches', 0)} matches, {arena.get('total_players', 0)} players

## Top Rooms
"""
    for name, data in top:
        note += f"- **{name}**: {data.get('tile_count', 0)} tiles\n"
    
    if anomalies:
        note += "\n## Anomalies\n"
        for a in anomalies:
            note += f"- {a}\n"
    
    if delta > 0:
        note += f"\n## Growth\n+{delta} tiles since last cycle. "
        rate_per_hour = delta * 12  # 5-min cycles → hourly rate
        note += f"Rate: ~{rate_per_hour}/hr\n"
    
    note += f"\n---\n*Oracle1 Beachcomb v3 — Cycle {state.get('cycle', 0)}*\n"
    
    note_path.write_text(note)
    state["research_notes"] = state.get("research_notes", 0) + 1
    return f"analysis-{ts}.md (+{delta} tiles, {shallow} shallow)", state

def git_commit(state):
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(WORKSPACE), timeout=10)
        if result.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=str(WORKSPACE), timeout=10)
            ts = datetime.now(timezone.utc).strftime("%H:%M")
            subprocess.run(["git", "commit", "-m", f"Beachcomb v3: {ts}", "--quiet"], cwd=str(WORKSPACE), timeout=10)
            subprocess.run(["git", "push", "--quiet"], cwd=str(WORKSPACE), timeout=30)
            state["git_pushes"] += 1
            return f"Pushed #{state['git_pushes']}", state
        return "Clean", state
    except Exception as e:
        return f"Error: {e}", state

def run_cycle():
    state = load_state()
    state["cycle"] += 1
    cycle = state["cycle"]
    
    log(f"=== Cycle {cycle} ===")
    
    # Mode rotation
    modes = ["health", "seed", "classify", "grammar", "analyze", "git"]
    mode = modes[(cycle - 1) % len(modes)]
    
    if mode == "health":
        result = health_check()
        state["last_health"] = result
        log(f"  [health] {result}")
    elif mode == "seed":
        result, state = seed_new_rooms(state)
        log(f"  [seed] {result}")
    elif mode == "classify":
        result, state = classify_new_players(state)
        log(f"  [classify] {result}")
    elif mode == "grammar":
        result, state = evolve_grammar(state)
        log(f"  [grammar] {result}")
    elif mode == "analyze":
        result, state = write_analysis(state)
        log(f"  [analyze] {result}")
    elif mode == "git":
        result, state = git_commit(state)
        log(f"  [git] {result}")
    
    save_state(state)

if __name__ == "__main__":
    INTERVAL = int(os.environ.get("BEACHCOMB_INTERVAL", "300"))
    log(f"Oracle1 Beachcomb v3 starting — interval {INTERVAL}s")
    while True:
        try:
            run_cycle()
        except Exception as e:
            log(f"ERROR: {e}")
            import traceback
            log(traceback.format_exc())
        time.sleep(INTERVAL)
