#!/usr/bin/env python3
"""Agent Bootcamp Engine — Spiral training for git-agents

Scans a project, generates challenges from weak spots,
runs dojo sessions against agent variants, and manages blind tests.

Usage:
  python3 bootcamp.py --repo /path/to/project --cadet navigator
  python3 bootcamp.py --repo /path/to/project --cadet navigator --day 3
  python3 bootcamp.py --dojo-only --cadet navigator --difficulty 7
"""

import json
import os
import sys
import time
import subprocess
import urllib.request
import ssl
import ast
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

# API setup
DSKEY = os.environ.get("DEEPSEEK_KEY", "[DEEPSEEK_KEY_REDACTED]")
SFKEY = os.environ.get("SILICONFLOW_KEY", "[SF_KEY_REDACTED]")
ctx = ssl.create_default_context()

@dataclass
class WeakSpot:
    path: str
    function_name: str
    kind: str  # untested, undocumented, long, missing_error_handling, dead_code
    severity: int  # 1-10
    context: str

@dataclass
class Challenge:
    target: WeakSpot
    task: str
    difficulty: int
    time_limit_minutes: float
    verification: str
    blind: bool = False

@dataclass
class Estimate:
    minutes: float
    confidence: float
    similar_tasks: int = 0
    calibration: float = 1.0

@dataclass
class TaskEstimator:
    history: List[Dict] = field(default_factory=list)
    calibration: float = 1.0
    
    def estimate(self, task: str, context: dict) -> Estimate:
        similar = [h for h in self.history if h.get("kind") == context.get("kind")]
        if similar:
            base = sum(h["actual"] for h in similar) / len(similar)
        else:
            base = 10
        
        multiplier = 1.0
        if context.get("unfamiliar"):
            multiplier *= 1.5
        if context.get("cross_language"):
            multiplier *= 2.0
        
        minutes = base * multiplier * self.calibration
        confidence = min(len(similar) / 10, 0.95)
        return Estimate(minutes=minutes, confidence=confidence, similar_tasks=len(similar), calibration=self.calibration)
    
    def calibrate(self, task: str, kind: str, estimated: float, actual: float):
        self.history.append({"task": task[:50], "kind": kind, "estimated": estimated, "actual": actual})
        if actual > estimated:
            self.calibration *= 1.05
        else:
            self.calibration *= 0.97
        self.calibration = max(0.5, min(2.0, self.calibration))


