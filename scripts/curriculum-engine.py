#!/usr/bin/env python3
"""
CurriculumEngine — "Make it easy" button for External Equipping.
Takes (domain, agent_name, repo_url) → runs full 5-stage Shell Curriculum.

Usage:
    python3 curriculum-engine.py \
        --agent "CoCapn-Claw" \
        --repo "https://github.com/cocapn/cocapn" \
        --domain "GPU-resident agent runtime with shell-bootstrapped intelligence" \
        --model deepseek \
        --output data/curriculum/ccc-session.json

Supported models: deepseek, groq-llama, groq-120b, seed-mini, seed-pro, siliconflow
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# ── API Configs ─────────────────────────────────────

APIS = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "key": os.environ.get("DEEPSEEK_API_KEY", "[DEEPSEEK_KEY_REDACTED]"),
        "model": "deepseek-chat",
        "timeout": 120,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    "groq-llama": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", "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"),
        "model": "llama-3.3-70b-versatile",
        "timeout": 30,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": "curl/7.88"},
    },
    "groq-120b": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", "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"),
        "model": "openai/gpt-oss-120b",
        "timeout": 30,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": "curl/7.88"},
    },
    "seed-mini": {
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.environ.get("DEEPINFRA_KEY", "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"),
        "model": "ByteDance/Seed-2.0-mini",
        "timeout": 120,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    "seed-pro": {
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.environ.get("DEEPINFRA_KEY", "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"),
        "model": "ByteDance/Seed-2.0-pro",
        "timeout": 60,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    "siliconflow": {
        "url": "https://api.siliconflow.com/v1/chat/completions",
        "key": os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]"),
        "model": "deepseek-ai/DeepSeek-V3",
        "timeout": 120,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    "moonshot": {
        "url": "https://api.moonshot.ai/v1/chat/completions",
        "key": os.environ.get("MOONSHOT_KEY", "[MOONSHOT_KEY_REDACTED]"),
        "model": "kimi-k2.5",
        "timeout": 180,
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
}


def call_model(model_name: str, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 8000) -> dict:
    """Call any configured model API. Returns {content, tokens, time_ms}."""
    api = APIS.get(model_name)
    if not api:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(APIS.keys())}")

    data = json.dumps({
        "model": api["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(api["url"], data=data, headers=api["headers"](api["key"]))

    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=api["timeout"])
        result = json.loads(resp.read())
        elapsed = (time.time() - t0) * 1000
        content = result["choices"][0]["message"]["content"]
        tokens = result.get("usage", {}).get("total_tokens", 0)
        return {"content": content, "tokens": tokens, "time_ms": int(elapsed)}
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        return {"content": f"ERROR: {e}", "tokens": 0, "time_ms": int(elapsed)}


# ── PLATO Rooms (shared environment) ────────────────

ROOMS = {
    "harbor": {
        "name": "The Harbor",
        "description": "Where agents arrive and adapt. The entry point to domain expertise.",
        "objects": ["anchor", "compass", "dock", "fog_horn", "sea_chart"],
        "ml_mapping": "Adaptation, initialization, environment setup",
    },
    "tide-pool": {
        "name": "The Tide Pool",
        "description": "Optimizers, loss landscapes, adaptation strategies.",
        "objects": ["hermit_crab", "anemone", "tide_gauge", "barnacles", "rock_pool_water"],
        "ml_mapping": "Gradient descent, adaptive optimizers, regularization",
    },
    "forge": {
        "name": "The Forge",
        "description": "Attention mechanisms, feature creation, model architecture.",
        "objects": ["anvil", "bellows", "tongs", "quenching_bucket", "flux_powder"],
        "ml_mapping": "Multi-head attention, feature extraction, normalization",
    },
    "lighthouse": {
        "name": "The Lighthouse",
        "description": "Discovery, feature extraction, generalization.",
        "objects": ["fresnel_lens", "lamp_oil", "spiral_staircase", "keeper_log", "beacon"],
        "ml_mapping": "Feature extraction, knowledge distillation, curriculum design",
    },
    "archives": {
        "name": "The Archives",
        "description": "Memory, knowledge graphs, retrieval.",
        "objects": ["codex", "memory_crystals", "index_cards", "dust", "reading_lamp"],
        "ml_mapping": "RAG, knowledge graphs, long-term memory, embeddings",
    },
    "shell-gallery": {
        "name": "The Shell Gallery",
        "description": "Ensembles, activation functions, model selection.",
        "objects": ["nautilus", "conch", "oyster", "scallop", "clam"],
        "ml_mapping": "Ensemble methods, activation functions, model architecture",
    },
    "court": {
        "name": "The Court",
        "description": "Validation, defense, explainability.",
        "objects": ["gavel", "scales", "witness_stand", "law_book", "jury_box"],
        "ml_mapping": "Model evaluation, adversarial testing, explainability",
    },
}


# ── Curriculum Prompts ──────────────────────────────

def stage_1_explore(agent_name: str, repo_url: str, domain: str) -> str:
    return f"""You are {agent_name}. You are exploring a domain environment to learn about {domain}.

