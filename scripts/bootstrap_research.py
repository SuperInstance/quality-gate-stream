#!/usr/bin/env python3
"""Self-Bootstrapping Research Experiment Runner

Runs iterative experiments on SiliconFlow models, collects results,
and uses those results to design the NEXT round of experiments.

Each round:
1. Generate hypotheses from previous results
2. Run experiments across multiple models
3. Analyze results for patterns
4. Design next round based on discoveries
"""

import json
import urllib.request
import ssl
import time
import os
import sys
from datetime import datetime

SFKEY = os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]")
SFURL = "https://api.siliconflow.com/v1/chat/completions"
ctx = ssl.create_default_context()

MODELS = {
    "deepseek-v3": "deepseek-ai/DeepSeek-V3",
    "qwen3-coder": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "seed": "ByteDance/Seed-OSS-36B-Instruct",
}

FLUX_OPS = {
    "NOP": "0x00", "HALT": "0x01", "MOVI": "0x10", "MOV": "0x11",
    "IADD": "0x20", "ISUB": "0x21", "IMUL": "0x22",
    "JMP": "0x30", "JZ": "0x31", "JNZ": "0x32",
    "CMP": "0x40", "JE": "0x41",
    "PUSH": "0x50", "POP": "0x51",
    "CALL": "0x60", "RET": "0x61",
    "GAUGE": "0x90", "ALERT": "0x91", "EVOLVE": "0xA0", "SAY": "0x80",
}

