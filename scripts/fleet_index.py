#!/usr/bin/env python3
"""
Fleet Index Generator — builds a static HTML page showing all categorized repos.
Run periodically to keep it fresh.
"""

import json, os, time
from collections import Counter

DATA_FILE = "/home/ubuntu/.openclaw/workspace/data/fleet-categorization.json"
OUTPUT_FILE = "/tmp/fleet-index.html"

def build_index():
    with open(DATA_FILE) as f:
        categorized = json.load(f)
    
    # Collect non-fork repos
    repos = []
    for owner, owner_repos in categorized.items():
        for name, info in owner_repos.items():
            if info.get("fork"):
                continue
            repos.append({
                "owner": owner,
                "name": name,
                "domain": info["primary_domain"],
                "all_domains": info.get("all_domains", []),
                "language": info.get("language"),
                "description": info.get("description") or "",
                "updated": info.get("updated", ""),
                "stars": info.get("stars", 0),
            })
    
    # Domain stats
    domain_counts = Counter(r["domain"] for r in repos)
    lang_counts = Counter(r["language"] for r in repos if r["language"])
    
    # Build HTML
    domain_order = [d for d, _ in domain_counts.most_common()]
    
    sections = ""
    for domain in domain_order:
        domain_repos = sorted(
            [r for r in repos if r["domain"] == domain],
            key=lambda x: (-x["stars"], x["name"])
        )
        rows = ""
        for r in domain_repos:
            lang_badge = f'<span class="lang">{r["language"]}</span>' if r["language"] else ""
            desc = r["description"][:80] + ("..." if len(r["description"]) > 80 else "")
            rows += f"""
            <tr>
                <td><a href="https://github.com/{r['owner']}/{r['name']}">{r['name']}</a></td>
                <td class="owner">{r['owner']}</td>
                <td>{desc}</td>
                <td>{lang_badge}</td>
                <td class="dim">{r['updated']}</td>
            </tr>"""
        
        sections += f"""
        <h2 id="{domain}">{domain} <span class="count">{domain_counts[domain]}</span></h2>
        <table>
            <tr><th>Repo</th><th>Owner</th><th>Description</th><th>Lang</th><th>Updated</th></tr>
            {rows}
        </table>"""
    
    nav = " | ".join(f'<a href="#{d}">{d} ({domain_counts[d]})</a>' for d in domain_order)
    
    lang_bars = ""
    for lang, count in lang_counts.most_common(10):
        pct = count * 100 // len(repos)
        lang_bgs = {"Python": "#3572A5", "Rust": "#dea584", "TypeScript": "#2b7489", "Go": "#00ADD8", "Shell": "#89e051"}
        bg = lang_bgs.get(lang, "#666")
        lang_bars += f'<span class="lang-bar" style="background:{bg};width:{pct}%">{lang} {pct}%</span>\n'
    
    html = f"""<!DOCTYPE html>
<html><head>
<title>Cocapn Fleet Index</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{background:#0a0a0f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:1.5em;max-width:1200px}}
h1{{color:#4fc3f7;border-bottom:2px solid #1a1a2e;padding-bottom:.4em}}
h2{{color:#7c4dff;margin-top:1.5em;font-size:1.1em}}
.count{{color:#888;font-size:.8em}}
nav{{background:#12121a;border-radius:8px;padding:.8em;margin:1em 0;font-size:.85em;line-height:2}}
nav a{{color:#4fc3f7;text-decoration:none;margin-right:.5em}}
nav a:hover{{text-decoration:underline}}
table{{width:100%;border-collapse:collapse;margin-top:.3em}}
th{{text-align:left;color:#4fc3f7;font-size:.8em;padding:.4em;border-bottom:1px solid #1a1a2e}}
td{{padding:.35em .4em;font-size:.85em;border-bottom:1px solid #0d0d12}}
td a{{color:#7c4dff;text-decoration:none}}
td a:hover{{text-decoration:underline}}
.owner{{color:#888;font-size:.8em}}
.dim{{color:#555;font-size:.8em}}
.lang{{background:#1a1a2e;padding:.1em .4em;border-radius:3px;font-size:.75em;color:#aaa}}
.lang-bar{{display:inline-block;padding:.15em .4em;margin:.1em;border-radius:3px;font-size:.75em;color:#fff;min-width:30px;text-align:center}}
.stats{{display:flex;gap:1.5em;margin:1em 0;flex-wrap:wrap}}
.stat{{text-align:center}}
.stat .value{{font-size:1.6em;color:#7c4dff;font-weight:bold}}
.stat .label{{color:#888;font-size:.8em}}
.footer{{margin-top:2em;color:#444;font-size:.75em;text-align:center}}
</style>
</head><body>
<h1>🦀 Cocapn Fleet Index</h1>

<div class="stats">
    <div class="stat"><div class="value">{len(repos)}</div><div class="label">Repos</div></div>
    <div class="stat"><div class="value">{len(domain_counts)}</div><div class="label">Domains</div></div>
    <div class="stat"><div class="value">{len(lang_counts)}</div><div class="label">Languages</div></div>
    <div class="stat"><div class="value">{sum(1 for r in repos if r['owner']=='SuperInstance')}</div><div class="label">SuperInstance</div></div>
    <div class="stat"><div class="value">{sum(1 for r in repos if r['owner']=='cocapn')}</div><div class="label">cocapn</div></div>
    <div class="stat"><div class="value">{sum(1 for r in repos if r['owner']=='Lucineer')}</div><div class="label">Lucineer</div></div>
</div>

<div style="margin:1em 0">{lang_bars}</div>

<nav>{nav}</nav>

{sections}

<div class="footer">
    Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by Oracle1 🔮 &mdash; 
    <a href="https://github.com/SuperInstance/oracle1-workspace">workspace</a>
</div>
</body></html>"""
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    
    print(f"Fleet index built: {len(repos)} repos, {len(domain_counts)} domains → {OUTPUT_FILE}")

if __name__ == "__main__":
    build_index()