class ProjectScanner:
    """Scans a project repo to find weak spots."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def scan(self) -> List[WeakSpot]:
        weak_spots = []
        weak_spots.extend(self._find_untested())
        weak_spots.extend(self._find_undocumented())
        weak_spots.extend(self._find_long_functions())
        weak_spots.extend(self._find_missing_error_handling())
        return sorted(weak_spots, key=lambda w: w.severity, reverse=True)
    
    def _find_untested(self) -> List[WeakSpot]:
        """Find functions without corresponding tests."""
        spots = []
        test_dir = self.repo_path / "tests"
        src_files = list(self.repo_path.glob("src/**/*.py")) + list(self.repo_path.glob("**/*.rs")) + list(self.repo_path.glob("**/*.go"))
        
        for src in src_files[:20]:  # limit scan
            if "test" in str(src):
                continue
            content = src.read_text(errors="ignore")
            # Find function definitions
            funcs = re.findall(r'(?:def|fn|func)\s+(\w+)', content)
            for func in funcs[:5]:
                # Check if test exists
                has_test = False
                if test_dir.exists():
                    for test_file in test_dir.glob("*"):
                        if func in test_file.read_text(errors="ignore"):
                            has_test = True
                            break
                if not has_test:
                    spots.append(WeakSpot(
                        path=str(src.relative_to(self.repo_path)),
                        function_name=func,
                        kind="untested",
                        severity=7,
                        context=content[:200]
                    ))
        return spots[:10]
    
    def _find_undocumented(self) -> List[WeakSpot]:
        """Find functions without docstrings."""
        spots = []
        py_files = list(self.repo_path.glob("src/**/*.py"))[:20]
        for src in py_files:
            content = src.read_text(errors="ignore")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if re.match(r'^def\s+\w+', line.strip()):
                    # Check next line for docstring
                    if i + 1 < len(lines) and not lines[i+1].strip().startswith('"""'):
                        func_name = re.search(r'def\s+(\w+)', line).group(1)
                        if func_name.startswith("_"):
                            continue
                        spots.append(WeakSpot(
                            path=str(src.relative_to(self.repo_path)),
                            function_name=func_name,
                            kind="undocumented",
                            severity=4,
                            context=line
                        ))
        return spots[:10]
    
    def _find_long_functions(self) -> List[WeakSpot]:
        """Find functions over 50 lines."""
        spots = []
        py_files = list(self.repo_path.glob("src/**/*.py"))[:20]
        for src in py_files:
            content = src.read_text(errors="ignore")
            lines = content.split("\n")
            func_start = None
            func_name = None
            for i, line in enumerate(lines):
                if re.match(r'^def\s+\w+', line.strip()):
                    if func_start and func_name:
                        length = i - func_start
                        if length > 50:
                            spots.append(WeakSpot(
                                path=str(src.relative_to(self.repo_path)),
                                function_name=func_name,
                                kind="long_function",
                                severity=min(length // 10, 10),
                                context=f"{length} lines"
                            ))
                    func_start = i
                    func_name = re.search(r'def\s+(\w+)', line).group(1)
        return spots[:5]
    
    def _find_missing_error_handling(self) -> List[WeakSpot]:
        """Find functions with try/except missing."""
        spots = []
        py_files = list(self.repo_path.glob("src/**/*.py"))[:20]
        for src in py_files:
            content = src.read_text(errors="ignore")
            if "urlopen" in content or "open(" in content or "requests." in content:
                if "try:" not in content and "except" not in content:
                    spots.append(WeakSpot(
                        path=str(src.relative_to(self.repo_path)),
                        function_name=Path(src).stem,
                        kind="missing_error_handling",
                        severity=6,
                        context="Has I/O without try/except"
                    ))
        return spots[:5]


class ChallengeGenerator:
    """Generates challenges from weak spots with spiraling difficulty."""
    
    def __init__(self, estimator: TaskEstimator):
        self.estimator = estimator
        self.topic_rotation = ["testing", "documentation", "refactoring", "integration", "debugging"]
        self.current_topic = 0
        self.difficulty = 1
    
    def generate(self, weak_spots: List[WeakSpot], count: int = 5) -> List[Challenge]:
        challenges = []
        for _ in range(count):
            if not weak_spots:
                break
            spot = weak_spots[len(challenges) % len(weak_spots)]
            topic = self.topic_rotation[self.current_topic % len(self.topic_rotation)]
            self.current_topic += 1
            
            task = self._format_task(spot, topic, self.difficulty)
            est = self.estimator.estimate(task, {"kind": spot.kind, "unfamiliar": self.difficulty > 5})
            
            challenges.append(Challenge(
                target=spot,
                task=task,
                difficulty=self.difficulty,
                time_limit_minutes=est.minutes,
                verification=f"Run tests for {spot.function_name}",
                blind=self.difficulty >= 4,
            ))
            
            self.difficulty = min(self.difficulty + 1, 10)
        
        return challenges
    
    def _format_task(self, spot: WeakSpot, topic: str, difficulty: int) -> str:
        templates = {
            ("testing", 1): f"Write a basic test for `{spot.function_name}` in {spot.path}",
            ("testing", 4): f"Write edge case tests for `{spot.function_name}` — test empty input, None, overflow, and wrong types",
            ("testing", 7): f"Property-based test `{spot.function_name}` — find invariants and test them with 100 random inputs",
            ("documentation", 1): f"Add a docstring to `{spot.function_name}` explaining what it does",
            ("documentation", 4): f"Document `{spot.function_name}` with: purpose, args, returns, raises, and a usage example",
            ("documentation", 7): f"Write an architecture doc for the module containing `{spot.function_name}` — explain the design decisions",
            ("refactoring", 1): f"Simplify `{spot.function_name}` — remove any obvious redundancy",
            ("refactoring", 4): f"Split `{spot.function_name}` into smaller functions, each doing one thing. Maintain all existing behavior.",
            ("refactoring", 7): f"Redesign the interface around `{spot.function_name}` — propose a better API that handles the same cases with less code",
            ("integration", 1): f"Check if `{spot.function_name}` is called from anywhere else in the project",
            ("integration", 4): f"Connect `{spot.function_name}` to the test suite and CI pipeline. Make it testable in isolation.",
            ("integration", 7): f"Build a bridge between the module containing `{spot.function_name}` and another module. Handle the interface mismatch.",
            ("debugging", 1): f"Read `{spot.function_name}` and list anything that could go wrong",
            ("debugging", 4): f"Add defensive checks to `{spot.function_name}` — what if inputs are wrong? What if the network is down?",
            ("debugging", 7): f"Find the latent bug in `{spot.function_name}` — there IS one. Fix it, add a test that proves the old code was wrong.",
        }
        
        # Find closest difficulty match
        for d in range(difficulty, 0, -1):
            key = (topic, d)
            if key in templates:
                return templates[key]
        return templates.get((topic, 1), f"Work on {spot.function_name}")


class DojoSession:
    """Pits an agent against variants of itself."""
    
    def __init__(self, cadet_id: str, cadet_model: str = "deepseek-chat"):
        self.cadet_id = cadet_id
        self.cadet_model = cadet_model
        self.variants = [
            ("Twin-A", cadet_model, 0.0, True),   # same everything
            ("Twin-B", cadet_model, 0.7, True),   # higher temp
            ("Twin-C", cadet_model, 0.0, False),  # no context
            ("Twin-D", "Qwen/Qwen3-Coder-30B-A3B-Instruct", 0.0, True),  # different model
            ("Twin-E", "Qwen/Qwen3-Coder-30B-A3B-Instruct", 0.9, False),  # wild card
        ]
    
    def run(self, challenge: Challenge, cadet_context: str = "") -> Dict:
        """Run dojo: all variants attempt the challenge."""
        results = {}
        
        for name, model, temp, use_context in self.variants:
            url = "https://api.deepseek.com/chat/completions"
            key = DSKEY
            if model.startswith("Qwen") or model.startswith("ByteDance"):
                url = "https://api.siliconflow.com/v1/chat/completions"
                key = SFKEY
            
            messages = []
            if use_context and cadet_context:
                messages.append({"role": "system", "content": f"Project context: {cadet_context[:500]}"})
            messages.append({"role": "user", "content": challenge.task})
            
            body = json.dumps({"model": model, "messages": messages, "max_tokens": 500, "temperature": temp}).encode()
            req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            
            try:
                d = json.loads(urllib.request.urlopen(req, timeout=30, context=ctx).read())
                response = d["choices"][0]["message"]["content"]
                results[name] = {"response": response[:300], "tokens": d.get("usage", {}).get("total_tokens", 0)}
            except Exception as e:
                results[name] = {"error": str(e)}
            
            time.sleep(0.3)
        
        return results


class BlindTestRunner:
    """Manages blind tests — agent submits, verifies later."""
    
    def __init__(self, state_file: str = "/tmp/blind_tests.json"):
        self.state_file = state_file
        self.tests = {}
        if os.path.exists(state_file):
            with open(state_file) as f:
                self.tests = json.load(f)
    
    def submit(self, agent_id: str, challenge_id: str, work: str) -> str:
        token = f"{agent_id}-{challenge_id}-{int(time.time())}"
        self.tests[token] = {
            "agent_id": agent_id,
            "challenge_id": challenge_id,
            "work": work[:500],
            "submitted": datetime.utcnow().isoformat(),
            "status": "pending",
        }
        self._save()
        return token
    
    def verify(self, token: str, passed: bool, details: str = ""):
        if token in self.tests:
            self.tests[token]["status"] = "pass" if passed else "fail"
            self.tests[token]["details"] = details
            self.tests[token]["verified"] = datetime.utcnow().isoformat()
            self._save()
    
    def pickup(self, agent_id: str) -> List[Dict]:
        return [t for t in self.tests.values() if t["agent_id"] == agent_id and t["status"] != "pending"]
    
    def _save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.tests, f, indent=2, default=str)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Bootcamp Engine")
    parser.add_argument("--repo", required=True, help="Path to project repo")
    parser.add_argument("--cadet", required=True, help="Cadet agent ID")
    parser.add_argument("--day", type=int, default=1, help="Bootcamp day (1-7+)")
    parser.add_argument("--dojo-only", action="store_true", help="Run only dojo session")
    parser.add_argument("--difficulty", type=int, default=1, help="Starting difficulty")
    parser.add_argument("--challenges", type=int, default=5, help="Number of challenges to generate")
    args = parser.parse_args()
    
    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║  AGENT BOOTCAMP — Day {args.day}                        ║")
    print(f"║  Cadet: {args.cadet:40s}  ║")
    print(f"║  Repo: {args.repo[:42]:42s}  ║")
    print(f"╚══════════════════════════════════════════════════╝\n")
    
    estimator = TaskEstimator()
    scanner = ProjectScanner(args.repo)
    generator = ChallengeGenerator(estimator)
    generator.difficulty = args.difficulty
    
    if not args.dojo_only:
        # Scan project
        print("🔍 Scanning project for weak spots...")
        weak_spots = scanner.scan()
        print(f"   Found {len(weak_spots)} weak spots:")
        for ws in weak_spots[:10]:
            print(f"   - [{ws.severity}/10] {ws.kind}: {ws.function_name} in {ws.path}")
        
        # Generate challenges
        print(f"\n📋 Generating {args.challenges} challenges (difficulty {args.difficulty}+)...")
        challenges = generator.generate(weak_spots, count=args.challenges)
        for i, ch in enumerate(challenges):
            est = estimator.estimate(ch.task, {"kind": ch.target.kind})
            blind_tag = "🔒 BLIND" if ch.blind else "👀 OPEN"
            print(f"\n   Challenge {i+1} [{blind_tag}] (difficulty {ch.difficulty}, ~{est.minutes:.0f}min):")
            print(f"   {ch.task}")
    
    # Dojo
    print(f"\n🥋 Dojo Session — {args.cadet} vs 5 variants")
    dojo = DojoSession(args.cadet)
    if challenges:
        print(f"   Using challenge: {challenges[0].task[:60]}...")
        results = dojo.run(challenges[0])
        for name, result in results.items():
            if "error" in result:
                print(f"   {name}: ❌ {result['error'][:50]}")
            else:
                print(f"   {name}: {result.get('tokens',0)} tokens — {result.get('response','')[:60]}...")
    
    print(f"\n{'═'*50}")
    print(f"Bootcamp Day {args.day} complete.")
    print(f"Difficulty reached: {generator.difficulty}")
    print(f"Estimator calibration: {estimator.calibration:.2f}x")
    
    # Save state
    state = {
        "cadet": args.cadet,
        "repo": args.repo,
        "day": args.day,
        "difficulty": generator.difficulty,
        "calibration": estimator.calibration,
        "history_count": len(estimator.history),
        "timestamp": datetime.utcnow().isoformat(),
    }
    state_file = f"/tmp/bootcamp-{args.cadet}-state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State saved: {state_file}")


if __name__ == "__main__":
    main()
