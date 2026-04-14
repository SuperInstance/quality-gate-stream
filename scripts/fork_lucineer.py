#!/usr/bin/env python3
"""
Fork remaining Lucineer repos to SuperInstance. 
Rate-limited: 3s between forks, 30s pause every 40.
"""
import json, time, os, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def _get_github_token():
    t = os.environ.get("GITHUB_TOKEN", "")
    if t:
        return t
    with open(os.path.expanduser("~/.bashrc")) as f:
        for line in f:
            if line.strip().startswith("export GITHUB_TOKEN="):
                return line.strip().split("=", 1)[1]
    return ""

TOKEN = _get_github_token()
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

def api_get(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def api_post(url, retries=3):
    req = Request(url, data=b"{}", headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as e:
            if e.code == 403 and "too quickly" in e.read().decode():
                wait = 30 * (attempt + 1)
                print(f"    rate limited, waiting {wait}s...", end=" ", flush=True)
                time.sleep(wait)
                continue
            elif e.code == 403:
                body = e.read().decode()
                if "no Git content" in body:
                    return 403, {"error": "empty repo"}
                return e.code, {"error": body[:100]}
            return e.code, {"error": str(e)[:100]}
        except Exception as e:
            return 0, {"error": str(e)[:100]}
    return 0, {"error": "max retries"}

def get_all_repo_names(owner):
    names = set()
    page = 1
    while True:
        batch = api_get(f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}")
        if not batch:
            break
        for r in batch:
            names.add(r["name"])
        page += 1
    return names

def main():
    print("Fetching repo lists...")
    si_repos = get_all_repo_names("SuperInstance")
    luc_repos = get_all_repo_names("Lucineer")
    
    to_fork = sorted([n for n in luc_repos if n not in si_repos])
    print(f"SuperInstance: {len(si_repos)} repos")
    print(f"Lucineer: {len(luc_repos)} repos")
    print(f"Need to fork: {len(to_fork)}")

    if not to_fork:
        print("All done!")
        return

    success, failed = [], []
    for i, name in enumerate(to_fork):
        print(f"  [{i+1}/{len(to_fork)}] {name}...", end=" ", flush=True)
        status, result = api_post(f"https://api.github.com/repos/Lucineer/{name}/forks")
        if status in (200, 201, 202):
            print("✓")
            success.append(name)
        elif status == 403 and "empty repo" in str(result.get("error","")):
            print("⊘ empty")
            failed.append({"name": name, "reason": "empty"})
        else:
            print(f"✗ {status}")
            failed.append({"name": name, "status": status, "error": str(result.get("error",""))[:80]})
        
        time.sleep(5)  # 5s between each fork (GitHub secondary rate limit)
        
        if (i + 1) % 30 == 0:
            print(f"  --- cooldown 60s ({i+1}/{len(to_fork)}) ---")
            time.sleep(60)

    out_dir = "/home/ubuntu/.openclaw/workspace/scripts/output"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/fork_results.json", "w") as f:
        json.dump({"forked": len(success), "failed": len(failed), "success": success, "failed_details": failed}, f, indent=2)
    
    print(f"\n✓ Forked: {len(success)} | ✗ Failed: {len(failed)}")
    if failed:
        print(f"Failed repos saved to {out_dir}/fork_results.json")

if __name__ == "__main__":
    main()
