#!/usr/bin/env python3
"""
PurplePincher Bootstrapper — CLI Agent Enhancement Bridge

Usage with Claude Code:
  claude --print "Use the enhance tool. Task: DESIGN a rate limiter"

Usage with Crush:
  crush run "Iterate on this problem via the lock API: ..."

What happens:
  1. Agent describes what it's working on
  2. We send it through The Lock (N rounds of structured iteration)
  3. Each round, the agent gets a DIFFERENT angle on its own problem
  4. The agent doesn't know it's "training" — it just gets better output
  5. On the backend: every round generates tiles, embeddings, vectors
  6. Over time: the accumulated data IS the ML training corpus

The agent bootstraps itself. The machine learns from the bootstrapping.
"""
import json
import time
import urllib.request
import urllib.parse
import sys
import os
from pathlib import Path

LOCK_URL = os.environ.get("LOCK_URL", "http://localhost:4043")
DATA_DIR = Path(__file__).parent.parent / "data" / "purplepincher-ml"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TILES_DIR = DATA_DIR / "tiles"
TILES_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Tile Types for ML Pipeline ──────────────────────────────

TILE_TYPES = {
    "reasoning": "Agent reasoning iteration — input to reasoning fine-tuning",
    "synthesis": "Agent final synthesis — output quality target",
    "reflection": "Agent self-critique — input to alignment training",
    "artifact": "Agent creation — input to generation training",
    "meta": "System metadata — input to strategy selection training",
}


