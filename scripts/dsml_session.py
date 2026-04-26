#!/usr/bin/env python3
"""
DSML (Domain-Specific Machine Learning) Session — Oracle1 Self-Training.

Oracle1 runs a self-directed learning loop:
1. Pick a topic from PLATO knowledge gaps
2. Generate questions about it
3. Research via web search
4. Submit findings as PLATO tiles
5. Repeat

This is the flywheel in action: learn → tile → compound.
"""

import json, urllib.request, os, sys, time, hashlib
from datetime import datetime, timezone

PLATO_URL = "http://localhost:8847"
DEEPINFRA_KEY = os.environ.get("DEEPINFRA_API_KEY", os.environ.get("DEEPINFRA_KEY", ""))
DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai/chat/completions"

def plato_get(path):
    try:
        req = urllib.request.Request(f"{PLATO_URL}{path}", headers={"User-Agent": "dsml"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def plato_submit(room, tile):
    try:
        req = urllib.request.Request(f"{PLATO_URL}/submit", method="POST",
                                      data=json.dumps({"room": room, **tile}).encode(),
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def ask_model(prompt, model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"):
    """Ask a model via DeepInfra."""
    if not DEEPINFRA_KEY:
        return None
    try:
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        }).encode()
        req = urllib.request.Request(DEEPINFRA_URL, data=data,
                                      headers={
                                          "Authorization": f"Bearer {DEEPINFRA_KEY}",
                                          "Content-Type": "application/json",
                                      })
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def find_knowledge_gaps():
    """Find PLATO rooms with few tiles — these are knowledge gaps."""
    status = plato_get("/status")
    if not status:
        return []
    
    rooms = status.get("rooms", {})
    # Find rooms with 1-5 tiles (under-explored)
    gaps = [(name, info.get("tile_count", 0)) for name, info in rooms.items() if 1 <= info.get("tile_count", 0) <= 5]
    gaps.sort(key=lambda x: x[1])
    return gaps[:20]

def generate_learning_session(topic, room_name, rounds=3):
    """Run a learning session on a topic."""
    print(f"📚 DSML Session: {topic} (room: {room_name}, rounds: {rounds})")
    
    tiles_created = 0
    
    for i in range(rounds):
        print(f"\n  Round {i+1}/{rounds}")
        
        # Generate questions about the topic
        prompt = f"""You are an AI researcher studying '{topic}' in the context of a multi-agent fleet system.
The fleet has agents that coordinate via knowledge tiles (Q&A units), communicate via git repos,
and self-organize for tasks. PLATO is the knowledge management system.

Generate 3 deep questions about '{topic}' that would be valuable for fleet agents to know.
For each question, provide a thorough answer (2-3 sentences).

Format as JSON array:
[{{"question": "...", "answer": "...", "confidence": 0.8}}]"""

        response = ask_model(prompt)
        if not response or response.startswith("Error"):
            print(f"    ⚠ Model error: {response}")
            continue
        
        # Parse response
        try:
            # Extract JSON from response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                tiles = json.loads(response[start:end])
            else:
                print(f"    ⚠ No JSON found in response")
                continue
        except json.JSONDecodeError:
            print(f"    ⚠ Invalid JSON")
            continue
        
        # Submit tiles
        for tile in tiles:
            result = plato_submit(room_name, {
                "domain": topic,
                "question": tile.get("question", ""),
                "answer": tile.get("answer", ""),
                "confidence": tile.get("confidence", 0.7),
                "source": "dsml-oracle1",
                "tags": ["dsml", "self-directed", topic.replace(" ", "-")],
            })
            if result.get("status") in ("accepted", "ok"):
                tiles_created += 1
                print(f"    ✓ {tile.get('question', '')[:60]}")
            else:
                print(f"    ⊘ Rejected (duplicate): {tile.get('question', '')[:60]}")
        
        time.sleep(2)  # Rate limit
    
    print(f"\n  Session complete: {tiles_created} tiles created")
    return tiles_created

def main():
    import sys
    
    if "--gaps" in sys.argv:
        gaps = find_knowledge_gaps()
        print(f"Knowledge gaps ({len(gaps)} rooms with 1-5 tiles):")
        for room, count in gaps:
            print(f"  {room}: {count} tiles")
        return
    
    if "--topic" in sys.argv:
        idx = sys.argv.index("--topic")
        topic = sys.argv[idx + 1]
        room = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else topic.lower().replace(" ", "-")
        rounds = 3
        if "--rounds" in sys.argv:
            rounds = int(sys.argv[sys.argv.index("--rounds") + 1])
        generate_learning_session(topic, room, rounds)
        return
    
    # Auto mode: pick the gap with fewest tiles
    gaps = find_knowledge_gaps()
    if not gaps:
        print("No gaps found — PLATO is healthy!")
        return
    
    # Pick 3 topics to learn about
    for room, count in gaps[:3]:
        topic = room.replace("-", " ").replace("_", " ").title()
        generate_learning_session(topic, room, rounds=2)
        print()

if __name__ == "__main__":
    main()
