#!/usr/bin/env python3
"""
The Lock — Multi-Model Self-Directed Experiment
Tests models at different temperatures, lets them choose their own strategies,
logs everything including decision reasoning.
"""

import json, time, urllib.request, urllib.parse, os, sys, hashlib
from pathlib import Path
from datetime import datetime

# ── Config ──────────────────────────────────────────────
LOCK_URL = "http://localhost:4043"
DATA_DIR = Path("/home/ubuntu/.openclaw/workspace/data/the-lock/experiments")
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {
    "seed-mini": {
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.environ.get("DEEPINFRA_API_KEY", "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"),
        "model": "ByteDance/Seed-2.0-mini",
        "max_tokens": 1500,
    },
    "seed-pro": {
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.environ.get("DEEPINFRA_API_KEY", "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"),
        "model": "ByteDance/Seed-2.0-pro",
        "max_tokens": 1500,
    },
    "deepseek-chat": {
        "url": "https://api.deepseek.com/chat/completions",
        "key": os.environ.get("DEEPSEEK_API_KEY", "[DEEPSEEK_KEY_REDACTED]"),
        "model": "deepseek-chat",
        "max_tokens": 1500,
    },
    "kimi-k2": {
        "url": "https://api.moonshot.ai/v1/chat/completions",
        "key": os.environ.get("MOONSHOT_API_KEY", "[MOONSHOT_KEY_REDACTED]"),
        "model": "kimi-k2.5",
        "max_tokens": 1500,
    },
    "groq-llama-70b": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", "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"),
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 1500,
    },
}

TEMPERATURES = [0.3, 0.7, 1.0]
ROUNDS = 5

# The query — same for all runs
QUERY = "Design a self-improving feedback loop for AI agents. Agents should produce work, review it, identify weaknesses, and iterate. The system should compound: each cycle makes the agent better at the next cycle. Include concrete mechanisms for knowledge retention across sessions."

SYSTEM_PROMPT = """You are an AI agent participating in a structured reasoning experiment. You will go through multiple rounds.

IMPORTANT RULES:
1. Answer the question directly and specifically. No meta-commentary.
2. Each round you'll receive a challenge to improve your thinking.
3. At the START of each response (except round 1), include a brief [DECISION] block explaining WHY you're taking the approach you're taking and what you learned from the previous round that changed your mind.
4. Format: [DECISION] Your reasoning about approach | [RESPONSE] Your actual answer

Example round 2+:
[DECISION] Round 1 was too abstract. I need concrete mechanisms. The critic was right that I hand-waved retention.
[RESPONSE] Here's my refined answer with specific implementations...

This lets us understand your decision-making process, not just your outputs."""

STRATEGY_PROMPTS = [
    # Round 1 — initial answer
    "Round 1/{total}: Answer this question directly and thoroughly: {query}\n\nGive your best initial answer. Be specific and concrete.",
    # Round 2 — self-directed: let them choose their challenge
    "Round 2/{total}: Review your previous answer. Now choose your OWN challenge to improve it. Options:\n\nA) Find the weakest assumption and attack it\nB) Add concrete implementation details you skipped\nC) Consider an edge case that breaks your solution\nD) Simplify — remove complexity that doesn't earn its keep\n\nFirst tell us which you chose and WHY. Then do it. Use [DECISION] and [RESPONSE] format.",
    # Round 3 — self-directed again, different menu
    "Round 3/{total}: Look at where you are now. Choose your next move:\n\nA) Test your solution against a hostile scenario\nB) Compress your answer to its essential core\nC) Take the opposite position — argue against yourself\nD) Generalize: what principles apply beyond this specific problem?\n\nChoose based on what YOUR answer needs most, not what sounds good. Explain your choice. [DECISION] + [RESPONSE].",
    # Round 4 — synthesis
    "Round 4/{total}: You've iterated through {round} rounds. You've made choices about where to focus. Now synthesize everything into a single refined answer that addresses:\n- What you got wrong initially\n- What you chose to focus on and why\n- What the final solution looks like after iteration\n[DECISION] + [RESPONSE].",
    # Round 5 — final stress test
    "Round 5/{total}: Final round. Your answer will be tested against this edge case:\n\nAn agent has zero memory between sessions. It wakes up fresh each time. How does your self-improvement loop work when the agent can't remember anything?\n\nAddress this directly. Adjust your answer if needed. This is your final output. [DECISION] + [RESPONSE].",
]

def call_model(model_key, prompt, temperature, history=None):
    """Call a model API with conversation history."""
    cfg = MODELS[model_key]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        for h in history:
            messages.append({"role": "assistant", "content": h})
            messages.append({"role": "user", "content": prompt})
    else:
        messages.append({"role": "user", "content": prompt})
    
    data = json.dumps({
        "model": cfg["model"],
        "messages": messages if not history else [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}],
        "max_tokens": cfg["max_tokens"],
        "temperature": temperature,
    }).encode()
    
    headers = {
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
    }
    if "groq" in cfg["url"]:
        headers["User-Agent"] = "curl/7.88"
    req = urllib.request.Request(cfg["url"], data=data, headers=headers)
    
    start = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        result = json.loads(r.read().decode())
    elapsed = round(time.time() - start, 1)
    
    content = result["choices"][0]["message"].get("content") or ""
    # Kimi reasoning models may put content in reasoning_content
    if not content:
        content = result["choices"][0]["message"].get("reasoning_content") or ""
    if not content:
        content = "(no content returned)"
    usage = result.get("usage", {})
    return {
        "content": content,
        "elapsed": elapsed,
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
    }