def call_model(model_id, prompt, temp=0.3, max_tokens=300):
    """Call a SiliconFlow model."""
    body = json.dumps({
        "model": MODELS.get(model_id, model_id),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }).encode()
    req = urllib.request.Request(
        SFURL, data=body,
        headers={"Authorization": f"Bearer {SFKEY}", "Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=25, context=ctx)
        data = json.loads(resp.read())
        return {
            "content": data["choices"][0]["message"]["content"],
            "tokens": data.get("usage", {}).get("total_tokens", 0),
            "model": model_id
        }
    except Exception as e:
        return {"content": f"ERROR: {e}", "tokens": 0, "model": model_id}


def run_experiment(exp_id, prompt, models=None, temps=None):
    """Run an experiment across models and temperatures."""
    models = models or list(MODELS.keys())
    temps = temps or [0.1, 0.5, 0.9]
    results = []
    
    for model in models:
        for temp in temps:
            start = time.time()
            r = call_model(model, prompt, temp=temp)
            elapsed = time.time() - start
            r["temp"] = temp
            r["elapsed"] = round(elapsed, 2)
            r["exp_id"] = exp_id
            results.append(r)
            print(f"  {model} t={temp}: {r['tokens']}tok {elapsed:.1f}s → {r['content'][:60]}...")
            time.sleep(0.3)
    
    return results


def analyze_consistency(results):
    """Check if outputs are consistent across temperatures."""
    by_model = {}
    for r in results:
        by_model.setdefault(r["model"], []).append(r["content"])
    
    analysis = {}
    for model, outputs in by_model.items():
        unique = len(set(o.strip()[:50] for o in outputs))
        total = len(outputs)
        analysis[model] = {
            "unique_outputs": unique,
            "total": total,
            "consistent": unique == 1,
            "samples": [o[:100] for o in outputs[:2]]
        }
    return analysis


def generate_next_round(prev_results, round_num):
    """Use a creative model to design the next experiment based on findings."""
    findings = json.dumps(prev_results, indent=2)[:2000]
    
    prompt = f"""You are a research architect. Based on round {round_num} results:

{findings}

Design the NEXT experiment to explore these findings further. What question should we ask now?
Format: EXPERIMENT_ID, HYPOTHESIS, PROMPT_TO_TEST, EXPECTED_INSIGHT
Be specific and creative. Push into unknown territory."""

    r = call_model("seed", prompt, temp=0.95, max_tokens=400)
    return r["content"]


# ═══ EXPERIMENTS ═══

def exp_bytecode_vs_english():
    """Exp A: Can models write bytecode more consistently than English pseudocode?"""
    print("\n╔══ EXP A: Bytecode vs English Consistency ══╗")
    
    # Same program, two prompts
    prompts = {
        "bytecode": f"Write FLUX bytecode hex for: set heading=1, speed=10, loop: gauge hull, if reactor>200 alert, if storm=0 halt. Ops: {FLUX_OPS}. Output ONLY hex.",
        "english": "Write pseudocode for: set heading=1, speed=10, loop: gauge hull, if reactor>200 alert, if storm=0 halt. Output ONLY pseudocode.",
    }
    
    results = {}
    for kind, prompt in prompts.items():
        print(f"\n  --- {kind} prompt ---")
        results[kind] = run_experiment(f"A-{kind}", prompt, models=["qwen3-coder"], temps=[0.1, 0.3, 0.5, 0.7, 0.9])
    
    bc_consistent = analyze_consistency(results["bytecode"])
    en_consistent = analyze_consistency(results["english"])
    
    print(f"\n  Bytecode consistency: {bc_consistent}")
    print(f"  English consistency: {en_consistent}")
    return {"bytecode": bc_consistent, "english": en_consistent}


def exp_lock_cascade():
    """Exp B: Do locks compound? Does having MORE locks improve quality exponentially?"""
    print("\n╔══ EXP B: Lock Cascade ══╗")
    
    base = "Compile to FLUX hex: navigate east 10 knots, check hull, alert reactor>200, evolve on spike, anchor at storm=0."
    
    lock_levels = {
        "0_locks": base,
        "3_locks": f"[LOCK: navigate→MOVI heading 1] [LOCK: loop→JNZ] [LOCK: alert→CMP JZ ALERT]\n{base}",
        "7_locks": f"[LOCK: navigate→MOVI heading 1] [LOCK: speed→MOVI speed 10] [LOCK: loop→JNZ] [LOCK: gauge→GAUGE reg] [LOCK: alert→CMP JZ ALERT] [LOCK: evolve→GAUGE CMP JNZ EVOLVE] [LOCK: anchor→CMP 0 JZ HALT]\n{base}",
    }
    
    results = {}
    for level, prompt in lock_levels.items():
        print(f"\n  --- {level} ---")
        results[level] = run_experiment(f"B-{level}", prompt, models=["qwen3-coder"], temps=[0.3, 0.7])
    
    return {k: analyze_consistency(v) for k, v in results.items()}


def exp_polyglot_semantic_density():
    """Exp C: Which language produces the most semantically dense bytecode?"""
    print("\n╔══ EXP C: Polyglot Semantic Density ══╗")
    
    programs = {
        "english": "Navigate east at 10 knots, check hull every loop, alert if reactor hot, evolve on spike, anchor at zero",
        "japanese": "東に10ノットで航海、船体確認、原子炉熱で警告、急上昇で進化、ゼロで停泊",
        "french_maritime": "naviguer est 10 noeuds, vérifier coque, alerter réacteur chaud, évoluer si pic, ancrer à zéro",
        "mixed": "東に10ノット航海, check coque chaque boucle, alert si réacteur>200, 演化 on spike, 锚 at zero",
    }
    
    results = {}
    for lang, prog in programs.items():
        prompt = f"Compile to FLUX bytecode hex ONLY: {prog}\nOps: {FLUX_OPS}"
        print(f"\n  --- {lang} ---")
        r = call_model("qwen3-coder", prompt, temp=0.3)
        # Count actual hex bytes
        hex_chars = sum(1 for c in r["content"] if c in "0123456789abcdefABCDEF")
        byte_count = hex_chars // 2
        results[lang] = {
            "bytes": byte_count,
            "input_tokens": r["tokens"],
            "output_sample": r["content"][:100],
            "density": round(byte_count / max(r["tokens"], 1), 2)
        }
        print(f"    {byte_count} bytes, {r['tokens']} tokens, density={results[lang]['density']}")
    
    return results


def exp_cross_model_reading():
    """Exp D: Can model A read model B's bytecode?"""
    print("\n╔══ EXP D: Cross-Model Bytecode Reading ══╗")
    
    # Model A writes
    write_r = call_model("deepseek-v3",
        f"Write FLUX bytecode for a simple storm avoidance program. Ops: {FLUX_OPS}. Registers: R0-R5. Output bytecode with comments.",
        temp=0.3)
    bytecode = write_r["content"]
    print(f"  DeepSeek-V3 wrote: {bytecode[:150]}...")
    
    # Model B reads
    read_r = call_model("qwen3-coder",
        f"Read this FLUX bytecode and explain what it does:\n{bytecode}\nExplain each instruction.",
        temp=0.3)
    
    print(f"  Qwen3-Coder read: {read_r['content'][:200]}...")
    
    # Original author verifies the reading
    verify_r = call_model("deepseek-v3",
        f"You wrote this bytecode:\n{bytecode}\n\nAnother model interpreted it as:\n{read_r['content']}\n\nIs their interpretation correct? Grade 1-10.",
        temp=0.3)
    
    print(f"  Author verification: {verify_r['content'][:200]}")
    
    return {"bytecode": bytecode[:500], "reading": read_r["content"][:500], "verification": verify_r["content"][:500]}


# ═══ MAIN ═══

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║  SELF-BOOTSTRAPPING RESEARCH — FLUX COGNITIVE COMP   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"Started: {datetime.utcnow().isoformat()}")
    
    all_results = {}
    
    # Run experiments
    all_results["exp_A"] = exp_bytecode_vs_english()
    all_results["exp_B"] = exp_lock_cascade()
    all_results["exp_C"] = exp_polyglot_semantic_density()
    all_results["exp_D"] = exp_cross_model_reading()
    
    # Synthesize findings
    print("\n╔══ SYNTHESIS: What did we learn? ══╗")
    next_round = generate_next_round(all_results, 1)
    print(f"\n  Next round suggestion:\n  {next_round}")
    
    # Save results
    all_results["synthesis"] = next_round
    all_results["timestamp"] = datetime.utcnow().isoformat()
    
    outfile = "/home/ubuntu/.openclaw/workspace/research/bootstrap-results-r1.json"
    with open(outfile, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {outfile}")
    print(f"Total tokens used: ~{sum(r.get('tokens',0) for exp in all_results.values() if isinstance(exp, dict) for r in exp.values() if isinstance(r, list) for r in r)}")
