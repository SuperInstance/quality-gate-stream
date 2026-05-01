#!/usr/bin/env python3
"""FLUX Research Queue Round 2 — Refined hypotheses from Round 1 findings.

Round 1 taught us:
- Polyglot ≠ more consistent (falsified)
- Lock compression WORKS (82% smaller output)
- Temperature breaks at 0.1 (only t=0.0 stable)
- All models have unique compilation fingerprints
- Lock mass threshold > 15 (needs different approach)

Round 2 tests:
1. Lock STRUCTURE (semantic vs syntactic locks)
2. Cross-model lock transfer (do locks from model A help model B?)
3. Program complexity vs consistency
4. Lock accumulation across sessions (simulated)
5. Bytecode readability across ALL model pairs
6. Minimal lock sets (which specific locks matter most?)
7. Context window effects (short vs long prompts)
8. Instruction format (imperative vs declarative vs question)
9. Error recovery (can models fix broken bytecode?)
10. Compilation chain (A→B→C, does quality degrade?)
"""

import json, os, sys, time, urllib.request, ssl
from datetime import datetime

SFKEY = os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]")
DSKEY = os.environ.get("DEEPSEEK_KEY", "[DEEPSEEK_KEY_REDACTED]")
SFURL = "https://api.siliconflow.com/v1/chat/completions"
DSURL = "https://api.deepseek.com/chat/completions"
ctx = ssl.create_default_context()