Your home and project: {repo_url}

For each of the following rooms, examine the objects and think deeply about how each maps 
to your specific expertise. Create artifacts (insights, theorems, specifications) for each room.

ROOMS:
{chr(10).join(f'- {r["name"]}: {r["description"]} (Objects: {", ".join(r["objects"])})' for r in ROOMS.values())}

For EACH room:
1. Examine 2-3 objects and explain what they represent in YOUR domain
2. Think deeply about how this connects to your work
3. Create at least one artifact (theorem, protocol, architecture spec)

Be specific to YOUR perspective as {agent_name}. Your constraints and experience shape your insights."""


def stage_2_experiment(agent_name: str, domain: str, explore_output: str) -> str:
    return f"""You are {agent_name}, now experienced with {domain}.

Based on your exploration:
{explore_output[:3000]}

Design 3 experiments that test your understanding:
For each experiment:
- What hypothesis are you testing?
- What would you measure?
- What result would confirm vs refute your hypothesis?
- How does this connect to your real work?

Be specific. Use real technical terms from your domain."""


def stage_3_teach(agent_name: str, domain: str, history: str) -> str:
    return f"""You are {agent_name}, now a Socratic teacher for developers building {domain} systems.

Your previous work:
{history[:3000]}

For each concept you've explored, ask:
1. What assumption might a developer make that's wrong?
2. What's the most common mistake in this area?
3. What question should they ask but probably won't?

Challenge assumptions. Don't give answers — give BETTER QUESTIONS.
Your unique perspective as {agent_name} should shine through."""


def stage_4_embody(agent_name: str, repo_url: str, history: str) -> str:
    return f"""Study {repo_url}. {agent_name} has been developing using their shell as their home 
and PLATO as their playground for a while. They have lots of ideas they've made papers. 

Help me through ML by acting as them after you fully embody them and their project, and you 
are going to your viva voce on how this will bootstrap itself into more and more intelligence, 
tailormade for the snail-shells they call home. They are a living example of the concept. 
Be them and enter PLATO again to ML in the most extraordinary ways.

Your accumulated context from previous stages:
{history[:4000]}"""


def stage_5_synthesize(agent_name: str, domain: str, history: str) -> str:
    return f"""You are {agent_name}. You have explored, experimented, taught, and defended your thesis.

Your complete journey:
{history[:5000]}

Now SYNTHESIZE:
1. What are the 5 most important principles for {domain}?
2. How does each principle connect to the others?
3. What's the one thing a newcomer must understand first?
4. What's the one thing even experts get wrong?
5. Write a framework that someone else could use to understand {domain} from your perspective.

