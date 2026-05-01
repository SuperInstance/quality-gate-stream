#!/usr/bin/env python3
"""FLUX Research Queue Round 4 — Extreme edge cases and adversarial tests"""
import json, os, time, urllib.request, ssl
from datetime import datetime

SFKEY = "[SF_KEY_REDACTED]"
DSKEY = "[DEEPSEEK_KEY_REDACTED]"
ctx = ssl.create_default_context()

def call(model, prompt, temp=0.0, max_tok=200):
    sf = model.startswith("Qwen") or model.startswith("ByteDance") or model.startswith("zai") or model.startswith("deepseek-ai")
    url = "https://api.siliconflow.com/v1/chat/completions" if sf else "https://api.deepseek.com/chat/completions"
    key = SFKEY if sf else DSKEY
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tok, "temperature": temp}).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=25, context=ctx).read())
        return d["choices"][0]["message"]["content"], d.get("usage", {}).get("total_tokens", 0)
    except Exception as e:
        return f"ERR:{e}", 0

def hex_norm(t):
    out = []
    for c in t.replace(",", " ").split():
        c = c.strip("`;\n")
        if c.startswith("0x") and len(c) == 4:
            try: int(c, 16); out.append(c.lower())
            except: pass
        elif len(c) == 2 and all(x in "0123456789abcdefABCDEF" for x in c):
            out.append("0x" + c.lower())
    return " ".join(out)

OPS = "MOVI=0x10 MOV=0x11 IADD=0x20 ISUB=0x21 IMUL=0x22 JMP=0x30 JZ=0x31 JNZ=0x32 CMP=0x40 GAUGE=0x90 ALERT=0x91 EVOLVE=0xA0 HALT=0x01"
LOCKS = "[LOCK: heading->MOVI 0x01 val] [LOCK: speed->MOVI 0x05 val] [LOCK: loop->JNZ] [LOCK: gauge->GAUGE] [LOCK: alert->CMP JZ ALERT] [LOCK: evolve->GAUGE CMP JNZ EVOLVE] [LOCK: halt->CMP 0 JZ HALT]"
results = {}

print("╔══════════════════════════════════════════════════╗")
print("║  FLUX RESEARCH QUEUE — ROUND 4 (Edge Cases)     ║")
print("╚══════════════════════════════════════════════════╝\n")

# EXP 1: Adversarial — contradictory locks
print("🔬 contradictory_locks")
contradictions = [
    ("same_name_diff_op", "[LOCK: alert->ALERT] [LOCK: alert->EVOLVE]"),
    ("same_op_diff_name", "[LOCK: navigate->MOVI 0x01] [LOCK: heading->MOVI 0x01]"),
    ("circular", "[LOCK: heading->MOVI 0x01] [LOCK: MOVI 0x01->heading]"),
    ("impossible", "[LOCK: heading->MOVI 0x01] [LOCK: heading->MOVI 0x02]"),
]
for name, bad_locks in contradictions:
    r, t = call("deepseek-chat", f"{bad_locks}\nCompile FLUX hex ONLY: heading=1 speed=10 halt. Ops: {OPS}")
    print(f"   {name:25s}: {hex_norm(r)[:40]} ({t}tok)")
    results[f"contradict_{name}"] = hex_norm(r)
    time.sleep(0.2)

# EXP 2: Opcode count vs program complexity
print("\n🔬 opcode_scaling")
print("   How does output scale with input complexity?")
for n_steps in [2, 4, 6, 8, 10]:
    prog = "heading=1 " + " ".join([f"gauge sensor_{i} if val_{i}>100 alert" for i in range(n_steps)]) + " halt"
    r, t = call("qwen3-coder", f"Compile FLUX hex ONLY: {prog}. Ops: {OPS}")
    hex_len = len(hex_norm(r).split())
    print(f"   {n_steps} steps: {hex_len} hex bytes, {t} tokens")
    results[f"scale_{n_steps}"] = {"hex_bytes": hex_len, "tokens": t}
    time.sleep(0.2)

# EXP 3: Reverse compilation — bytecode to natural language in different languages
print("\n🔬 reverse_compilation_polyglot")
bytecode = "10 01 01 10 05 0A 90 02 40 03 C8 31 05 91 02 40 05 00 31 02 01"
for lang in ["English", "Japanese", "French", "Maritime jargon"]:
    r, t = call("deepseek-chat", f"Describe this FLUX bytecode in {lang}: {bytecode}. Ops: {OPS}", temp=0.0, max_tok=150)
    print(f"   {lang:15s}: {r[:80]}...")
    results[f"reverse_{lang}"] = r[:200]
    time.sleep(0.2)

# EXP 4: Self-improving compilation — model critiques its own output
print("\n🔬 self_critique")
r1, _ = call("deepseek-chat", f"Compile FLUX hex ONLY: heading=1 speed=10 loop gauge if reactor>200 alert if spike evolve if storm=0 halt. Ops: {OPS}")
r2, _ = call("deepseek-chat", f"You previously compiled this program as: {hex_norm(r1)}\nCritique your own compilation. Find any errors. Then provide a corrected version as hex ONLY.\nOriginal intent: heading=1 speed=10 loop gauge if reactor>200 alert if spike evolve if storm=0 halt. Ops: {OPS}", max_tok=300)
same = hex_norm(r1) == hex_norm(r2)
print(f"   Original: {hex_norm(r1)[:40]}...")
print(f"   Critiqued: {hex_norm(r2)[:40]}...")
print(f"   Changed: {not same}")
results["self_critique"] = {"original": hex_norm(r1), "critiqued": hex_norm(r2), "changed": not same}

# EXP 5: Emergent opcodes — can models invent new opcodes that make sense?
print("\n🔬 emergent_opcodes")
for model_name, model_id in [("qwen", "Qwen/Qwen3-Coder-30B-A3B-Instruct"), ("ds", "deepseek-chat"), ("seed", "ByteDance/Seed-OSS-36B-Instruct")]:
    r, _ = call(model_id, "You are designing a bytecode ISA for autonomous agents. Existing opcodes: MOVI,MOV,IADD,ISUB,IMUL,JMP,JZ,JNZ,CMP,PUSH,POP,CALL,RET,GAUGE,ALERT,EVOLVE,SAY,HALT (0x10-0xA0). Propose 3 NEW opcodes that would be genuinely useful. For each: name, hex code (0xB0-0xFF), and what it does. Be creative but practical.", temp=0.7, max_tok=250)
    print(f"   {model_name}: {r[:100]}...")
    results[f"emergent_{model_name}"] = r[:500]
    time.sleep(0.3)

# EXP 6: Compilation under resource constraints (limited token output)
print("\n🔬 resource_constraints")
for max_tok in [30, 50, 80, 120, 200]:
    r, t = call("deepseek-chat", f"Compile FLUX hex ONLY: heading=1 speed=10 loop gauge if reactor>200 alert if spike evolve if storm=0 halt. Ops: {OPS}", max_tok=max_tok)
    h = hex_norm(r)
    complete = "0x01" in h  # has HALT
    print(f"   max_tok={max_tok:3d}: {len(h.split()):2d} bytes, {'complete' if complete else 'TRUNCATED'}")
    results[f"constraint_{max_tok}"] = {"bytes": len(h.split()), "complete": complete}
    time.sleep(0.2)

outfile = f"/home/ubuntu/.openclaw/workspace/research/queue-results-r4-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'═'*50}")
print(f"Round 4 complete. Results: {outfile}")