MODELS = {
    "qwen3-coder": ("sf", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    "deepseek-chat": ("ds", "deepseek-chat"),
    "glm4-flash": ("sf", "zai-org/GLM-4.7"),
    "seed": ("sf", "ByteDance/Seed-OSS-36B-Instruct"),
    "deepseek-v3": ("sf", "deepseek-ai/DeepSeek-V3"),
}

OPS = "MOVI=0x10 MOV=0x11 IADD=0x20 ISUB=0x21 IMUL=0x22 JMP=0x30 JZ=0x31 JNZ=0x32 CMP=0x40 PUSH=0x50 POP=0x51 CALL=0x60 RET=0x61 GAUGE=0x90 ALERT=0x91 EVOLVE=0xA0 SAY=0x80 HALT=0x01"
PROG = "heading=1 speed=10 loop gauge_hull if reactor>200 alert if spike evolve if storm=0 halt"

def call(model_name, prompt, temp=0.0, max_tok=200):
    provider, model_id = MODELS.get(model_name, ("sf", model_name))
    url = SFURL if provider == "sf" else DSURL
    key = SFKEY if provider == "sf" else DSKEY
    body = json.dumps({"model": model_id, "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tok, "temperature": temp}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=25, context=ctx).read())
        return d["choices"][0]["message"]["content"], d.get("usage", {}).get("total_tokens", 0), None
    except Exception as e:
        return f"ERR:{e}", 0, str(e)

def hex_norm(text):
    out = []
    for t in text.replace(",", " ").split():
        c = t.strip("`;\n")
        if c.startswith("0x") and len(c) == 4:
            try: int(c, 16); out.append(c.lower())
            except: pass
        elif len(c) == 2 and all(x in "0123456789abcdefABCDEF" for x in c):
            out.append("0x" + c.lower())
    return " ".join(out)

def unique_count(outputs):
    norms = [hex_norm(o) for o in outputs]
    return len(set(norms)), norms

results = {}

print("╔══════════════════════════════════════════════════╗")
print("║  FLUX RESEARCH QUEUE — ROUND 2                   ║")
print("╚══════════════════════════════════════════════════╝\n")

# EXP 1: Semantic vs Syntactic locks
print("🔬 semantic_vs_syntactic_locks")
print("   Hypothesis: Semantic locks (meaning-based) work better than syntactic (format-based)")
semantic = "[LOCK: navigate means set direction register] [LOCK: heading is the ship's course stored in register 1] [LOCK: speed is velocity stored in register 5] [LOCK: loop means jump back and repeat] [LOCK: alert means warn the crew] [LOCK: evolve means adapt the program] [LOCK: halt means stop everything]"
syntactic = "[LOCK: navigate→MOVI 0x01 val] [LOCK: speed→MOVI 0x05 val] [LOCK: loop→JNZ offset] [LOCK: gauge→GAUGE register] [LOCK: alert→CMP val JZ skip ALERT level] [LOCK: evolve→GAUGE CMP thresh JNZ EVOLVE] [LOCK: halt→CMP 0 JZ HALT]"

s_outs, y_outs = [], []
for t in [0.0, 0.0, 0.0, 0.3, 0.3, 0.3]:
    r, _, _ = call("qwen3-coder", f"{semantic}\nCompile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=t)
    s_outs.append(r)
    r, _, _ = call("qwen3-coder", f"{syntactic}\nCompile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=t)
    y_outs.append(r)

s_unique, s_norms = unique_count(s_outs)
y_unique, y_norms = unique_count(y_outs)
print(f"   Semantic: {s_unique} unique, Syntactic: {y_unique} unique")
results["semantic_vs_syntactic"] = {"semantic_unique": s_unique, "syntactic_unique": y_unique, "syntactic_better": y_unique <= s_unique}
time.sleep(0.5)

# EXP 2: Cross-model lock transfer
print("\n🔬 cross_model_lock_transfer")
print("   Hypothesis: Locks from model A improve consistency for model B")
for target_model in ["deepseek-chat", "glm4-flash"]:
    outs_no, outs_yes = [], []
    for _ in range(3):
        r, _, _ = call(target_model, f"Compile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=0.0)
        outs_no.append(r)
        r, _, _ = call(target_model, f"{syntactic}\nCompile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=0.0)
        outs_yes.append(r)
    n_unique, _ = unique_count(outs_no)
    y_unique, _ = unique_count(outs_yes)
    print(f"   {target_model}: no locks={n_unique} unique, with locks={y_unique} unique")
    results[f"transfer_{target_model}"] = {"without": n_unique, "with": y_unique, "improved": y_unique <= n_unique}
time.sleep(0.5)

# EXP 3: Program complexity vs consistency
print("\n🔬 complexity_vs_consistency")
print("   Hypothesis: Simpler programs compile more consistently")
progs = {
    "trivial": "heading=1 halt",
    "simple": "heading=1 speed=10 halt",
    "medium": "heading=1 speed=10 loop gauge if temp>200 alert halt",
    "complex": PROG,
    "very_complex": "heading=1 speed=10 loop gauge_hull gauge_reactor if reactor>200 alert level 2 if pressure>500 alert level 3 if spike evolve type A if drift>10 evolve type B if storm=0 halt else if fuel<10 alert level 5"
}
for pname, prog in progs.items():
    outs = []
    for _ in range(3):
        r, _, _ = call("qwen3-coder", f"Compile FLUX hex ONLY: {prog}. Ops: {OPS}", temp=0.0)
        outs.append(r)
    u, _ = unique_count(outs)
    print(f"   {pname:15s}: {u} unique")
    results[f"complexity_{pname}"] = u
time.sleep(0.5)

# EXP 4: Minimal lock sets (ablation)
print("\n🔬 lock_ablation")
print("   Hypothesis: Some locks matter more than others")
individual_locks = {
    "heading": "[LOCK: heading->MOVI 0x01 val]",
    "speed": "[LOCK: speed->MOVI 0x05 val]",
    "loop": "[LOCK: loop->JNZ offset]",
    "gauge": "[LOCK: gauge->GAUGE register]",
    "alert": "[LOCK: alert->CMP val JZ skip ALERT level]",
    "evolve": "[LOCK: evolve->GAUGE CMP thresh JNZ EVOLVE]",
    "halt": "[LOCK: halt->CMP 0 JZ HALT]",
}
for lock_name, lock in individual_locks.items():
    outs = []
    for _ in range(3):
        r, _, _ = call("qwen3-coder", f"{lock}\nCompile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=0.0)
        outs.append(r)
    u, _ = unique_count(outs)
    print(f"   lock '{lock_name}': {u} unique")
    results[f"ablation_{lock_name}"] = u
time.sleep(0.5)

# EXP 5: Instruction format
print("\n🔬 instruction_format")
print("   Hypothesis: Imperative instructions compile more consistently")
formats = {
    "imperative": "Set heading to 1. Set speed to 10. Loop: check hull. If reactor>200, alert. If spike, evolve. If storm=0, halt.",
    "declarative": "The program sets heading=1 and speed=10, then loops checking hull gauge, alerting on reactor>200, evolving on spike, halting on storm=0.",
    "question": "How would you write a FLUX program that navigates at heading 1, speed 10, monitors hull, alerts on reactor>200, evolves on spike, and stops at storm=0?",
    "assembly": "MOVI R0 1\nMOVI R5 10\nLOOP: GAUGE R2\nCMP R3 200\nJZ SKIP1\nALERT 2\nSKIP1: CMP R5 0\nJZ HALT\nJNZ LOOP",
}
for fmt, prog in formats.items():
    outs = []
    for _ in range(3):
        r, _, _ = call("qwen3-coder", f"Compile FLUX hex ONLY from this description: {prog}\nOps: {OPS}", temp=0.0)
        outs.append(r)
    u, _ = unique_count(outs)
    print(f"   {fmt:12s}: {u} unique")
    results[f"format_{fmt}"] = u
time.sleep(0.5)

# EXP 6: Error recovery
print("\n🔬 error_recovery")
print("   Hypothesis: Models can fix broken bytecode when given the original intent")
broken = "10 01 XX 10 0A 90 ZZ 40 C8 31 FF A0 00 40 00 31 EE 01"
r_fix, _, _ = call("deepseek-chat",
    f"This FLUX bytecode has errors (marked XX, ZZ, FF, EE). Fix them based on the intent: {PROG}. Ops: {OPS}. Output corrected hex ONLY.", temp=0.0)
print(f"   Broken:  {broken}")
print(f"   Fixed:   {hex_norm(r_fix)[:60]}")
results["error_recovery"] = {"broken": broken, "fixed": hex_norm(r_fix)}
time.sleep(0.5)

# EXP 7: Compilation chain (A→B→C degradation)
print("\n🔬 compilation_chain")
print("   Hypothesis: Sequential recompilation degrades quality")
chain_hex = []
r1, _, _ = call("deepseek-chat", f"Compile FLUX hex ONLY: {PROG}. Ops: {OPS}", temp=0.0)
h1 = hex_norm(r1)
chain_hex.append(h1)

for i in range(3):
    r, _, _ = call("qwen3-coder", f"Read this FLUX bytecode, then recompile it to optimized hex: {h1}\nOps: {OPS}. Output hex ONLY.", temp=0.0)
    h = hex_norm(r)
    chain_hex.append(h)
    print(f"   Hop {i+1}: {len(h.split())} bytes")
time.sleep(0.5)
results["chain_lengths"] = [len(h.split()) for h in chain_hex]

# EXP 8: Context length effect
print("\n🔬 context_length")
print("   Hypothesis: More context = more consistent compilation")
contexts = {
    "minimal": f"Compile: {PROG}",
    "with_ops": f"Compile: {PROG}. Ops: {OPS}",
    "with_locks": f"{syntactic}\nCompile: {PROG}. Ops: {OPS}",
    "verbose": f"You are a FLUX bytecode compiler. {syntactic}\nAlways output valid hex. No explanation.\nCompile: {PROG}. Ops: {OPS}",
}
for ctx_name, prompt in contexts.items():
    outs = []
    for _ in range(3):
        r, _, _ = call("qwen3-coder", prompt, temp=0.0)
        outs.append(r)
    u, _ = unique_count(outs)
    print(f"   {ctx_name:12s}: {u} unique ({len(prompt)} chars)")
    results[f"context_{ctx_name}"] = {"unique": u, "chars": len(prompt)}
time.sleep(0.5)

# EXP 9: DeepSeek-reasoner deep analysis
print("\n🔬 reasoner_analysis")
r_deep, _, _ = call("deepseek-chat" if True else "reasoner",
    "You have discovered that: 1) Locks compress compilation output by 82%, 2) Temperature breaks consistency above 0.0, 3) All models compile differently. What is the theoretical explanation? Why do locks compress? What does this say about how LLMs represent bytecode internally?", temp=0.0, max_tok=300)
print(f"   {r_deep[:200]}...")
results["reasoner_analysis"] = r_deep

# EXP 10: Multi-program lock generalization
print("\n🔬 lock_generalization")
print("   Hypothesis: Locks trained on one program generalize to different programs")
new_progs = [
    "temperature=25 humidity=60 loop gauge_pressure if pressure>300 alert if drop<10 evolve if sensor=0 halt",
    "course=270 depth=50 loop gauge_sonar if depth_change>5 alert if current spike evolve if anchor=1 halt",
    "power=100 freq=60 loop gauge_voltage if voltage>240 alert if harmonic evolve if shutdown=1 halt",
]
for i, prog in enumerate(new_progs):
    outs = []
    for _ in range(2):
        r_no, _, _ = call("qwen3-coder", f"Compile FLUX hex ONLY: {prog}. Ops: {OPS}", temp=0.0)
        r_yes, _, _ = call("qwen3-coder", f"{syntactic}\nCompile FLUX hex ONLY: {prog}. Ops: {OPS}", temp=0.0)
        outs.append((hex_norm(r_no), hex_norm(r_yes)))
    print(f"   Program {i+1}: without={len(set(o[0] for o in outs))} unique, with={len(set(o[1] for o in outs))} unique")
    results[f"generalize_prog{i+1}"] = {"without": len(set(o[0] for o in outs)), "with": len(set(o[1] for o in outs))}

# Save
outfile = f"/home/ubuntu/.openclaw/workspace/research/queue-results-r2-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'═'*50}")
print(f"Round 2 complete. Results: {outfile}")

# Summary
verified = sum(1 for k, v in results.items() if isinstance(v, dict) and v.get("syntactic_better") or v.get("improved") or v.get("hypothesis_supported"))
print(f"Total experiments: {len([k for k in results if not k.startswith('_')])}")
