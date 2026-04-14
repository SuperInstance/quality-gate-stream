#!/usr/bin/env python3
"""
Deep repo analyzer — uses z.ai models to understand a codebase.
Usage: python3 analyze_repo.py /path/to/repo
"""
import os, sys, json, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
from batch import call_zai

def get_tree(repo_path, max_depth=3, max_files=200):
    """Get directory tree as text."""
    result = []
    count = 0
    for root, dirs, files in os.walk(repo_path):
        depth = root.replace(repo_path, "").count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', '.mypy_cache', 'dist', 'build', '.next', 'target', 'venv')]
        indent = " " * 2 * depth
        result.append(f"{indent}{os.path.basename(root)}/")
        for f in sorted(files)[:20]:
            if count >= max_files:
                result.append(f"{indent}  ... (truncated)")
                return "\n".join(result)
            result.append(f"{indent}  {f}")
            count += 1
    return "\n".join(result)

def get_stats(repo_path):
    """Get file type stats."""
    types = {}
    total = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', 'dist', 'build', 'target')]
        for f in files:
            ext = f.rsplit('.', 1)[-1] if '.' in f else 'none'
            types[ext] = types.get(ext, 0) + 1
            total += 1
    return total, dict(sorted(types.items(), key=lambda x: -x[1])[:15])

def get_readme(repo_path):
    """Get README content."""
    for name in ['README.md', 'README.txt', 'README']:
        p = Path(repo_path) / name
        if p.exists():
            return p.read_text(errors='ignore')[:4000]
    return ""

def get_package_info(repo_path):
    """Get package/dependency info."""
    info = {}
    pkg = Path(repo_path) / "package.json"
    if pkg.exists():
        d = json.loads(pkg.read_text())
        info["npm_name"] = d.get("name", "")
        info["npm_version"] = d.get("version", "")
        info["npm_deps"] = len(d.get("dependencies", {}))
        info["scripts"] = list(d.get("scripts", {}).keys())
    pyproj = Path(repo_path) / "pyproject.toml"
    if pyproj.exists():
        info["pyproject"] = True
    cargo = Path(repo_path) / "Cargo.toml"
    if cargo.exists():
        info["cargo"] = True
    return info

def analyze(repo_path):
    repo_path = os.path.abspath(repo_path)
    name = os.path.basename(repo_path)
    
    print(f"Analyzing {name}...")
    total, types = get_stats(repo_path)
    tree = get_tree(repo_path)
    readme = get_readme(repo_path)
    pkg = get_package_info(repo_path)
    
    # Build analysis prompt
    prompt = f"""Analyze this codebase and provide:
1. **Purpose** — What does it do? (2-3 sentences)
2. **Architecture** — How is it structured? Key modules and their roles.
3. **Tech Stack** — Languages, frameworks, key dependencies.
4. **Maturity** — How production-ready is it? (prototype/MVP/production)
5. **Strengths** — What's done well?
6. **Gaps** — What's missing or could be improved?
7. **Connections** — What other SuperInstance/Lucineer repos would this integrate with?

Repo: {name}
Files: {total}
Types: {json.dumps(types)}
Package: {json.dumps(pkg)}

Directory tree:
{tree}

README excerpt:
{readme[:2000]}"""

    result = call_zai(prompt, model="glm-4.7", max_tokens=4096)
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_repo.py /path/to/repo")
        sys.exit(1)
    
    result = analyze(sys.argv[1])
    print(result)
    
    # Save
    name = os.path.basename(sys.argv[1])
    out = Path("/home/ubuntu/.openclaw/workspace/scripts/output/repo_analysis")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{name}.md", "w") as f:
        f.write(f"# {name} Analysis\n\n{result}")
    print(f"\nSaved to {out / name}.md")
