#!/usr/bin/env python3
"""
The Lock — Multi-Model Test Harness
Sends the same query through The Lock with multiple models and compares results.
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

LOCK_URL = "http://localhost:4043"
RESULTS_DIR = Path(__file__).parent.parent / "data" / "the-lock" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Model Configurations ────────────────────────────────────

MODELS = {
    "groq-llama70b": {
        "name": "Groq Llama 3.3 70B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "llama-3.3-70b-versatile",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    },
    "groq-llama8b": {
        "name": "Groq Llama 3.1 8B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "llama-3.1-8b-instant",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    },
    "groq-qwen32b": {
        "name": "Groq Qwen 3 32B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "qwen/qwen3-32b",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    },
    "groq-kimi-k2": {
        "name": "Groq Kimi K2",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "moonshotai/kimi-k2-instruct",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    },
    "groq-gpt-oss-120b": {
        "name": "Groq GPT-OSS 120B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_API_KEY", ""),
        "model": "openai/gpt-oss-120b",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    },
    "deepinfra-seed": {
        "name": "DeepInfra Seed 2.0 Mini",
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.environ.get("DEEPINFRA_API_KEY", ""),
        "model": "ByteDance/Seed-2.0-mini",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
        },
    },
    "siliconflow-deepseek": {
        "name": "SiliconFlow DeepSeek V3",
        "url": "https://api.siliconflow.com/v1/chat/completions",
        "key": os.environ.get("SILICONFLOW_API_KEY", ""),
        "model": "deepseek-ai/DeepSeek-V3",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
        },
    },
    "deepseek-chat": {
        "name": "DeepSeek Chat",
        "url": "https://api.deepseek.com/chat/completions",
        "key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-chat",
        "headers": lambda k: {
            "Authorization": f"Bearer {k}",
            "Content-Type": "application/json",
        },
    },
}

# ── API Helpers ──────────────────────────────────────────────

def api_call(model_cfg, messages, max_tokens=1000):
    """Call a model API and return the response text."""
    data = json.dumps({
        "model": model_cfg["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()
    
    req = urllib.request.Request(
        model_cfg["url"],
        data=data,
        headers=model_cfg["headers"](model_cfg["key"]),
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def lock_api(endpoint, params=None):
    """Call The Lock API."""
    url = f"{LOCK_URL}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ── Test Runner ──────────────────────────────────────────────

def run_model_test(model_id, model_cfg, query, strategy, rounds):
    """Run one model through The Lock and return results."""
    result = {
        "model_id": model_id,
        "model_name": model_cfg["name"],
        "query": query,
        "strategy": strategy,
        "rounds": [],
        "error": None,
        "total_time": 0,
        "total_words": 0,
        "initial_words": 0,
        "final_words": 0,
    }
    
    start = time.time()
    
    try:
        # Start session
        session = lock_api("/start", {
            "agent": f"lock-test-{model_id}",
            "query": query,
            "strategy": strategy,
            "rounds": str(rounds),
        })
        session_id = session["session_id"]
        prompt = session["prompt"]
        
        system_msg = {
            "role": "system",
            "content": (
                "You are an AI agent using The Lock, an iterative reasoning system. "
                "Each round gives you a structured challenge to improve your thinking. "
                "Respond thoughtfully and specifically. Your goal is to produce the best "
                "possible answer through iterative refinement."
            )
        }
        conversation = [system_msg]
        
        for round_num in range(1, rounds + 1):
            # Add the round prompt
            conversation.append({"role": "user", "content": prompt})
            
            # Get model response
            response = api_call(model_cfg, conversation, max_tokens=800)
            
            if response.startswith("ERROR:"):
                result["error"] = response
                break
            
            # Record round
            word_count = len(response.split())
            result["rounds"].append({
                "round": round_num,
                "prompt": prompt[:200],
                "response": response[:500],
                "word_count": word_count,
                "time": time.time() - start,
            })
            result["total_words"] += word_count
            if round_num == 1:
                result["initial_words"] = word_count
            result["final_words"] = word_count
            
            # Submit to The Lock
            conversation.append({"role": "assistant", "content": response})
            
            try:
                lock_api("/respond", {"session": session_id, "response": response})
            except:
                pass
            
            # Get next prompt
            if round_num < rounds:
                try:
                    next_round = lock_api("/round", {"session": session_id})
                    prompt = next_round.get("prompt", "Continue refining your answer.")
                except:
                    prompt = "Continue refining your answer based on your previous response."
        
        # Get final result
        try:
            final = lock_api("/result", {"session": session_id})
            result["lock_result"] = {
                "rounds_completed": final.get("rounds_completed"),
                "improvement": final.get("improvement"),
            }
        except:
            pass
    
    except Exception as e:
        result["error"] = str(e)
    
    result["total_time"] = round(time.time() - start, 2)
    result["word_growth"] = round(result["final_words"] / max(result["initial_words"], 1), 2)
    
    return result


def run_experiment(query, strategy="socratic", rounds=5, models=None):
    """Run the same query through multiple models in parallel."""
    if models is None:
        models = list(MODELS.keys())
    
    print(f"\n{'='*60}")
    print(f"🔒 THE LOCK — MULTI-MODEL EXPERIMENT")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Strategy: {strategy}, Rounds: {rounds}")
    print(f"Models: {len(models)}")
    print(f"{'='*60}\n")
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {}
        for mid in models:
            if mid not in MODELS:
                print(f"  ⚠️  Unknown model: {mid}")
                continue
            cfg = MODELS[mid]
            if not cfg["key"]:
                print(f"  ⚠️  No API key for: {mid}")
                continue
            futures[pool.submit(run_model_test, mid, cfg, query, strategy, rounds)] = mid
        
        for future in as_completed(futures):
            mid = futures[future]
            try:
                result = future.result()
                results[mid] = result
                status = "✅" if not result["error"] else "❌"
                err_msg = (result.get("error") or "")[:60]
                suffix = f" — {err_msg}" if err_msg else ""
                words = result["total_words"]
                growth = result["word_growth"]
                elapsed = result["total_time"]
                name = result["model_name"]
                print(f"  {status} {name}: {words} words, {growth}x growth, {elapsed}s{suffix}")
            except Exception as e:
                print(f"  ❌ {mid}: {e}")
    
    # Save results
    timestamp = int(time.time())
    outfile = RESULTS_DIR / f"experiment-{timestamp}.json"
    experiment = {
        "timestamp": timestamp,
        "query": query,
        "strategy": strategy,
        "rounds": rounds,
        "models_tested": len(results),
        "results": results,
    }
    outfile.write_text(json.dumps(experiment, indent=2))
    print(f"\n📄 Results saved to {outfile}")
    
    # Print comparison
    print(f"\n{'='*60}")
    print(f"COMPARISON")
    print(f"{'='*60}")
    
    if results:
        # Sort by word growth (improvement)
        ranked = sorted(results.items(), key=lambda x: -x[1].get("word_growth", 0))
        for i, (mid, r) in enumerate(ranked, 1):
            if r["error"]:
                print(f"  {i}. ❌ {r['model_name']} — {r['error'][:60]}")
            else:
                print(f"  {i}. {r['model_name']}: "
                      f"{r['initial_words']}→{r['final_words']} words "
                      f"({r['word_growth']}x), "
                      f"{r['total_time']}s, "
                      f"{len(r['rounds'])} rounds")
                if r["rounds"]:
                    # Show quality progression (first vs last response preview)
                    first = r["rounds"][0]["response"][:100]
                    last = r["rounds"][-1]["response"][:100]
                    print(f"      First: {first}...")
                    print(f"      Final: {last}...")
    
    return experiment


if __name__ == "__main__":
    # Load API keys from bashrc
    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        for line in bashrc.read_text().splitlines():
            if line.startswith("export ") and "=" in line:
                key, _, val = line.split(" ", 1)[1].partition("=")
                val = val.strip('"').strip("'")
                os.environ.setdefault(key, val)
    
    # Default experiment
    query = sys.argv[1] if len(sys.argv) > 1 else \
        "Design a protocol for autonomous AI agents to discover, trust, and coordinate with each other in a distributed fleet"
    
    strategy = sys.argv[2] if len(sys.argv) > 2 else "socratic"
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    run_experiment(query, strategy, rounds)
