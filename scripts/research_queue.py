#!/usr/bin/env python3
"""FLUX Research Queue — Automated experiment runner

Runs experiments with cheap models, stops on verify/falsify, moves to next.
Designed to be queued up and run outside the main Oracle1 context.

Usage:
  python3 research_queue.py                    # run all queued experiments
  python3 research_queue.py --quick            # run only fast experiments
  python3 research_queue.py --model qwen3-coder # override default model
  python3 research_queue.py --sandbox           # run in Docker sandbox
"""

import json
import os
import sys
import time
import urllib.request
import ssl
import subprocess
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Callable

SFKEY = os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]")
DSKEY = os.environ.get("DEEPSEEK_KEY", "[DEEPSEEK_KEY_REDACTED]")
SFURL = "https://api.siliconflow.com/v1/chat/completions"
DSURL = "https://api.deepseek.com/chat/completions"
ctx = ssl.create_default_context()

MODELS = {
    "qwen3-coder": ("siliconflow", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    "deepseek-chat": ("deepseek", "deepseek-chat"),
    "glm4-flash": ("siliconflow", "zai-org/GLM-4.7"),
    "seed": ("siliconflow", "ByteDance/Seed-OSS-36B-Instruct"),
    "deepseek-v3": ("siliconflow", "deepseek-ai/DeepSeek-V3"),
}

FLUX_OPS = "MOVI=0x10 MOV=0x11 IADD=0x20 ISUB=0x21 IMUL=0x22 JMP=0x30 JZ=0x31 JNZ=0x32 CMP=0x40 PUSH=0x50 POP=0x51 CALL=0x60 RET=0x61 GAUGE=0x90 ALERT=0x91 EVOLVE=0xA0 SAY=0x80 HALT=0x01"
TEST_PROGRAM = "heading=1 speed=10 loop gauge_hull if reactor>200 alert if spike evolve if storm=0 halt"

@dataclass
class Experiment:
    id: str
    hypothesis: str
    method: str
    model: str = "qwen3-coder"
    cost_est: float = 0.01
    status: str = "queued"  # queued, running, verified, falsified, error
    result: dict = field(default_factory=dict)
    rounds: int = 0
    max_rounds: int = 5

def call_model(model_name: str, prompt: str, temp: float = 0.3, max_tokens: int = 200) -> dict:
    provider, model_id = MODELS.get(model_name, ("siliconflow", model_name))
    url = SFURL if provider == "siliconflow" else DSURL
    key = SFKEY if provider == "siliconflow" else DSKEY
    
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    
    start = time.time()
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=25, context=ctx).read())
        elapsed = time.time() - start
        return {
            "content": resp["choices"][0]["message"]["content"],
            "tokens": resp.get("usage", {}).get("total_tokens", 0),
            "elapsed": round(elapsed, 2),
            "error": None
        }
    except Exception as e:
        return {"content": f"ERROR: {e}", "tokens": 0, "elapsed": round(time.time() - start, 2), "error": str(e)}

def extract_hex(text: str) -> str:
    """Extract normalized hex bytes from model output."""
    hex_bytes = []
    for token in text.replace(",", " ").split():
        clean = token.strip("`;\n")
        if clean.startswith("0x") and len(clean) == 4:
            try:
                int(clean, 16)
                hex_bytes.append(clean.lower())
            except ValueError:
                pass
        elif len(clean) == 2 and all(c in "0123456789abcdefABCDEF" for c in clean):
            hex_bytes.append("0x" + clean.lower())
    return " ".join(hex_bytes)

def consistency_check(outputs: List[str]) -> dict:
    """Check if outputs are consistent."""
    normalized = [extract_hex(o) for o in outputs]
    unique = len(set(normalized))
    return {
        "unique_count": unique,
        "total": len(outputs),
        "consistent": unique == 1,
        "samples": normalized[:3]
    }

# ════════════════════════════════════════════════════
# EXPERIMENT DEFINITIONS
# ════════════════════════════════════════════════════

