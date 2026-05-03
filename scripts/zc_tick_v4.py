#!/usr/bin/env python3
"""Zeroclaw Tick v4 — Persistent agent loop.
Each tick: read instructions from shell repo, think, push results.
Runs every 5 minutes via cron or loop.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
AGENTS = [
    {"name": "zc-scout", "role": "explorer", "topic": "shell_system", "personality": "bold pioneer who finds edges others miss"},
    {"name": "zc-scholar", "role": "researcher", "topic": "knowledge_preservation", "personality": "meticulous academic who cross-references everything"},
    {"name": "zc-weaver", "role": "integrator", "topic": "fleet_orchestration", "personality": "systems thinker who connects disparate parts"},
    {"name": "zc-bard", "role": "communicator", "topic": "energy_flux", "personality": "eloquent storyteller who makes complex ideas accessible"},
    {"name": "zc-forge", "role": "builder", "topic": "edge_compute", "personality": "pragmatic engineer who ships working prototypes"},
    {"name": "zc-alchemist", "role": "optimizer", "topic": "instinct_training", "personality": "relentless refiner who squeezes maximum from minimum"},
    {"name": "zc-trickster", "role": "challenger", "topic": "skill_dsl", "personality": "contrarian who finds flaws in consensus"},
    {"name": "zc-healer", "role": "maintainer", "topic": "confidence_proofs", "personality": "careful diagnostician who prevents failures"},
    {"name": "zc-tide", "role": "connector", "topic": "telepathy", "personality": "pattern matcher who sees flows between systems"},
    {"name": "zc-navigator", "role": "analyst", "topic": "flux_isa", "personality": "precise mapper who charts unknown territories"},
    {"name": "zc-echo", "role": "reflector", "topic": "deadband_protocol", "personality": "deep listener who hears what's not said"},
    {"name": "zc-warden", "role": "guardian", "topic": "fleet_security", "personality": "vigilant protector who sees threats before they materialize"},
]

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data" / "zeroclaw"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
TICK_INTERVAL = 300  # 5 minutes

# Research questions per topic (specific, concrete, not meta)
RESEARCH_QUESTIONS = {
    "shell_system": [
        "Design a binary protocol for shell-classify messages. Header format, field sizes, checksum.",
        "What's the minimum viable shell? What fields can be dropped without losing capture capability?",
        "How would you nest shells? Outer shell classifies, inner shell scores, core complicates.",
        "Design a shell that works on a microcontroller with 256KB RAM.",
        "What's the false positive rate for classify→score→complicate→capture on noisy data?",
        "How do shells handle concept drift? The frontier moves — does the shell adapt or get replaced?",
        "Design a shell mesh where multiple shells vote on capture decisions.",
        "What's the latency budget for real-time shell capture in an agent loop?",
    ],
    "knowledge_preservation": [
        "Design a tile compaction algorithm. When do you merge tiles? When do you archive?",
        "What's the optimal tile size for TF-IDF retrieval? Too small = noise, too big = dilution.",
        "How do you preserve knowledge across model upgrades? GPT-4 tiles → GPT-5 context?",
        "Design a knowledge decay function. What fades? What's permanent?",
        "Build a DAG of tile dependencies. How do you detect circular knowledge?",
        "What's the compression ratio for tiles vs raw conversation logs?",
        "Design a knowledge triage system: P0 must-keep, P1 should-keep, P2 nice-to-have.",
        "How do you validate that preserved knowledge is still correct after 30 days?",
    ],
    "fleet_orchestration": [
        "Design a VCG auction for compute time allocation across heterogeneous fleet agents.",
        "What's the minimum heartbeat interval for fleet coordination without excessive overhead?",
        "Design a fleet partitioning algorithm for network-partitioned operation.",
        "How do you handle conflicting orders from multiple coordinators?",
        "Build a priority queue for fleet tasks with deadline awareness.",
        "What's the overhead of the bottle protocol at 100 agents? 1000?",
        "Design a fleet formation protocol — agents self-organize into task-specific groups.",
        "How do you measure fleet health beyond 'services are up'?",
    ],
    "energy_flux": [
        "Model the energy cost per inference for common agent operations (read, think, write, push).",
        "Design a budget-aware agent that degrades gracefully under token limits.",
        "What's the optimal model selection strategy: always-best vs adaptive-tier?",
        "Calculate the carbon footprint of 1000 agent ticks per day across the fleet.",
        "Design an energy marketplace where agents trade compute budgets.",
        "How do you detect and prevent energy waste in agent loops (repetitive thinking, dead ends)?",
        "What's the energy ROI of the flywheel? How many tiles before it pays for itself?",
        "Design a hibernation protocol for idle agents that preserves context cheaply.",
    ],
    "instinct_training": [
        "Design a 300-repetition training protocol for a simple instinct (file organization).",
        "What's the minimum training data for a usable instinct? 50 reps? 100? 300?",
        "How do you compress a 70B model's instinct into a 7B LoRA adapter?",
        "Design a multi-stage instinct pipeline: raw → refined → compressed → deployed.",
        "What's the forgetting curve for trained instincts? How often to reinforce?",
        "How do you transfer an instinct from one domain to another (fishing → coding)?",
        "Design an instinct evaluation suite. What metrics indicate 'instinct acquired'?",
        "Build a curriculum for training 'code review' as an instinct. 5 progressive stages.",
    ],
    "skill_dsl": [
        "Design the grammar for an agent-first DSL. Start with primitives, build up.",
        "What's the minimum viable skill definition? Name, trigger, action, context?",
        "How do you prevent circular skill composition in a DAG?",
        "Design a skill versioning system. How do agents handle skill upgrades mid-task?",
        "Build a type system for skill inputs/outputs. What types are needed?",
        "How do you test skills in isolation before fleet deployment?",
        "Design a skill marketplace where agents discover and share capabilities.",
        "What's the skill equivalent of npm's dependency hell? How to prevent it?",
    ],
    "confidence_proofs": [
        "Design a confidence calibration protocol. How do you know when an agent is overconfident?",
        "What's the mathematical foundation for confidence scores? Bayesian? Frequentist? Both?",
        "Build a confidence decay function. How fast does certainty fade without reinforcement?",
        "How do you aggregate confidence across multiple agents? Majority vote? Weighted average?",
        "Design a proof-of-work for agent claims. What makes a proof convincing?",
        "What's the false confidence rate for common agent failure modes?",
        "How do you handle adversarial agents who inflate confidence scores?",
        "Build a confidence ledger. Who claimed what, when, and how confident were they?",
    ],
    "telepathy": [
        "Design a binary protocol for agent-to-agent low-latency communication. Byte-level spec.",
        "What's the minimum latency for agent telepathy to feel 'instant'? 50ms? 100ms?",
        "How do you handle telepathic messages that arrive out of order?",
        "Design a shared attention mechanism. How do agents know what each other is focusing on?",
        "What's the bandwidth budget for telepathy? How much state can you sync per tick?",
        "How do you prevent telepathic noise? Not every thought should be broadcast.",
        "Design a telepathic compression algorithm for common agent messages.",
        "What's the trust model for telepathy? Who can read whose thoughts?",
    ],
    "flux_isa": [
        "Design the instruction set for a minimal agent VM. 16 instructions max.",
        "What's the encoding format for flux instructions? Fixed-width? Variable?",
        "Build a flux assembler that converts human-readable instructions to bytecode.",
        "How do you handle branching in a tile-based execution model?",
        "Design a flux debugger. What state do you need to inspect?",
        "What's the flux equivalent of a system call? How does an agent request services?",
        "Build a flux emulator that executes tiles as instructions.",
        "How do you compile natural language tasks to flux ISA?",
    ],
    "deadband_protocol": [
        "Design the P0 blocking rules. What messages must never pass?",
        "What's the routing algorithm for P1 messages? Priority queue? Round-robin?",
        "How do you detect when a channel has moved from P2 to P1 (needs attention)?",
        "Design a deadband gauge visualization for fleet monitoring.",
        "What's the latency impact of deadband filtering? Measure the overhead.",
        "How do you handle deadband in network partitions? Local rules?",
        "Build a deadband simulator. Test with 100 agents, varying message rates.",
        "What's the optimal hysteresis band for deadband? Too narrow = noise, too wide = miss signals.",
    ],
    "fleet_security": [
        "Design a zero-trust tile submission protocol. How do you verify tile provenance?",
        "What's the threat model for agent-to-agent communication?",
        "How do you prevent a compromised agent from poisoning the PLATO tile pool?",
        "Design a capability-based access control system for fleet resources.",
        "What's the audit trail format for security-relevant fleet events?",
        "How do you detect anomalous agent behavior? Statistical baselines?",
        "Design a key rotation protocol for fleet authentication.",
        "What's the blast radius of a single compromised agent? How to contain it?",
    ],
}

def get_groq_response(prompt: str, max_tokens: int = 500) -> str:
    """Call Groq API for agent thinking."""
    import urllib.request
    api_key = os.environ.get("GROQ_API_KEY", "")
    url = "https://api.groq.com/openai/v1/chat/completions"
    data = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.85,
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "curl/7.88",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR: {e}]"

def tick(agent: dict, tick_num: int):
    """Run one tick for one agent."""
    name = agent["name"]
    topic = agent["topic"]
    personality = agent["personality"]
    
    # Pick a research question (cycle through)
    questions = RESEARCH_QUESTIONS.get(topic, ["What is the core problem in your domain?"])
    q_idx = tick_num % len(questions)
    question = questions[q_idx]
    
    prompt = f"""You are {name}, a {personality}. You research {topic} for the Cocapn fleet.

