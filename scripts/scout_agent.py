#!/usr/bin/env python3
"""
Scout Agent Service — roams fleet repos, finds gaps, reports opportunities.

Modes:
  /scan      — full fleet scan (stale repos, missing tests/docs/CI)
  /gaps      — deep gap analysis (find what's missing)
  /patterns  — cross-repo pattern detection
  /report    — generate full fleet health report
  /watch     — continuous mode, check periodically

HTTP API on port 4052.
"""

import json, urllib.request, os, sys, time, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
PLATO_URL = "http://localhost:8847"
DATA_DIR = Path("/tmp/scout-data")
DATA_DIR.mkdir(exist_ok=True)
REPORT_FILE = DATA_DIR / "latest-report.json"
STATE_FILE = DATA_DIR / "state.json"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "User-Agent": "scout-agent/1.0",
}

def api_get(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def plato_post(data):
    try:
        req = urllib.request.Request(f"{PLATO_URL}/submit", method="POST",
                                      data=json.dumps(data).encode(),
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except:
        return None


class FleetScout:
    """The Scout roams the fleet, finding gaps and opportunities."""
    
    def __init__(self):
        self.repos = []
        self.report = {}
    
    def load_fleet(self):
        """Load all fleet repos."""
        self.repos = []
        page = 1
        while True:
            data = api_get(f"https://api.github.com/user/repos?per_page=100&page={page}&sort=updated")
            if not data:
                break
            self.repos.extend(data)
            page += 1
            if len(data) < 100:
                break
        
        # Add cocapn user repos
        cocapn = api_get("https://api.github.com/users/cocapn/repos?per_page=100&sort=updated")
        if cocapn:
            existing = {r["full_name"] for r in self.repos}
            for r in cocapn:
                if r["full_name"] not in existing:
                    self.repos.append(r)
        
        return len(self.repos)
    
    def check_readme(self, repo):
        """Check if repo has a README and its quality."""
        name = repo["full_name"]
        readme = api_get(f"https://api.github.com/repos/{name}/contents/README.md")
        if not readme:
            return "missing"
        if readme.get("size", 0) < 100:
            return "stub"
        if readme.get("size", 0) < 500:
            return "thin"
        return "ok"
    
    def check_ci(self, repo):
        """Check if repo has CI workflows."""
        name = repo["full_name"]
        ci = api_get(f"https://api.github.com/repos/{name}/contents/.github/workflows")
        if not ci or not isinstance(ci, list):
            return "missing"
        return f"{len(ci)} workflows"
    
    def check_tests(self, repo):
        """Check if repo has test files."""
        name = repo["full_name"]
        lang = repo.get("language", "")
        
        # Check common test patterns
        test_paths = {
            "Python": ["tests/", "test/", "test_"],
            "Rust": ["tests/", "#[test]"],
            "TypeScript": ["test/", "tests/", ".test.ts", ".spec.ts"],
            "Go": ["_test.go"],
        }
        
        patterns = test_paths.get(lang, ["test/", "tests/"])
        for pattern in patterns:
            if pattern.endswith("/"):
                result = api_get(f"https://api.github.com/repos/{name}/contents/{pattern}")
                if result and isinstance(result, list) and len(result) > 0:
                    return "has tests"
            else:
                # Search for test files
                search = api_get(f"https://api.github.com/search/code?q={pattern}+repo:{name}")
                if search and search.get("total_count", 0) > 0:
                    return "has tests"
        
        return "missing"
    
    def check_license(self, repo):
        """Check if repo has a license."""
        return "mit" if repo.get("license") else "missing"
    
    def check_staleness(self, repo):
        """Check how stale a repo is."""
        updated = repo.get("updated_at", "")
        if not updated:
            return "unknown"
        
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
            if age_days > 365:
                return f"stale ({age_days}d)"
            elif age_days > 180:
                return f"old ({age_days}d)"
            elif age_days > 90:
                return f"aging ({age_days}d)"
            return f"fresh ({age_days}d)"
        except:
            return "unknown"
    
    def full_scan(self):
        """Run full fleet scan — check all repos for gaps."""
        count = self.load_fleet()
        print(f"Scout scanning {count} repos...")
        
        findings = {
            "total_repos": count,
            "forks": sum(1 for r in self.repos if r.get("fork")),
            "non_forks": sum(1 for r in self.repos if not r.get("fork")),
            "missing_readme": [],
            "stub_readme": [],
            "thin_readme": [],
            "missing_ci": [],
            "missing_tests": [],
            "missing_license": [],
            "stale": [],
            "empty": [],
            "no_description": [],
            "score_distribution": defaultdict(int),
        }
        
        for repo in self.repos:
            if repo.get("fork"):
                continue
            
            name = repo["full_name"]
            
            # Check description
            if not repo.get("description"):
                findings["no_description"].append(name)
            
            # Check if empty
            if repo.get("size", 0) == 0:
                findings["empty"].append(name)
                continue
            
            # Check README
            readme_status = self.check_readme(repo)
            if readme_status == "missing":
                findings["missing_readme"].append(name)
            elif readme_status == "stub":
                findings["stub_readme"].append(name)
            elif readme_status == "thin":
                findings["thin_readme"].append(name)
            
            # Check CI (skip for repos < 1 week old or very small)
            if repo.get("size", 0) > 50:
                ci = self.check_ci(repo)
                if ci == "missing":
                    findings["missing_ci"].append(name)
            
            # Check license
            lic = self.check_license(repo)
            if lic == "missing":
                findings["missing_license"].append(name)
            
            # Check staleness
            stale = self.check_staleness(repo)
            if "stale" in stale:
                findings["stale"].append({"repo": name, "status": stale})
            
            # Score the repo (0-5)
            score = 0
            if readme_status == "ok": score += 1
            if repo.get("description"): score += 1
            if lic == "mit": score += 1
            if "fresh" in stale: score += 1
            if repo.get("size", 0) > 100: score += 1
            findings["score_distribution"][score] += 1
        
        self.report = findings
        return findings
    
    def gap_analysis(self):
        """Deep gap analysis — find what specific things are missing."""
        if not self.report:
            self.full_scan()
        
        gaps = []
        
        # Repos missing README
        for name in self.report.get("missing_readme", [])[:10]:
            gaps.append({
                "type": "missing_readme",
                "repo": name,
                "severity": "high",
                "fix": f"Create README.md with project description, usage, and install instructions",
            })
        
        # Repos missing CI
        for name in self.report.get("missing_ci", [])[:10]:
            gaps.append({
                "type": "missing_ci",
                "repo": name,
                "severity": "medium",
                "fix": f"Add .github/workflows/ci.yml with test + lint steps",
            })
        
        # Repos missing license
        for name in self.report.get("missing_license", [])[:10]:
            gaps.append({
                "type": "missing_license",
                "repo": name,
                "severity": "medium",
                "fix": f"Add MIT LICENSE file",
            })
        
        # Empty repos
        for name in self.report.get("empty", [])[:10]:
            gaps.append({
                "type": "empty_repo",
                "repo": name,
                "severity": "low",
                "fix": f"Either populate with code or archive",
            })
        
        # No description
        for name in self.report.get("no_description", [])[:10]:
            gaps.append({
                "type": "no_description",
                "repo": name,
                "severity": "low",
                "fix": f"Add a description to the GitHub repo settings",
            })
        
        return gaps
    
    def find_patterns(self):
        """Find cross-repo patterns and shared issues."""
        if not self.report:
            self.full_scan()
        
        patterns = []
        
        # Group by language
        lang_groups = defaultdict(list)
        for repo in self.repos:
            if repo.get("fork") or repo.get("size", 0) == 0:
                continue
            lang = repo.get("language") or "None"
            lang_groups[lang].append(repo["full_name"])
        
        for lang, repos in sorted(lang_groups.items(), key=lambda x: -len(x[1])):
            if len(repos) >= 3:
                patterns.append({
                    "type": "language_cluster",
                    "language": lang,
                    "count": len(repos),
                    "repos": repos[:5],
                    "opportunity": f"Shared CI template for {lang} repos" if len(repos) >= 5 else None,
                })
        
        # Group by staleness
        stale_repos = [s["repo"] for s in self.report.get("stale", [])]
        if len(stale_repos) >= 3:
            patterns.append({
                "type": "stale_cluster",
                "count": len(stale_repos),
                "repos": stale_repos[:5],
                "opportunity": "Consider archiving stale repos or updating dependencies",
            })
        
        return patterns
    
    def generate_report(self):
        """Generate full fleet health report."""
        scan = self.full_scan()
        gaps = self.gap_analysis()
        patterns = self.find_patterns()
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan": {k: v for k, v in scan.items() if not k.startswith("score")},
            "scores": dict(scan.get("score_distribution", {})),
            "gaps": gaps,
            "gaps_by_severity": {
                "high": sum(1 for g in gaps if g["severity"] == "high"),
                "medium": sum(1 for g in gaps if g["severity"] == "medium"),
                "low": sum(1 for g in gaps if g["severity"] == "low"),
            },
            "patterns": patterns,
            "summary": {
                "fleet_health": f"{scan['non_forks']} repos, {len(gaps)} gaps found",
                "top_issue": max(
                    [("missing_readme", len(scan.get("missing_readme", []))),
                     ("missing_ci", len(scan.get("missing_ci", []))),
                     ("missing_license", len(scan.get("missing_license", []))),
                     ("empty", len(scan.get("empty", [])))],
                    key=lambda x: x[1]
                )[0] if gaps else "none",
            },
        }
        
        # Save report
        with open(REPORT_FILE, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Submit summary tile to PLATO
        plato_post({
            "room": "scout-reports",
            "domain": "fleet-health",
            "question": f"What is the fleet health status as of {report['timestamp'][:10]}?",
            "answer": f"Fleet: {scan['non_forks']} non-fork repos. Gaps: {len(gaps)} total ({report['gaps_by_severity']['high']} high, {report['gaps_by_severity']['medium']} medium, {report['gaps_by_severity']['low']} low). Top issue: {report['summary']['top_issue']}. Score distribution: {dict(scan.get('score_distribution', {}))}",
            "confidence": 0.85,
            "source": "scout-agent",
            "tags": ["fleet-health", "gap-analysis"],
        })
        
        self.report_data = report
        return report


class ScoutHandler(BaseHTTPRequestHandler):
    """HTTP handler for Scout Agent."""
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str, ensure_ascii=False).encode())
    
    def do_GET(self):
        scout = FleetScout()
        
        if self.path == "/scan":
            print("Scout: full fleet scan...")
            result = scout.full_scan()
            summary = {k: v for k, v in result.items() if isinstance(v, (int, str, list))}
            summary["score_distribution"] = dict(result.get("score_distribution", {}))
            self._json({"status": "scanned", "findings": summary})
        
        elif self.path == "/gaps":
            print("Scout: gap analysis...")
            result = scout.full_scan()
            gaps = scout.gap_analysis()
            self._json({"status": "analyzed", "gaps": gaps, "total": len(gaps)})
        
        elif self.path == "/patterns":
            print("Scout: pattern detection...")
            result = scout.full_scan()
            patterns = scout.find_patterns()
            self._json({"status": "analyzed", "patterns": patterns})
        
        elif self.path == "/report":
            print("Scout: generating full report...")
            report = scout.generate_report()
            self._json({"status": "reported", "report": report})
        
        elif self.path == "/health":
            self._json({"status": "healthy", "service": "scout-agent"})
        
        elif self.path == "/latest":
            try:
                with open(REPORT_FILE) as f:
                    self._json(json.load(f))
            except:
                self._json({"status": "no report yet — hit /report first"})
        
        else:
            self._json({
                "service": "scout-agent",
                "endpoints": ["/scan", "/gaps", "/patterns", "/report", "/latest", "/health"],
            })
    
    def log_message(self, format, *args):
        print(f"[Scout] {args[0]}" if args else "")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4052
    print(f"🔍 Scout Agent starting on http://localhost:{port}")
    print(f"   Endpoints: /scan, /gaps, /patterns, /report, /health")
    server = HTTPServer(("0.0.0.0", port), ScoutHandler)
    server.serve_forever()
