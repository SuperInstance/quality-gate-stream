#!/usr/bin/env python3
"""
Oracle1 Batch Workers — parallel tasks using cheap z.ai models.

Usage:
  python3 batch.py descriptions   # Generate descriptions for repos missing them
  python3 batch.py analyze        # Analyze repo patterns and suggest improvements
  python3 batch.py export         # Export full index as structured JSON
"""

import os, sys, json, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ.get("ZAI_API_KEY", "6c510fb6b1774b91bbfc929903d41bb9.BxxVcNESAC5pIMEV")
BASE_URL = "https://api.z.ai/api/coding/paas/v4"

def _get_github_token():
    t = os.environ.get("GITHUB_TOKEN", "")
    if t:
        return t
    try:
        with open(os.path.expanduser("~/.bashrc")) as f:
            for line in f:
                if line.strip().startswith("export GITHUB_TOKEN="):
                    return line.strip().split("=", 1)[1]
    except:
        pass
    return ""

GITHUB_TOKEN = _get_github_token()
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")

def call_zai(prompt, model="glm-4.7-flashx", system="You are a helpful coding assistant.", max_tokens=4096):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }).encode()

    req = Request(f"{BASE_URL}/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
    
    try:
        with urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def github_api(url):
    """Call GitHub API with auth."""
    req = Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_all_repos(owner):
    """Fetch all repos for a user/org."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}"
        data = github_api(url)
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def generate_descriptions_batch(repos_with_no_desc, batch_size=30):
    """Generate descriptions for repos that have none, in batches."""
    results = {}
    
    def process_batch(batch):
        names = [r["name"] for r in batch]
        prompt = f"""For each GitHub repository name, write a ONE-LINE description (max 120 chars) that explains what the project likely does based on its name.
Return ONLY valid JSON mapping repo name to description string. No markdown.

Repos: {json.dumps(names)}"""
        
        resp = call_zai(prompt, model="glm-4.7-flashx", max_tokens=4096)
        try:
            # Extract JSON
            start = resp.index("{")
            end = resp.rindex("}") + 1
            return json.loads(resp[start:end])
        except (ValueError, json.JSONDecodeError):
            return {}
    
    batches = [repos_with_no_desc[i:i+batch_size] for i in range(0, len(repos_with_no_desc), batch_size)]
    
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(process_batch, b): i for i, b in enumerate(batches)}
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                descs = future.result()
                results.update(descs)
                print(f"  Batch {batch_idx+1}/{len(batches)}: got {len(descs)} descriptions")
            except Exception as e:
                print(f"  Batch {batch_idx+1} failed: {e}")
    
    return results


def cmd_descriptions():
    """Generate descriptions for all repos missing them."""
    print("Fetching repo lists...")
    
    for owner in ["SuperInstance", "Lucineer"]:
        print(f"\n=== {owner} ===")
        repos = fetch_all_repos(owner)
        no_desc = [r for r in repos if not r.get("description")]
        print(f"  {len(no_desc)} repos without descriptions out of {len(repos)}")
        
        if no_desc:
            print(f"  Generating descriptions...")
            descs = generate_descriptions_batch(no_desc)
            
            # Save results
            out = WORKSPACE / "scripts" / "output" / f"{owner.lower()}_descriptions.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as f:
                json.dump(descs, f, indent=2)
            print(f"  Saved to {out}")
            
            # Optionally update GitHub
            print(f"\n  To apply descriptions, run:")
            print(f"  python3 batch.py apply_descriptions {owner}")


def cmd_analyze():
    """Analyze the ecosystem and produce insights."""
    print("Analyzing ecosystem...")
    
    all_repos = {"SuperInstance": fetch_all_repos("SuperInstance"), 
                 "Lucineer": fetch_all_repos("Lucineer")}
    
    # Build summary for analysis
    summary = []
    for owner, repos in all_repos.items():
        for r in repos:
            summary.append(f"{owner}/{r['name']}: {r.get('description', 'no desc')}")
    
    prompt = f"""Analyze this collection of {len(summary)} GitHub repositories across two profiles (SuperInstance and Lucineer).
Identify:
1. The top 5 core themes/paradigms
2. The most interconnected projects (hub repos)
3. Any gaps or missing pieces in the ecosystem
4. Suggested next projects to build

Repos (name: description):
{chr(10).join(summary[:200])}"""

    result = call_zai(prompt, model="glm-4.7", max_tokens=8192)
    
    out = WORKSPACE / "scripts" / "output" / "ecosystem_analysis.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(f"# Ecosystem Analysis\n\n{result}")
    print(result)
    print(f"\nSaved to {out}")


def cmd_export():
    """Export full repo data as structured JSON."""
    data = {}
    for owner in ["SuperInstance", "Lucineer"]:
        repos = fetch_all_repos(owner)
        data[owner] = [{
            "name": r["name"],
            "description": r.get("description", ""),
            "url": r["html_url"],
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "topics": r.get("topics", []),
            "created": r.get("created_at", ""),
            "updated": r.get("updated_at", ""),
            "default_branch": r.get("default_branch", "main")
        } for r in sorted(repos, key=lambda x: x["name"])]
    
    out = WORKSPACE / "scripts" / "output" / "full_index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Exported {sum(len(v) for v in data.values())} repos to {out}")


def cmd_apply_descriptions(owner):
    """Apply generated descriptions to repos on GitHub."""
    desc_file = WORKSPACE / "scripts" / "output" / f"{owner.lower()}_descriptions.json"
    if not desc_file.exists():
        print(f"No descriptions file for {owner}. Run 'descriptions' first.")
        return
    
    with open(desc_file) as f:
        descs = json.load(f)
    
    print(f"Applying {len(descs)} descriptions to {owner}...")
    applied, failed = 0, 0
    
    for name, desc in descs.items():
        url = f"https://api.github.com/repos/{owner}/{name}"
        body = json.dumps({"description": desc}).encode()
        req = Request(url, data=body, headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }, method="PATCH")
        try:
            with urlopen(req, timeout=30) as resp:
                if resp.status in (200, 201):
                    applied += 1
                    if applied % 20 == 0:
                        print(f"  {applied}/{len(descs)} applied...")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name}: {e}")
        time.sleep(0.5)  # avoid secondary rate limit
    
    print(f"Done! Applied: {applied}, Failed: {failed}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "descriptions":
        cmd_descriptions()
    elif cmd == "analyze":
        cmd_analyze()
    elif cmd == "export":
        cmd_export()
    elif cmd == "apply_descriptions" and len(sys.argv) >= 3:
        cmd_apply_descriptions(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