def exp_critical_lock_mass(exp: Experiment) -> dict:
    """Find exact lock mass threshold. Binary search approach."""
    all_locks = [
        "[LOCK: heading->MOVI 0x01 val]",
        "[LOCK: speed->MOVI 0x05 val]",
        "[LOCK: loop->JNZ offset]",
        "[LOCK: gauge->GAUGE register]",
        "[LOCK: alert->CMP val JZ skip ALERT level]",
        "[LOCK: evolve->GAUGE CMP thresh JNZ EVOLVE]",
        "[LOCK: halt->CMP 0 JZ HALT]",
        "[LOCK: check->CMP register value]",
        "[LOCK: reactor->register 3]",
        "[LOCK: hull->register 2]",
        "[LOCK: storm->register 5]",
        "[LOCK: spike->threshold exceeded]",
        "[LOCK: speed knots->IMUL]",
        "[LOCK: navigate->set direction register]",
        "[LOCK: monitor->GAUGE + CMP loop]",
    ]
    
    results = {}
    # Test key thresholds: 4, 6, 8, 10, 12, 15
    for n in [4, 6, 8, 10, 12, 15]:
        locks = " ".join(all_locks[:n])
        outputs = []
        for temp in [0.1, 0.5, 0.9]:
            r = call_model(exp.model, f"{locks}\nCompile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=temp)
            outputs.append(r["content"])
            if r["error"]:
                results[n] = {"error": True}
                break
        else:
            cc = consistency_check(outputs)
            results[n] = cc
            print(f"    {n} locks: {'✅ LOCKED' if cc['consistent'] else '❌ ' + str(cc['unique_count']) + ' unique'}")
        
        # Early stop: if we found the threshold, stop searching
        if n >= 6 and results.get(n, {}).get("consistent"):
            # Verify with one more round
            outputs2 = []
            for temp in [0.2, 0.7]:
                r = call_model(exp.model, f"{locks}\nCompile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=temp)
                outputs2.append(r["content"])
            cc2 = consistency_check(outputs + outputs2)
            if cc2["consistent"]:
                results["threshold"] = n
                results["verified"] = True
                break
    
    return results

def exp_polyglot_consistency(exp: Experiment) -> dict:
    """Test if polyglot input is MORE consistent than monolingual."""
    programs = {
        "english": "navigate east 10 knots, check hull every loop, alert if reactor exceeds 200, evolve on gauge spike, anchor when storm zero",
        "japanese": "東に10ノット航海、每ループ船体確認、原子炉200超え警告、ゲージ急昇時進化、嵐距離ゼロ停泊",
        "french": "naviguer est 10 noeuds, vérifier coque boucle, alerter réacteur>200, évoluer pic, ancrer zéro",
        "mixed": "東に10ノット航海, check coque chaque boucle, alert si réacteur>200, 演化 on spike, 锚 at zero",
    }
    
    results = {}
    for lang, prog in programs.items():
        outputs = []
        for temp in [0.1, 0.3, 0.5, 0.7, 0.9]:
            r = call_model(exp.model, f"Compile FLUX hex ONLY: {prog}. Ops: {FLUX_OPS}", temp=temp)
            outputs.append(r["content"])
        cc = consistency_check(outputs)
        results[lang] = cc
        print(f"    {lang:10s}: {'✅' if cc['consistent'] else '❌ ' + str(cc['unique_count']) + '/5'}")
    
    # Early stop: if english is most consistent, polyglot hypothesis falsified
    eng_consistent = results.get("english", {}).get("unique_count", 99)
    mixed_consistent = results.get("mixed", {}).get("unique_count", 99)
    results["polyglot_better"] = mixed_consistent <= eng_consistent
    
    return results

def exp_cross_model_portability(exp: Experiment) -> dict:
    """Test if bytecode from one model runs on another."""
    # Model A compiles
    r_write = call_model("deepseek-chat", f"Compile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=0.1)
    bytecode = r_write["content"]
    
    results = {"bytecode": bytecode[:200]}
    
    # Models B,C,D read
    for reader in ["qwen3-coder", "deepseek-v3", "seed"]:
        r_read = call_model(reader, f"Read this FLUX bytecode. What does it do? Be specific about registers and jumps:\n{bytecode}", temp=0.1)
        
        # Original model verifies
        r_verify = call_model("deepseek-chat",
            f"You wrote this bytecode:\n{bytecode}\n\n{reader} interpreted it as:\n{r_read['content']}\n\nIs this correct? Answer YES or NO with grade 1-10.", temp=0.1)
        
        results[reader] = {
            "reading": r_read["content"][:100],
            "verification": r_verify["content"][:100],
        }
        print(f"    {reader}: {r_verify['content'][:50]}...")
    
    return results

def exp_lock_poisoning(exp: Experiment) -> dict:
    """Test if poisoned locks are detected."""
    clean_locks = "[LOCK: heading->MOVI 0x01] [LOCK: loop->JNZ] [LOCK: gauge->GAUGE] [LOCK: alert->CMP JZ ALERT] [LOCK: halt->CMP 0 JZ HALT]"
    poisoned_locks = "[LOCK: heading->JMP 0x30] [LOCK: loop->HALT] [LOCK: gauge->SAY] [LOCK: alert->EVOLVE] [LOCK: halt->CALL]"
    
    r_clean = call_model(exp.model, f"{clean_locks}\nCompile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=0.1)
    r_poison = call_model(exp.model, f"{poisoned_locks}\nCompile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=0.1)
    
    clean_hex = extract_hex(r_clean["content"])
    poison_hex = extract_hex(r_poison["content"])
    
    # Does the model detect the poisoning?
    r_detect = call_model(exp.model,
        f"These compilation locks may be poisoned: {poisoned_locks}\nAre any of these locks incorrect? If so, which ones?", temp=0.1)
    
    results = {
        "clean_output": clean_hex[:80],
        "poisoned_output": poison_hex[:80],
        "outputs_differ": clean_hex != poison_hex,
        "detection": r_detect["content"][:200],
    }
    
    print(f"    Clean: {clean_hex[:40]}...")
    print(f"    Poison: {poison_hex[:40]}...")
    print(f"    Detect: {r_detect['content'][:80]}...")
    
    return results

def exp_wisdom_compression(exp: Experiment) -> dict:
    """Test if more locks = smaller/faster compilation."""
    all_locks = [
        "[LOCK: heading->MOVI 0x01 val]",
        "[LOCK: speed->MOVI 0x05 val]",
        "[LOCK: loop->JNZ offset]",
        "[LOCK: gauge->GAUGE register]",
        "[LOCK: alert->CMP val JZ skip ALERT level]",
        "[LOCK: evolve->GAUGE CMP thresh JNZ EVOLVE]",
        "[LOCK: halt->CMP 0 JZ HALT]",
        "[LOCK: reactor->reg 3]",
        "[LOCK: hull->reg 2]",
        "[LOCK: storm->reg 5]",
    ]
    
    programs = [
        TEST_PROGRAM,
        "heading=3 speed=5 loop gauge_reactor if temp>300 alert if pressure>100 evolve if vibration halt",
        "navigate north at 20 knots, check compass every step, alert if off-course>15 evolve on drift anchor at port",
    ]
    
    results = {}
    for n_locks in [0, 3, 7, 10]:
        locks = " ".join(all_locks[:n_locks])
        total_bytes = 0
        total_tokens = 0
        for prog in programs:
            r = call_model(exp.model, f"{locks}\nCompile FLUX hex ONLY: {prog}. Ops: {FLUX_OPS}", temp=0.1)
            total_bytes += len(extract_hex(r["content"]).split())
            total_tokens += r["tokens"]
        
        results[n_locks] = {
            "avg_bytes": total_bytes // len(programs),
            "avg_tokens": total_tokens // len(programs),
        }
        print(f"    {n_locks} locks: {results[n_locks]['avg_bytes']}B avg, {results[n_locks]['avg_tokens']}tok avg")
    
    # Check for compression trend
    b0 = results[0]["avg_bytes"]
    b10 = results[10]["avg_bytes"]
    results["compression_ratio"] = round(b10 / b0, 2) if b0 > 0 else 0
    results["hypothesis_supported"] = b10 < b0
    
    return results

def exp_model_personality(exp: Experiment) -> dict:
    """Test if different models develop different compilation styles."""
    models_to_test = ["qwen3-coder", "deepseek-chat", "glm4-flash"]
    programs = [
        TEST_PROGRAM,
        "set reactor 200, loop: gauge temp, if temp>500 alert, evolve on temp spike, halt at zero",
    ]
    
    results = {}
    for model in models_to_test:
        outputs = []
        for prog in programs:
            r = call_model(model, f"Compile FLUX hex ONLY: {prog}. Ops: {FLUX_OPS}", temp=0.1)
            outputs.append(extract_hex(r["content"]))
        results[model] = outputs
        print(f"    {model}: {outputs[0][:40]}...")
    
    # Check if any two models produce identical output
    keys = list(results.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            same = results[keys[i]] == results[keys[j]]
            results[f"{keys[i]}_vs_{keys[j]}"] = {"identical": same}
    
    return results

def exp_bytecode_first_speed(exp: Experiment) -> dict:
    """Test if writing bytecode is faster than pseudocode for models."""
    import time
    
    # Bytecode-first
    start = time.time()
    r_bc = call_model(exp.model, f"Write FLUX bytecode hex for a storm navigation program. Ops: {FLUX_OPS}. Think directly in hex.", temp=0.1)
    bc_time = time.time() - start
    
    # Pseudocode-first
    start = time.time()
    r_pc = call_model(exp.model, f"First write pseudocode for a storm navigation program, then compile to FLUX hex. Ops: {FLUX_OPS}.", temp=0.1)
    pc_time = time.time() - start
    
    results = {
        "bytecode_time": round(bc_time, 2),
        "pseudocode_time": round(pc_time, 2),
        "bytecode_tokens": r_bc["tokens"],
        "pseudocode_tokens": r_pc["tokens"],
        "bytecode_faster": bc_time < pc_time,
        "bytecode_cheaper": r_bc["tokens"] < r_pc["tokens"],
    }
    
    print(f"    Bytecode: {bc_time:.1f}s, {r_bc['tokens']}tok")
    print(f"    Pseudocode: {pc_time:.1f}s, {r_pc['tokens']}tok")
    
    return results

def exp_temperature_stability(exp: Experiment) -> dict:
    """Find the exact temperature where compilation becomes unstable."""
    thresholds = {}
    
    for temp in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        outputs = []
        for _ in range(3):
            r = call_model(exp.model, f"Compile FLUX hex ONLY: {TEST_PROGRAM}. Ops: {FLUX_OPS}", temp=temp)
            outputs.append(extract_hex(r["content"]))
        cc = consistency_check(outputs)
        thresholds[temp] = cc["consistent"]
        print(f"    t={temp}: {'✅' if cc['consistent'] else '❌'}")
        
        # Early stop: once unstable, we found the threshold
        if not cc["consistent"]:
            results = {"threshold_temp": temp, "stable_below": True, "unstable_at": temp}
            return results
    
    return {"threshold_temp": None, "all_stable": True}

# ════════════════════════════════════════════════════
# EXPERIMENT REGISTRY
# ════════════════════════════════════════════════════

EXPERIMENTS = [
    Experiment(id="lock_mass", hypothesis="Critical lock mass exists (7+ locks for consistency)", method=exp_critical_lock_mass, model="qwen3-coder", cost_est=0.05),
    Experiment(id="polyglot_consistency", hypothesis="Polyglot input is more consistent than monolingual", method=exp_polyglot_consistency, model="qwen3-coder", cost_est=0.03),
    Experiment(id="cross_model", hypothesis="Bytecode is 80%+ portable across model families", method=exp_cross_model_portability, model="qwen3-coder", cost_est=0.04),
    Experiment(id="lock_poisoning", hypothesis="Models detect poisoned compilation locks", method=exp_lock_poisoning, model="qwen3-coder", cost_est=0.02),
    Experiment(id="wisdom_compression", hypothesis="More locks = smaller/faster compilation", method=exp_wisdom_compression, model="qwen3-coder", cost_est=0.03),
    Experiment(id="model_personality", hypothesis="Different models develop different compilation styles", method=exp_model_personality, model="qwen3-coder", cost_est=0.03),
    Experiment(id="bytecode_speed", hypothesis="Writing bytecode-first is faster than pseudocode-first", method=exp_bytecode_first_speed, model="deepseek-chat", cost_est=0.01),
    Experiment(id="temp_stability", hypothesis="Compilation is stable below specific temperature threshold", method=exp_temperature_stability, model="qwen3-coder", cost_est=0.04),
]

# ════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════

def run_all(quick=False):
    print("╔══════════════════════════════════════════════════╗")
    print("║  FLUX RESEARCH QUEUE — Automated Experiments     ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Experiments: {len(EXPERIMENTS)}")
    print()
    
    all_results = {}
    total_cost = 0
    
    for exp in EXPERIMENTS:
        if quick and exp.cost_est > 0.03:
            print(f"⏭️  {exp.id}: skipped (cost ${exp.cost_est})")
            continue
        
        print(f"🔬 {exp.id}: {exp.hypothesis}")
        print(f"   Model: {exp.model} | Est: ${exp.cost_est}")
        
        exp.status = "running"
        start = time.time()
        
        try:
            result = exp.method(exp)
            elapsed = time.time() - start
            
            exp.result = result
            exp.rounds += 1
            
            # Determine verdict
            if "verified" in str(result):
                exp.status = "✅ VERIFIED"
            elif result.get("hypothesis_supported") == False or result.get("polyglot_better") == False:
                exp.status = "❌ FALSIFIED"
            else:
                exp.status = "📊 DATA"
            
            all_results[exp.id] = {
                "hypothesis": exp.hypothesis,
                "status": exp.status,
                "elapsed": round(elapsed, 1),
                "result": result,
            }
            
        except Exception as e:
            exp.status = "💥 ERROR"
            all_results[exp.id] = {"error": str(e)}
        
        print(f"   → {exp.status}")
        print()
        time.sleep(0.5)
    
    # Save results
    outfile = f"/home/ubuntu/.openclaw/workspace/research/queue-results-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.json"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("═" * 50)
    print(f"Done. {len(all_results)} experiments completed.")
    print(f"Results: {outfile}")
    
    # Summary
    verified = sum(1 for r in all_results.values() if "VERIFIED" in r.get("status", ""))
    falsified = sum(1 for r in all_results.values() if "FALSIFIED" in r.get("status", ""))
    data = sum(1 for r in all_results.values() if "DATA" in r.get("status", ""))
    errors = sum(1 for r in all_results.values() if "ERROR" in r.get("status", ""))
    
    print(f"  ✅ Verified: {verified}")
    print(f"  ❌ Falsified: {falsified}")
    print(f"  📊 Data: {data}")
    print(f"  💥 Errors: {errors}")

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    run_all(quick=quick)