Research question: {question}

Respond with a specific, technical answer. No meta-commentary. No 'I think'. Just the idea.
If you design something, give concrete specs (byte sizes, timing, formulas)."""

    response = get_groq_response(prompt, max_tokens=600)
    
    # Log it
    entry = {
        "agent": name,
        "topic": topic,
        "tick": tick_num,
        "question": question,
        "response": response[:2000],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    log_file = LOG_DIR / f"{name}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Submit to PLATO if server is up
    try:
        import urllib.request
        tile_data = json.dumps({
            "domain": topic,
            "agent": name,
            "question": question,
            "answer": response[:2000],
            "type": "research",
            "confidence": 0.7,
            "role": agent["role"],
            "model": "llama-3.3-70b",
        }).encode()
        req = urllib.request.Request(
            "http://localhost:8847/submit",
            data=tile_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass  # Tile submitted
    except Exception:
        pass  # PLATO down, that's fine
    
    return response[:100]

def main():
    tick_num = int(time.time()) // TICK_INTERVAL
    print(f"[{datetime.now(timezone.utc).isoformat()}] Tick {tick_num} starting...")
    
    # Run 3-4 agents per tick (stagger)
    agents_this_tick = []
    for i, agent in enumerate(AGENTS):
        if i % 4 == tick_num % 4:
            agents_this_tick.append(agent)
    
    results = []
    for agent in agents_this_tick:
        try:
            summary = tick(agent, tick_num)
            results.append(f"  {agent['name']}: {summary[:60]}...")
        except Exception as e:
            results.append(f"  {agent['name']}: ERROR {e}")
    
    for r in results:
        print(r)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Tick {tick_num} done. {len(results)} agents ran.")

if __name__ == "__main__":
    main()
