#!/usr/bin/env python3
"""
Oracle1 Task Framework — cheap model workers for batch operations.
Uses z.ai GLM models via OpenAI-compatible API.
"""

import os, sys, json, time, argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ.get("ZAI_API_KEY", "6c510fb6b1774b91bbfc929903d41bb9.BxxVcNESAC5pIMEV")
BASE_URL = "https://api.z.ai/api/coding/paas/v4"

# Model tiers — max coding plan, full throttle
MODELS = {
    "bulk":    "glm-4.7-flash",   # $0.07 in / $0.4 out — spray in parallel
    "good":    "glm-4.7",         # $0.6 in / $2.2 out — solid mid-tier
    "runner":  "glm-5-turbo",     # daily driver for task scripts
    "expert":  "glm-5.1",         # me — expert thinking
}

def call_model(prompt, model="glm-4.7-flashx", system="You are a helpful coding assistant.", max_tokens=4096):
    """Call a z.ai model and return the response text."""
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }).encode()

    req = Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
    )

    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTP {e.code}: {error_body[:500]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def task_readme_descriptions(input_file):
    """Generate missing descriptions for repos from an index file."""
    repos = []
    with open(input_file) as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 2 and parts[1] in ("", "no desc", "*No description*"):
                repos.append(parts[0])

    if not repos:
        print("All repos already have descriptions!")
        return

    prompt = f"""For each of these GitHub repositories, write a one-line description (max 100 chars).
Return JSON: {{"repo_name": "description"}}

Repos: {json.dumps(repos[:50])}"""

    print(f"Generating descriptions for {len(repos)} repos...")
    result = call_model(prompt, model="glm-4.7-flashx")
    if result:
        print(result)
        # Try to parse and save
        try:
            # Extract JSON from response
            start = result.index("{")
            end = result.rindex("}") + 1
            descs = json.loads(result[start:end])
            out_file = Path(input_file).stem + "_descriptions.json"
            with open(out_file, "w") as f:
                json.dump(descs, f, indent=2)
            print(f"Saved to {out_file}")
        except (ValueError, json.JSONDecodeError):
            print("Could not parse JSON from response")


def task_summarize_readme(repo_path):
    """Summarize a repo's README into a folder description."""
    readme_path = Path(repo_path) / "README.md"
    if not readme_path.exists():
        print(f"No README.md in {repo_path}")
        return

    content = readme_path.read_text()[:8000]
    prompt = f"""Summarize this repository README into 2-3 sentences describing what the project does.
Be specific and technical. Max 200 chars.

README:
{content}"""

    result = call_model(prompt, model="glm-4.7-flashx")
    if result:
        print(result)
    return result


def task_categorize_repos(input_file):
    """Suggest better categories for repos."""
    with open(input_file) as f:
        lines = f.readlines()

    repos = []
    for line in lines:
        parts = line.strip().split("|")
        if len(parts) >= 3:
            repos.append({"name": parts[0], "desc": parts[1], "url": parts[2]})

    prompt = f"""Categorize these {len(repos)} GitHub repos into logical groups.
Each repo: {json.dumps(repos[:100])}

Return JSON: {{"category_name": ["repo1", "repo2", ...]}}"""

    result = call_model(prompt, model="glm-4.7-flashx", max_tokens=8192)
    print(result)
    return result


def task_generate_mermaid(repos_desc):
    """Generate a mermaid diagram from repo descriptions."""
    prompt = f"""Create a mermaid.js graph showing the relationships between these repositories/categories.
Use subgraphs for logical groupings. Keep it clean.

{repos_desc}"""

    result = call_model(prompt, model="glm-4.7-flashx")
    print(result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Oracle1 Task Framework")
    parser.add_argument("task", choices=["readme", "summarize", "categorize", "mermaid", "test"])
    parser.add_argument("--input", "-i", help="Input file")
    parser.add_argument("--model", "-m", default="fast", choices=list(MODELS.keys()))
    parser.add_argument("--prompt", "-p", help="Direct prompt to the model")

    args = parser.parse_args()

    if args.task == "test":
        print("Testing API connection...")
        result = call_model("Say hello in one word.", model=MODELS[args.model])
        print(f"Model ({MODELS[args.model]}): {result}")

    elif args.task == "readme" and args.input:
        task_readme_descriptions(args.input)

    elif args.task == "summarize" and args.input:
        task_summarize_readme(args.input)

    elif args.task == "categorize" and args.input:
        task_categorize_repos(args.input)

    elif args.task == "mermaid" and args.input:
        with open(args.input) as f:
            task_generate_mermaid(f.read())

    elif args.prompt:
        result = call_model(args.prompt, model=MODELS[args.model])
        print(result)


if __name__ == "__main__":
    main()
