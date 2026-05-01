#!/usr/bin/env python3
"""Abstraction Plane Analyzer — determines optimal decomposition depth for a given component.

Uses cheap models to evaluate where on the 6-plane stack a component should live.
Stops when further decomposition has diminishing returns.

Planes:
  5 = Intent (natural language)
  4 = Domain Language (FLUX-ese, maritime vocab)
  3 = Structured IR (JSON AST, lock-annotated)
  2 = Interpreted Bytecode (FLUX opcodes)
  1 = Compiled Native (C/Rust/Zig)
  0 = Bare Metal (assembly, GPU kernels)

Usage:
  python3 plane_analyzer.py "navigate east 10 knots, monitor reactor, alert if overheating"
  python3 plane_analyzer.py --target esp32 "sensor reader for temperature"
  python3 plane_analyzer.py --target cloud "fleet coordination protocol"
"""

import json
import os
import sys
import time
import urllib.request
import ssl
from datetime import datetime

SFKEY = os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]")
DSKEY = os.environ.get("DEEPSEEK_KEY", "[DEEPSEEK_KEY_REDACTED]")
ctx = ssl.create_default_context()

PLANES = {
    5: "Intent (natural language)",
    4: "Domain Language (FLUX-ese, maritime, etc.)",
    3: "Structured IR (JSON AST, lock-annotated)",
    2: "Interpreted Bytecode (FLUX opcodes in hex)",
    1: "Compiled Native (C/Rust/Zig source code)",
    0: "Bare Metal (assembly, machine code, firmware)",
}

def call_deepseek(prompt, temp=0.0, max_tok=300):
    body = json.dumps({"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tok, "temperature": temp}).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
        headers={"Authorization": f"Bearer {DSKEY}", "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=30, context=ctx).read())
    return d["choices"][0]["message"]["content"], d["usage"]["total_tokens"]

def call_qwen(prompt, temp=0.0, max_tok=300):
    body = json.dumps({"model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tok, "temperature": temp}).encode()
    req = urllib.request.Request("https://api.siliconflow.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {SFKEY}", "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=25, context=ctx).read())
    return d["choices"][0]["message"]["content"], d["usage"]["total_tokens"]

def decompose(intent, from_plane, to_plane):
    """Decompose intent from one plane to the next lower plane."""
    prompts = {
        (5, 4): f"Convert this natural language intent into FLUX-ese domain language (structured maritime-style notation): {intent}",
        (4, 3): f"Convert this FLUX-ese domain language into structured JSON AST with types and lock annotations: {intent}",
        (3, 2): f"Convert this structured IR to FLUX bytecode hex. Ops: MOVI=0x10 MOV=0x11 IADD=0x20 ISUB=0x21 IMUL=0x22 JMP=0x30 JZ=0x31 JNZ=0x32 CMP=0x40 GAUGE=0x90 ALERT=0x91 EVOLVE=0xA0 SAY=0x80 HALT=0x01. Output hex ONLY: {intent}",
        (2, 1): f"Write a C or Zig function that executes this FLUX bytecode program. The function should take input registers and produce output: {intent}",
        (1, 0): f"Optimize this C code for bare metal execution on an embedded system with 4KB RAM. Use register allocation and minimize stack usage: {intent}",
    }
    
    prompt = prompts.get((from_plane, to_plane), f"Decompose to plane {to_plane}: {intent}")
    
    # Use deepseek-chat for compilation tasks, qwen for analysis
    if to_plane <= 2:
        return call_deepseek(prompt)
    else:
        return call_qwen(prompt)

def evaluate_quality(original, decomposed, plane):
    """Evaluate if decomposition to this plane added value."""
    prompt = f"""Rate this decomposition on a 1-10 scale for each criterion:
- Correctness: Does it preserve the original meaning?
- Compactness: Is it more compact than the original?
- Executability: Can it be directly executed/interpreted?
- Maintainability: Can a human or agent understand and modify it?

Original (Plane 5 intent): {original}
Decomposed (Plane {plane}): {decomposed[:500]}

Output ONLY a JSON object: {{"correctness": N, "compactness": N, "executability": N, "maintainability": N}}"""

    r, _ = call_deepseek(prompt, max_tok=150)
    try:
        # Extract JSON from response
        start = r.find("{")
        end = r.rfind("}") + 1
        scores = json.loads(r[start:end])
        scores["total"] = sum(scores.values()) / len(scores)
        return scores
    except:
        return {"correctness": 5, "compactness": 5, "executability": 5, "maintainability": 5, "total": 5}

def find_optimal_plane(intent, target="auto"):
    """Find the optimal abstraction plane for a given intent."""
    print(f"\n{'═'*60}")
    print(f"  ABSTRACTION PLANE ANALYZER")
    print(f"{'═'*60}")
    print(f"  Intent: {intent[:80]}...")
    print(f"  Target: {target}")
    print()
    
    # Target-based floor (won't go above this)
    target_floors = {"esp32": 0, "jetson": 1, "cloud": 3, "mud": 2, "agent": 3, "auto": 5}
    floor = target_floors.get(target, 5)
    
    current = intent
    plane_scores = {}
    prev_total = 0
    
    for plane in range(5, max(floor - 1, -1), -1):
        print(f"  Plane {plane}: {PLANES[plane]}")
        
        if plane < 5:
            current, tokens = decompose(current, plane + 1, plane)
            print(f"    Decomposed ({tokens} tokens): {current[:80]}...")
        else:
            print(f"    Original: {current[:80]}...")
        
        # Evaluate quality
        scores = evaluate_quality(intent, current, plane)
        plane_scores[plane] = scores
        
        print(f"    Quality: {scores['total']:.1f}/10 (corr={scores['correctness']} comp={scores['compactness']} exec={scores['executability']} maint={scores['maintainability']})")
        
        # Check for diminishing returns
        if plane < 5:
            improvement = scores["total"] - prev_total
            print(f"    Improvement: {'+' if improvement > 0 else ''}{improvement:.1f}")
            
            if improvement < -1.0:
                print(f"    ⚠️ Diminishing returns detected! Stopping at Plane {plane + 1}")
                optimal = plane + 1
                break
            elif improvement < 0.5 and plane <= floor:
                print(f"    ✅ Marginal returns. Optimal plane: {plane}")
                optimal = plane
                break
        
        prev_total = scores["total"]
        time.sleep(0.3)
    else:
        optimal = floor
    
    print(f"\n  ═══ RESULT ═══")
    print(f"  Optimal plane: {optimal} ({PLANES[optimal]})")
    print(f"  Decomposition stops: {'diminishing returns' if optimal > floor else 'target floor reached'}")
    
    return {"optimal_plane": optimal, "scores": plane_scores, "target": target}

if __name__ == "__main__":
    target = "auto"
    intent_parts = []
    
    for arg in sys.argv[1:]:
        if arg.startswith("--target="):
            target = arg.split("=")[1]
        elif arg == "--target":
            target = sys.argv[sys.argv.index(arg) + 1]
        else:
            intent_parts.append(arg)
    
    if not intent_parts:
        print("Usage: python3 plane_analyzer.py [--target esp32|jetson|cloud|mud|agent|auto] \"intent description\"")
        sys.exit(1)
    
    intent = " ".join(intent_parts)
    result = find_optimal_plane(intent, target=target)
    
    # Save result
    outfile = f"/home/ubuntu/.openclaw/workspace/research/plane-analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Saved: {outfile}")
