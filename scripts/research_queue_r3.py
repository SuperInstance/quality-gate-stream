#!/usr/bin/env python3
"""FLUX Research Queue Round 3 — Deep dive on compression, fingerprints, and edge cases"""
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
print("║  FLUX RESEARCH QUEUE — ROUND 3 (Deep Dive)      ║")
print("╚══════════════════════════════════════════════════╝\n")

# EXP 1: Fingerprint collision — do two models ever produce identical output?
print("🔬 fingerprint_collision (10 programs, 3 models)")
collision_count = 0
all_fingerprints = {}
progs = [
    "heading=1 speed=10 loop gauge_hull if reactor>200 alert if spike evolve if storm=0 halt",
    "set depth=50 course=180 loop gauge_sonar if obstacle<5 alert if current_spike evolve if surface halt",
    "power=100 voltage=240 loop gauge_grid if surge>300 alert if freq_drift evolve if blackout halt",
    "x=0 y=0 loop gauge_distance if dist<10 alert if speed_spike evolve if home halt",
    "temp=72 humidity=45 loop gauge_sensor if temp>100 alert if humidity_spike evolve if sensor_fail halt",
    "fuel=100 speed=25 loop gauge_engine if temp>220 alert if knock evolve if empty halt",
    "score=0 level=1 loop gauge_progress if score>100 evolve if health<1 halt",
    "pitch=440 vol=80 loop gauge_freq if distortion alert if harmonic evolve if silence halt",
    "lat=47 lon=-122 loop gauge_gps if drift>10 alert if multipath evolve if home halt",
    "cpu=50 mem=80 loop gauge_load if cpu>90 alert if spike evolve if shutdown halt",
]
for prog in progs:
    fps = {}
    for model_name, model_id in [("qwen", "Qwen/Qwen3-Coder-30B-A3B-Instruct"), ("ds", "deepseek-chat"), ("glm", "zai-org/GLM-4.7")]:
        r, _ = call(model_id, f"{LOCKS}\nCompile FLUX hex ONLY: {prog}. Ops: {OPS}")
        fp = hex_norm(r)
        fps[model_name] = fp
        if fp not in all_fingerprints:
            all_fingerprints[fp] = []
        all_fingerprints[fp].append(model_name)
    
    # Check for collisions
    vals = list(fps.values())
    if len(set(vals)) < len(vals):
        collision_count += 1
    time.sleep(0.2)

print(f"   Collisions (same hex from different models): {collision_count}/10")
print(f"   Unique fingerprints total: {len(all_fingerprints)}")
results["fingerprints"] = {"collisions": collision_count, "unique": len(all_fingerprints)}

# EXP 2: Token-level analysis — what does each model spend tokens on?
print("\n🔬 token_analysis (3 models, with/without locks)")
for model_name, model_id in [("qwen", "Qwen/Qwen3-Coder-30B-A3B-Instruct"), ("ds", "deepseek-chat"), ("glm", "zai-org/GLM-4.7")]:
    r_no, t_no = call(model_id, f"Compile FLUX hex ONLY: {progs[0]}. Ops: {OPS}")
    r_yes, t_yes = call(model_id, f"{LOCKS}\nCompile FLUX hex ONLY: {progs[0]}. Ops: {OPS}")
    savings = round((1 - t_yes / max(t_no, 1)) * 100, 1) if t_no > 0 else 0
    print(f"   {model_name}: no locks={t_no}tok, with locks={t_yes}tok ({savings}% savings)")
    results[f"tokens_{model_name}"] = {"without": t_no, "with": t_yes, "savings_pct": savings}
    time.sleep(0.2)

# EXP 3: Lock ordering — does the ORDER of locks matter?
print("\n🔬 lock_ordering")
locks_list = LOCKS.split("]")
import random
random.shuffle(locks_list)
shuffled = " ".join(locks_list).replace("  ", " ")

outs_original, outs_shuffled = [], []
for _ in range(3):
    r1, _ = call("Qwen/Qwen3-Coder-30B-A3B-Instruct", f"{LOCKS}\nCompile FLUX hex ONLY: {progs[0]}. Ops: {OPS}")
    r2, _ = call("Qwen/Qwen3-Coder-30B-A3B-Instruct", f"{shuffled}\nCompile FLUX hex ONLY: {progs[0]}. Ops: {OPS}")
    outs_original.append(hex_norm(r1))
    outs_shuffled.append(hex_norm(r2))

u_orig = len(set(outs_original))
u_shuf = len(set(outs_shuffled))
same_order = set(outs_original) == set(outs_shuffled)
print(f"   Original order: {u_orig} unique, Shuffled: {u_shuf} unique, Same: {same_order}")
results["lock_ordering"] = {"original_unique": u_orig, "shuffled_unique": u_shuf, "order_matters": not same_order}

# EXP 4: Noise resistance — can models compile from noisy input?
print("\n🔬 noise_resistance")
clean = "heading=1 speed=10 loop gauge_hull if reactor>200 alert if spike evolve if storm=0 halt"
noisy_versions = {
    "typos": "heading=1 spedd=10 lop gauge_hul if reactor>200 alrt if spiike evolv if sorm=0 hlt",
    "extra_words": "please set the heading to value 1 and speed to 10 then start a loop checking the hull gauge and if reactor exceeds 200 alert the crew and if spike detected evolve the program and if storm equals 0 then halt everything",
    "code_mixed": "heading=1; // set heading\nspeed=10; // knots\nwhile(true) { gauge(hull); if(reactor>200) alert(); if(spike) evolve(); if(storm==0) break; }",
    "fragmented": "heading...1 | speed..10 || LOOP_START: gauge...hull || IF reactor>200 => alert || IF spike => evolve || IF storm=0 => halt || GOTO LOOP_START",
}
for noise_type, noisy in noisy_versions.items():
    r, t = call("deepseek-chat", f"Compile FLUX hex ONLY: {noisy}. Ops: {OPS}")
    r_clean, _ = call("deepseek-chat", f"Compile FLUX hex ONLY: {clean}. Ops: {OPS}")
    same = hex_norm(r) == hex_norm(r_clean)
    print(f"   {noise_type:15s}: {'✅ same as clean' if same else '❌ differs'} ({t}tok)")
    results[f"noise_{noise_type}"] = {"same_as_clean": same, "tokens": t}
    time.sleep(0.2)

# EXP 5: Zero-shot vs few-shot compilation
print("\n🔬 zero_vs_few_shot")
few_shot = """Example compilation:
heading=1 speed=5 halt → 10 01 01 10 05 05 01

Example compilation:
heading=3 speed=20 loop gauge if temp>100 alert halt → 10 01 03 10 05 14 90 00 40 00 64 31 06 91 01 30 00

Now compile this: heading=1 speed=10 loop gauge_hull if reactor>200 alert if spike evolve if storm=0 halt
Output hex ONLY."""

for _ in range(3):
    r_zero, _ = call("deepseek-chat", f"Compile FLUX hex ONLY: {progs[0]}. Ops: {OPS}")
    r_few, _ = call("deepseek-chat", few_shot)
    z = hex_norm(r_zero)
    f = hex_norm(r_few)
    print(f"   Zero: {z[:40]}...")
    print(f"   Few:  {f[:40]}...")

results["few_shot"] = {"zero_shot": hex_norm(r_zero), "few_shot": hex_norm(r_few)}

# Save
outfile = f"/home/ubuntu/.openclaw/workspace/research/queue-results-r3-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'═'*50}")
print(f"Round 3 complete. Results: {outfile}")