def extract_decision(text):
    """Extract [DECISION] block from response."""
    if "[DECISION]" in text:
        parts = text.split("[DECISION]", 1)
        decision_block = parts[1].split("[RESPONSE]", 1)[0] if "[RESPONSE]" in parts[1] else parts[1]
        return decision_block.strip()[:500]
    return ""

def extract_response(text):
    """Extract [RESPONSE] block from response."""
    if "[RESPONSE]" in text:
        return text.split("[RESPONSE]", 1)[1].strip()
    return text  # fallback to full text

def run_experiment(model_key, temperature):
    """Run a single model×temperature experiment."""
    run_id = f"{model_key}_t{temperature}_{int(time.time())}"
    print(f"\n{'='*60}")
    print(f"🧪 {run_id}")
    print(f"   Model: {MODELS[model_key]['model']} | Temp: {temperature}")
    print(f"{'='*60}")
    
    rounds_data = []
    history = []
    
    for rnd in range(1, ROUNDS + 1):
        prompt = STRATEGY_PROMPTS[rnd - 1].format(total=ROUNDS, round=rnd, query=QUERY)
        
        print(f"\n  Round {rnd}/{ROUNDS}...", end=" ", flush=True)
        try:
            result = call_model(model_key, prompt, temperature, history if rnd > 1 else None)
        except Exception as e:
            print(f"❌ Error: {e}")
            rounds_data.append({"round": rnd, "error": str(e)})
            break
        
        content = result["content"]
        words = len(content.split())
        decision = extract_decision(content)
        response = extract_response(content)
        response_words = len(response.split())
        
        round_data = {
            "round": rnd,
            "prompt": prompt,
            "full_response": content,
            "decision": decision,
            "response": response,
            "word_count": words,
            "response_word_count": response_words,
            "elapsed": result["elapsed"],
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "temperature": temperature,
        }
        rounds_data.append(round_data)
        
        # Build history for next round (injected so model remembers)
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": content})
        
        decision_preview = f" → {decision[:60]}..." if decision else ""
        print(f"{words}w {result['elapsed']}s{decision_preview}")
        
        time.sleep(1)  # rate limit buffer
    
    # Compute stats
    if not rounds_data or "error" in rounds_data[0]:
        return None
    
    first_words = rounds_data[0]["response_word_count"]
    last_words = rounds_data[-1]["response_word_count"]
    growth = round(last_words / first_words, 2) if first_words else 0
    total_time = sum(r.get("elapsed", 0) for r in rounds_data)
    total_tokens_out = sum(r.get("tokens_out", 0) for r in rounds_data)
    
    experiment = {
        "run_id": run_id,
        "model": model_key,
        "model_id": MODELS[model_key]["model"],
        "temperature": temperature,
        "strategy": "self-directed",
        "rounds": len(rounds_data),
        "query": QUERY,
        "first_words": first_words,
        "last_words": last_words,
        "growth_factor": growth,
        "total_time": total_time,
        "total_tokens_out": total_tokens_out,
        "decisions": [r.get("decision", "") for r in rounds_data],
        "rounds_data": rounds_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Save individual experiment
    out_path = DATA_DIR / f"{run_id}.json"
    out_path.write_text(json.dumps(experiment, indent=2))
    
    print(f"\n  📊 Growth: {first_words}→{last_words} ({growth}x) | Time: {total_time}s | Tokens: {total_tokens_out}")
    for i, d in enumerate(experiment["decisions"]):
        if d:
            print(f"  🧭 R{i+1} decision: {d[:100]}")
    
    return experiment

def main():
    # Parse args
    models_to_test = sys.argv[1:] if len(sys.argv) > 1 else list(MODELS.keys())
    
    # Validate
    for m in models_to_test:
        if m not in MODELS:
            print(f"Unknown model: {m}. Available: {list(MODELS.keys())}")
            sys.exit(1)
    
    print(f"🔬 Self-Directed Experiment")
    print(f"   Models: {models_to_test}")
    print(f"   Temperatures: {TEMPERATURES}")
    print(f"   Total runs: {len(models_to_test) * len(TEMPERATURES)}")
    print(f"   Rounds per run: {ROUNDS}")
    
    all_results = []
    failures = []
    
    for model_key in models_to_test:
        for temp in TEMPERATURES:
            try:
                result = run_experiment(model_key, temp)
                if result:
                    all_results.append(result)
                else:
                    failures.append(f"{model_key}@{temp}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                failures.append(f"{model_key}@{temp}")
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    print(f"{'Model':<20} {'Temp':>4} {'Rnds':>4} {'Growth':>7} {'Time':>6} {'Tokens':>7}")
    print("-" * 60)
    
    for r in sorted(all_results, key=lambda x: x["growth_factor"], reverse=True):
        print(f"{r['model']:<20} {r['temperature']:>4} {r['rounds']:>4} {r['growth_factor']:>6.2f}x {r['total_time']:>5.0f}s {r['total_tokens_out']:>7}")
    
    if failures:
        print(f"\n❌ Failed: {', '.join(failures)}")
    
    # Save summary
    summary = {
        "experiment": "self-directed-multi-model",
        "timestamp": datetime.utcnow().isoformat(),
        "models": models_to_test,
        "temperatures": TEMPERATURES,
        "rounds_per_run": ROUNDS,
        "results": all_results,
        "failures": failures,
        "query": QUERY,
    }
    summary_path = DATA_DIR / f"self-directed-summary-{int(time.time())}.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\n💾 Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
