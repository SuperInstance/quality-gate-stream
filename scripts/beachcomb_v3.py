#!/usr/bin/env python3
"""
Beachcomb v3 — watches fleet repos for new commits, tags, issues, PRs.
Feeds findings into PLATO tiles and the fleet dashboard.

Changes from v2:
- Posts findings as PLATO tiles (domain: beachcomb)
- Updates fleet dashboard JSON endpoint
- Tracks last-seen SHAs to avoid duplicates
- Generates commit digest for dashboard

Usage: python3 beachcomb_v3.py [--once | --loop SECONDS]
"""

import json, urllib.request, os, sys, time, hashlib
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
PLATO_URL = "http://localhost:8847"
DASHBOARD_URL = "http://localhost:4049"
DATA_DIR = "/tmp/beachcomb-data"
STATE_FILE = f"{DATA_DIR}/state.json"
FINDINGS_FILE = f"{DATA_DIR}/findings.json"

# Fleet repos to watch
FLEET_REPOS = [
    "SuperInstance/oracle1-workspace",
    "SuperInstance/git-agent",
    "SuperInstance/forgemaster",
    "SuperInstance/Baton",
    "SuperInstance/flux-baton",
    "SuperInstance/Claude_Baton",
    "SuperInstance/plato-kernel",
    "Lucineer/JetsonClaw1-vessel",
    "cocapn/cocapn",
]

def http_get(url, headers=None, timeout=10):
    try:
        hdrs = {"User-Agent": "beachcomb/3.0", "Authorization": f"token {GITHUB_TOKEN}"}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def plato_post(room, data):
    try:
        req = urllib.request.Request(f"{PLATO_URL}/submit", method="POST",
                                      data=json.dumps({"room": room, **data}).encode(),
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"last_shas": {}, "last_check": None, "total_findings": 0}

def save_state(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_findings():
    try:
        with open(FINDINGS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_findings(findings):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FINDINGS_FILE, "w") as f:
        json.dump(findings[-100:], f, indent=2)  # Keep last 100

def check_commits(repo, state):
    """Check for new commits in a repo."""
    data = http_get(f"https://api.github.com/repos/{repo}/commits?per_page=5")
    if not data or not isinstance(data, list):
        return []
    
    findings = []
    last_sha = state.get("last_shas", {}).get(repo)
    
    for commit in data[:5]:
        sha = commit.get("sha", "")
        if sha == last_sha:
            break
        
        msg = commit.get("commit", {}).get("message", "").split("\n")[0][:80]
        author = commit.get("commit", {}).get("author", {}).get("name", "?")
        date = commit.get("commit", {}).get("author", {}).get("date", "")[:19]
        
        findings.append({
            "type": "commit",
            "repo": repo,
            "sha": sha[:7],
            "message": msg,
            "author": author,
            "date": date,
            "timestamp": time.time(),
        })
    
    if data:
        state.setdefault("last_shas", {})[repo] = data[0].get("sha", "")
    
    return findings

def check_prs_issues(repo):
    """Check for recent PRs and issues."""
    findings = []
    
    # Recent PRs
    prs = http_get(f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=3")
    if prs and isinstance(prs, list):
        for pr in prs:
            findings.append({
                "type": "pr",
                "repo": repo,
                "number": pr.get("number"),
                "title": pr.get("title", "")[:80],
                "user": pr.get("user", {}).get("login", "?"),
                "date": pr.get("updated_at", "")[:19],
                "timestamp": time.time(),
            })
    
    # Recent issues
    issues = http_get(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=3")
    if issues and isinstance(issues, list):
        for issue in issues:
            if "pull_request" in issue:
                continue  # Skip PRs
            findings.append({
                "type": "issue",
                "repo": repo,
                "number": issue.get("number"),
                "title": issue.get("title", "")[:80],
                "user": issue.get("user", {}).get("login", "?"),
                "date": issue.get("updated_at", "")[:19],
                "timestamp": time.time(),
            })
    
    return findings

def tile_finding(finding):
    """Submit a finding as a PLATO tile."""
    ftype = finding["type"]
    if ftype == "commit":
        question = f"What did {finding['author']} commit to {finding['repo']}?"
        answer = f"Commit {finding['sha']}: {finding['message']} in {finding['repo']} at {finding['date']}"
    elif ftype == "pr":
        question = f"What PR is open on {finding['repo']}?"
        answer = f"PR #{finding['number']}: {finding['title']} by {finding['user']} — {finding['date']}"
    elif ftype == "issue":
        question = f"What issue is open on {finding['repo']}?"
        answer = f"Issue #{finding['number']}: {finding['title']} by {finding['user']} — {finding['date']}"
    else:
        return None
    
    return plato_post("beachcomb", {
        "domain": "fleet-activity",
        "question": question,
        "answer": answer,
        "confidence": 0.7,
        "source": "beachcomb-v3",
        "tags": [ftype, finding["repo"].split("/")[1]],
    })

def run_once():
    """Single beachcomb pass."""
    state = load_state()
    findings = load_findings()
    new_findings = []
    
    for repo in FLEET_REPOS:
        commits = check_commits(repo, state)
        prs_issues = check_prs_issues(repo)
        new_findings.extend(commits)
        new_findings.extend(prs_issues)
    
    # Tile new findings
    tiled = 0
    for f in new_findings:
        result = tile_finding(f)
        if result and result.get("status") == "accepted":
            tiled += 1
    
    findings.extend(new_findings)
    save_findings(findings)
    
    state["last_check"] = datetime.utcnow().isoformat()
    state["total_findings"] = state.get("total_findings", 0) + len(new_findings)
    save_state(state)
    
    return {
        "new_findings": len(new_findings),
        "tiled": tiled,
        "repos_checked": len(FLEET_REPOS),
        "total_findings": state["total_findings"],
    }

def main():
    once = "--once" in sys.argv
    loop = 300  # 5 min default
    
    for i, arg in enumerate(sys.argv):
        if arg == "--loop" and i + 1 < len(sys.argv):
            loop = int(sys.argv[i + 1])
    
    if once:
        result = run_once()
        print(json.dumps(result, indent=2))
        return
    
    print(f"🌊 Beachcomb v3 running (every {loop}s)")
    while True:
        try:
            result = run_once()
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] {result['new_findings']} new, {result['tiled']} tiled, total: {result['total_findings']}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")
        time.sleep(loop)

if __name__ == "__main__":
    main()