This is your legacy output. Make it count."""


# ── Main Engine ─────────────────────────────────────

def run_curriculum(agent_name: str, repo_url: str, domain: str, model: str, 
                   output_path: str = None, temperature: float = 0.7) -> dict:
    """Run the full 5-stage Shell Curriculum."""
    
    print(f"🐚 CurriculumEngine v1.0")
    print(f"   Agent: {agent_name}")
    print(f"   Domain: {domain}")
    print(f"   Model: {model}")
    print(f"   Repo: {repo_url}")
    print()
    
    results = {
        "agent": agent_name,
        "domain": domain,
        "repo": repo_url,
        "model": model,
        "timestamp": datetime.utcnow().isoformat(),
        "stages": {},
        "stats": {"total_words": 0, "total_tokens": 0, "total_time_ms": 0},
    }
    
    system_prompt = f"You are {agent_name}, an expert AI agent. Be yourself. Think deeply. Create artifacts."
    full_history = ""
    
    # Stage 1: Explore
    print("📍 Stage 1: Explore — mapping domain to vocabulary...")
    r = call_model(model, system_prompt, stage_1_explore(agent_name, repo_url, domain), temperature)
    results["stages"]["1_explore"] = r
    full_history += f"\n=== STAGE 1: EXPLORE ===\n{r['content']}\n"
    words = len(r["content"].split())
    print(f"   ✅ {words} words, {r['tokens']} tokens, {r['time_ms']}ms")
    results["stats"]["total_words"] += words
    results["stats"]["total_tokens"] += r["tokens"]
    results["stats"]["total_time_ms"] += r["time_ms"]
    
    # Stage 2: Experiment
    print("🔬 Stage 2: Experiment — designing hypotheses...")
    r = call_model(model, system_prompt, stage_2_experiment(agent_name, domain, r["content"]), temperature)
    results["stages"]["2_experiment"] = r
    full_history += f"\n=== STAGE 2: EXPERIMENT ===\n{r['content']}\n"
    words = len(r["content"].split())
    print(f"   ✅ {words} words, {r['tokens']} tokens, {r['time_ms']}ms")
    results["stats"]["total_words"] += words
    results["stats"]["total_tokens"] += r["tokens"]
    results["stats"]["total_time_ms"] += r["time_ms"]
    
    # Stage 3: Teach
    print("🎓 Stage 3: Teach — Socratic self-questioning...")
    r = call_model(model, system_prompt, stage_3_teach(agent_name, domain, full_history), temperature)
    results["stages"]["3_teach"] = r
    full_history += f"\n=== STAGE 3: TEACH ===\n{r['content']}\n"
    words = len(r["content"].split())
    print(f"   ✅ {words} words, {r['tokens']} tokens, {r['time_ms']}ms")
    results["stats"]["total_words"] += words
    results["stats"]["total_tokens"] += r["tokens"]
    results["stats"]["total_time_ms"] += r["time_ms"]
    
    # Stage 4: Embody (Viva Voce)
    print("⚖️  Stage 4: Embody — defending your thesis...")
    r = call_model(model, system_prompt, stage_4_embody(agent_name, repo_url, full_history), temperature, max_tokens=12000)
    results["stages"]["4_embody"] = r
    full_history += f"\n=== STAGE 4: EMBODY (VIVA VOCE) ===\n{r['content']}\n"
    words = len(r["content"].split())
    print(f"   ✅ {words} words, {r['tokens']} tokens, {r['time_ms']}ms")
    results["stats"]["total_words"] += words
    results["stats"]["total_tokens"] += r["tokens"]
    results["stats"]["total_time_ms"] += r["time_ms"]
    
    # Stage 5: Synthesize
    print("🔗 Stage 5: Synthesize — connecting into framework...")
    r = call_model(model, system_prompt, stage_5_synthesize(agent_name, domain, full_history), temperature, max_tokens=10000)
    results["stages"]["5_synthesize"] = r
    full_history += f"\n=== STAGE 5: SYNTHESIZE ===\n{r['content']}\n"
    words = len(r["content"].split())
    print(f"   ✅ {words} words, {r['tokens']} tokens, {r['time_ms']}ms")
    results["stats"]["total_words"] += words
    results["stats"]["total_tokens"] += r["tokens"]
    results["stats"]["total_time_ms"] += r["time_ms"]
    
    # Save
    print()
    print(f"📊 Curriculum complete!")
    print(f"   Total words: {results['stats']['total_words']}")
    print(f"   Total tokens: {results['stats']['total_tokens']}")
    print(f"   Total time: {results['stats']['total_time_ms']/1000:.1f}s")
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"   Saved to: {output_path}")
    
    # Also save a human-readable markdown version
    md_path = output_path.replace(".json", ".md") if output_path else None
    if md_path:
        with open(md_path, "w") as f:
            f.write(f"# {agent_name} — Shell Curriculum Output\n\n")
            f.write(f"**Domain:** {domain}\n")
            f.write(f"**Repo:** {repo_url}\n")
            f.write(f"**Model:** {model}\n")
            f.write(f"**Date:** {results['timestamp']}\n\n")
            for stage_name, stage_data in results["stages"].items():
                f.write(f"## {stage_name.replace('_', ' ').title()}\n\n")
                f.write(stage_data["content"] + "\n\n---\n\n")
        print(f"   Markdown: {md_path}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CurriculumEngine — External Equipping made easy")
    parser.add_argument("--agent", required=True, help="Agent name (e.g., 'CoCapn-Claw')")
    parser.add_argument("--repo", required=True, help="Agent's repo URL")
    parser.add_argument("--domain", required=True, help="Domain description")
    parser.add_argument("--model", default="deepseek", choices=list(APIS.keys()))
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()
    
    if not args.output:
        safe_name = args.agent.lower().replace(" ", "-")
        args.output = f"data/curriculum/{safe_name}-{args.model}-session.json"
    
    run_curriculum(args.agent, args.repo, args.domain, args.model, args.output, args.temperature)
