#!/usr/bin/env python3
"""Curriculum Engine — CLI tool that runs a training curriculum for AI agents."""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone


API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
FALLBACK_MODEL = "ByteDance/Seed-2.0-mini"
API_KEY = "RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ"

STAGES = [
    (
        "ORIENTATION",
        "You are {agent}. Read your identity files. Summarize your role, capabilities, and place in the fleet.",
    ),
    (
        "EXPLORATION",
        "You are {agent}. List the 5 most important repos in your workspace and what they do.",
    ),
    (
        "APPLICATION",
        "You are {agent}. Pick one problem in your workspace and propose a concrete solution with file names and code changes.",
    ),
    (
        "SYNTHESIS",
        "You are {agent}. Connect 3 repos together to solve a fleet-level problem.",
    ),
    (
        "MASTERY",
        "You are {agent}. Write a teaching tile (Q&A format) that captures the most important thing you learned.",
    ),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Run a training curriculum for an AI agent.")
    parser.add_argument("--agent", required=True, help="Name of the agent.")
    parser.add_argument("--model", default="glm-4.7-flash", help="Model name (default: glm-4.7-flash).")
    parser.add_argument("--rounds", type=int, default=5, help="Number of rounds (default: 5).")
    parser.add_argument("--shell-dir", required=True, help="Path to agent's shell/config directory.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be run without making API calls.")
    return parser.parse_args()


def make_api_call(model, messages, temperature=0.7, max_tokens=1000):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def main():
    args = parse_args()

    if args.rounds < 1 or args.rounds > len(STAGES):
        print(f"--rounds must be between 1 and {len(STAGES)}", file=sys.stderr)
        sys.exit(1)

    # Prefer fallback model since the prompt says z.ai direct key expired
    effective_model = FALLBACK_MODEL

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = f"/tmp/curriculum-{args.agent}-{timestamp}.json"

    print(f"Curriculum Engine")
    print(f"  Agent : {args.agent}")
    print(f"  Model : {effective_model} (fallback)")
    print(f"  Rounds: {args.rounds}")
    print(f"  Shell : {args.shell_dir}")
    print(f"  Log   : {log_path}")
    if args.dry_run:
        print("  Mode  : DRY-RUN (no API calls)")
    print("-" * 40)

    log = {
        "agent": args.agent,
        "model": effective_model,
        "rounds": args.rounds,
        "shell_dir": args.shell_dir,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "stages": [],
    }

    messages = []
    total_tokens_estimate = 0

    for i in range(args.rounds):
        stage_name, template = STAGES[i]
        prompt = template.format(agent=args.agent)

        print(f"\nRound {i + 1}/{args.rounds} — {stage_name}")
        print(f"Prompt: {prompt}")

        if args.dry_run:
            response_text = f"[DRY-RUN] Would send prompt to {effective_model}."
            elapsed = 0.0
            tokens_estimate = 0
        else:
            messages.append({"role": "user", "content": prompt})
            start = time.monotonic()
            try:
                result = make_api_call(effective_model, messages)
            except Exception as exc:
                print(f"API error: {exc}", file=sys.stderr)
                log["error"] = str(exc)
                log["completed_at"] = datetime.now(timezone.utc).isoformat()
                log["summary"] = {
                    "total_tokens_estimate": total_tokens_estimate,
                    "completion_status": f"failed at round {i + 1} ({stage_name})",
                }
                with open(log_path, "w", encoding="utf-8") as f:
                    json.dump(log, f, indent=2)
                print(f"Partial log saved to {log_path}")
                sys.exit(1)

            elapsed = time.monotonic() - start
            choice = result.get("choices", [{}])[0]
            response_text = choice.get("message", {}).get("content", "")
            messages.append({"role": "assistant", "content": response_text})
            usage = result.get("usage", {})
            tokens_estimate = usage.get("total_tokens", len(prompt.split()) + len(response_text.split()))

        total_tokens_estimate += tokens_estimate

        print(f"Response ({len(response_text)} chars, {elapsed:.2f}s):")
        preview = response_text[:300].replace("\n", " ")
        print(f"  {preview}{'...' if len(response_text) > 300 else ''}")

        log["stages"].append({
            "round": i + 1,
            "stage": stage_name,
            "prompt": prompt,
            "response": response_text,
            "response_length": len(response_text),
            "elapsed_seconds": round(elapsed, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    log["completed_at"] = datetime.now(timezone.utc).isoformat()
    log["summary"] = {
        "total_tokens_estimate": total_tokens_estimate,
        "completion_status": "completed",
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    print("\n" + "=" * 40)
    print("CURRICULUM COMPLETE")
    print(f"  Rounds run : {args.rounds}")
    print(f"  Log file   : {log_path}")
    print(f"  Est. tokens: {total_tokens_estimate}")
    print(f"  Status     : completed")
    print("=" * 40)


if __name__ == "__main__":
    main()