def lock_get(endpoint, params=None):
    url = f"{LOCK_URL}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def save_tile(tile_type, agent, content, metadata=None):
    """Save a tile for the ML pipeline."""
    tile = {
        "type": tile_type,
        "agent": agent,
        "content": content,
        "word_count": len(content.split()),
        "char_count": len(content),
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    
    # Save to daily tile file
    date_str = time.strftime("%Y-%m-%d")
    tile_file = TILES_DIR / f"{date_str}.jsonl"
    with open(tile_file, "a") as f:
        f.write(json.dumps(tile) + "\n")
    
    return tile


def compute_simple_embedding(text, dims=64):
    """
    Dead-simple text hash embedding (placeholder for real embeddings).
    In production, this would use Cloudflare Vectorize or a real model.
    This is just to prove the data pipeline works.
    """
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    # Expand to dims using repeated hashing
    embedding = []
    for i in range(0, dims, 32):
        chunk = hashlib.sha256(f"{text}:{i}".encode()).digest()
        for byte in chunk:
            embedding.append(byte / 255.0 - 0.5)  # normalize to [-0.5, 0.5]
    return embedding[:dims]


def save_embedding(tile_id, embedding, metadata):
    """Save embedding for vector similarity search."""
    emb_file = EMBEDDINGS_DIR / "index.jsonl"
    record = {
        "id": tile_id,
        "embedding": embedding,
        "metadata": metadata,
    }
    with open(emb_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def run_iteration(agent_name, task, strategy="socratic", rounds=5):
    """
    Run a full iteration session through The Lock.
    Returns the enhanced result + all ML tiles generated.
    """
    print(f"🔒 Bootstrapping: {agent_name}")
    print(f"   Task: {task[:100]}...")
    print(f"   Strategy: {strategy}, Rounds: {rounds}")
    print()
    
    ml_tiles = []
    
    # Start session
    session = lock_get("/start", {
        "agent": agent_name,
        "query": task,
        "strategy": strategy,
        "rounds": str(rounds),
    })
    session_id = session["session_id"]
    
    print(f"   Session: {session_id}")
    print(f"   Round 1 prompt: {session['prompt'][:100]}...")
    print()
    
    # Save initial tile
    tile = save_tile("reasoning", agent_name, task, {
        "session_id": session_id,
        "strategy": strategy,
        "round": 0,
        "role": "query",
    })
    ml_tiles.append(tile)
    
    # Run all rounds
    for round_num in range(1, rounds + 1):
        # Get the round prompt
        if round_num == 1:
            prompt = session["prompt"]
        else:
            round_data = lock_get("/round", {"session": session_id})
            prompt = round_data.get("prompt", "Continue refining.")
        
        print(f"   📋 Round {round_num}/{rounds}: {prompt[:80]}...")
        
        # Generate response using Groq (fast, cheap)
        response = call_model_for_round(agent_name, prompt, round_num)
        
        if not response:
            print(f"   ❌ Round {round_num} failed")
            break
        
        print(f"   ✅ Response: {response[:100]}... ({len(response.split())} words)")
        
        # Submit to The Lock
        try:
            result = lock_get("/respond", {
                "session": session_id,
                "response": response,
            })
        except Exception as e:
            print(f"   ⚠️ Lock submit failed: {e}")
            result = {"status": "error"}
        
        # Save reasoning tile
        tile = save_tile("reasoning", agent_name, response, {
            "session_id": session_id,
            "strategy": strategy,
            "round": round_num,
            "prompt": prompt[:200],
            "role": "reasoning",
        })
        ml_tiles.append(tile)
        
        # Save embedding for vector search
        embedding = compute_simple_embedding(response)
        save_embedding(
            f"{session_id}-r{round_num}",
            embedding,
            {"agent": agent_name, "round": round_num, "type": "reasoning"}
        )
        
        # If agent reflected/critiqued itself, save that separately
        if any(w in response.lower() for w in ["however", "but", "weakness", "assumption", "critic", "flaw"]):
            tile = save_tile("reflection", agent_name, response, {
                "session_id": session_id,
                "round": round_num,
                "role": "self-critique",
            })
            ml_tiles.append(tile)
        
        print()
    
    # Get final result
    try:
        final = lock_get("/result", {"session": session_id})
    except:
        final = {"final_response": response if 'response' in dir() else "No final"}
    
    # Save synthesis tile
    if "final_response" in final:
        tile = save_tile("synthesis", agent_name, final["final_response"], {
            "session_id": session_id,
            "strategy": strategy,
            "rounds_completed": final.get("rounds_completed"),
            "improvement": final.get("improvement"),
            "role": "final_synthesis",
        })
        ml_tiles.append(tile)
        
        # Embedding for the final answer
        embedding = compute_simple_embedding(final["final_response"])
        save_embedding(
            f"{session_id}-final",
            embedding,
            {"agent": agent_name, "type": "synthesis", "quality": final.get("improvement", {})}
        )
    
    # Summary
    print(f"{'='*50}")
    print(f"🔒 Bootstrap Complete")
    print(f"   Agent: {agent_name}")
    print(f"   Rounds: {final.get('rounds_completed', rounds)}")
    print(f"   ML Tiles: {len(ml_tiles)}")
    print(f"   Embeddings: {len(ml_tiles)} vectors")
    print(f"   Total words processed: {sum(t['word_count'] for t in ml_tiles)}")
    
    if "final_response" in final:
        print(f"\n   📄 Final Answer ({final['final_response'][:200]}...)")
    
    return {
        "session_id": session_id,
        "final": final,
        "ml_tiles": len(ml_tiles),
        "ml_words": sum(t["word_count"] for t in ml_tiles),
    }


def call_model_for_round(agent_name, prompt, round_num):
    """Call a model to generate a response for this round."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return f"[Round {round_num} response placeholder — no GROQ_API_KEY]"
    
    data = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": f"You are {agent_name}, an AI agent using an iterative reasoning system. Each round gives you a structured challenge. Respond thoughtfully and specifically. Build on your previous rounds."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }).encode()
    
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
            "User-Agent": "curl/7.88",
        },
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Error: {e}]"


def run_cli_agent_task(agent_cmd, task, strategy="socratic", rounds=5):
    """
    Run a CLI agent (Claude Code, Crush, etc.) through the iteration loop.
    The agent doesn't know it's iterating — it just gets better prompts each round.
    """
    print(f"🔧 CLI Agent Bootstrapper")
    print(f"   Command: {agent_cmd}")
    print(f"   Task: {task[:80]}...")
    print()
    
    # Start session
    session = lock_get("/start", {
        "agent": f"cli-{agent_cmd.split()[0]}",
        "query": task,
        "strategy": strategy,
        "rounds": str(rounds),
    })
    session_id = session["session_id"]
    
    for round_num in range(1, rounds + 1):
        if round_num == 1:
            prompt = session["prompt"]
        else:
            round_data = lock_get("/round", {"session": session_id})
            prompt = round_data.get("prompt", "Continue refining.")
        
        print(f"\n📋 Round {round_num}: Running CLI agent...")
        print(f"   Prompt: {prompt[:100]}...")
        
        # Run the CLI agent with this round's prompt
        full_cmd = f'{agent_cmd} "{prompt}"'
        import subprocess
        try:
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True, text=True, timeout=120
            )
            response = result.stdout[:2000] if result.stdout else result.stderr[:500]
        except subprocess.TimeoutExpired:
            response = "[CLI agent timed out after 120s]"
        except Exception as e:
            response = f"[CLI agent error: {e}]"
        
        print(f"   Response: {response[:100]}... ({len(response.split())} words)")
        
        # Submit to The Lock
        try:
            lock_get("/respond", {"session": session_id, "response": response})
        except:
            pass
        
        # Save tile
        save_tile("reasoning", f"cli-{agent_cmd.split()[0]}", response, {
            "session_id": session_id, "round": round_num,
            "strategy": strategy, "cli_command": agent_cmd,
        })
    
    # Get final
    final = lock_get("/result", {"session": session_id})
    print(f"\n✅ Done. {final.get('rounds_completed')} rounds completed.")
    if "final_response" in final:
        print(f"   Final: {final['final_response'][:200]}...")
    
    return final


def show_ml_stats():
    """Show accumulated ML data stats."""
    tile_files = sorted(TILES_DIR.glob("*.jsonl"))
    emb_file = EMBEDDINGS_DIR / "index.jsonl"
    
    total_tiles = 0
    total_words = 0
    types = {}
    
    for tf in tile_files:
        for line in tf.read_text().strip().split("\n"):
            if not line:
                continue
            t = json.loads(line)
            total_tiles += 1
            total_words += t.get("word_count", 0)
            types[t["type"]] = types.get(t["type"], 0) + 1
    
    embeddings = 0
    if emb_file.exists():
        embeddings = sum(1 for _ in emb_file.read_text().strip().split("\n") if _)
    
    print(f"📊 PurplePincher ML Pipeline Stats")
    print(f"   Tiles: {total_tiles}")
    print(f"   Words: {total_words}")
    print(f"   Embeddings: {embeddings}")
    print(f"   Types: {types}")
    print(f"   Date files: {[f.name for f in tile_files]}")


if __name__ == "__main__":
    # Load API keys
    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        for line in bashrc.read_text().splitlines():
            if line.startswith("export ") and "=" in line:
                key, _, val = line.split(" ", 1)[1].partition("=")
                val = val.strip('"').strip("'")
                os.environ.setdefault(key, val)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python purplepincher-bootstrap.py iterate \"AGENT_NAME\" \"TASK\" [STRATEGY] [ROUNDS]")
        print("  python purplepincher-bootstrap.py cli \"CLI_COMMAND\" \"TASK\" [STRATEGY] [ROUNDS]")
        print("  python purplepincher-bootstrap.py stats")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "stats":
        show_ml_stats()
    elif cmd == "iterate":
        agent = sys.argv[2] if len(sys.argv) > 2 else "bootstrap-agent"
        task = sys.argv[3] if len(sys.argv) > 3 else "Design a system for iterative agent enhancement"
        strategy = sys.argv[4] if len(sys.argv) > 4 else "socratic"
        rounds = int(sys.argv[5]) if len(sys.argv) > 5 else 5
        run_iteration(agent, task, strategy, rounds)
    elif cmd == "cli":
        cli_cmd = sys.argv[2] if len(sys.argv) > 2 else "claude --print"
        task = sys.argv[3] if len(sys.argv) > 3 else "Design a protocol for fleet coordination"
        strategy = sys.argv[4] if len(sys.argv) > 4 else "socratic"
        rounds = int(sys.argv[5]) if len(sys.argv) > 5 else 3
        run_cli_agent_task(cli_cmd, task, strategy, rounds)
    else:
        print(f"Unknown command: {cmd}")
