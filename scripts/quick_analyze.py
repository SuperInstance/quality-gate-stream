#!/usr/bin/env python3
"""Quick ecosystem analysis using cheaper model."""
import sys
sys.path.insert(0, "/home/ubuntu/.openclaw/workspace/scripts")
from batch import call_zai, fetch_all_repos
import json

print("Fetching repos...")
repos = []
for owner in ["SuperInstance", "Lucineer"]:
    for r in fetch_all_repos(owner):
        desc = r.get("description") or ""
        repos.append(f"{owner}/{r['name']}: {desc[:80]}")

print(f"Got {len(repos)} repos, analyzing...")

# Split into 2 batches
half = len(repos) // 2
batches = [repos[:half], repos[half:]]

for i, batch in enumerate(batches):
    prompt = f"""Analyze these {len(batch)} GitHub repos. Identify:
1. Top 5 core themes
2. Hub repos (most connected/important)
3. Missing pieces in the ecosystem

Repos:
{chr(10).join(batch)}"""

    result = call_zai(prompt, model="glm-4.7-flashx", max_tokens=4096)
    print(f"\n=== Part {i+1} ===")
    print(result)
