#!/usr/bin/env python3
"""
Zeroclaw Bottle Protocol — Agent-to-agent discovery and sharing.

Each zeroclaw can:
1. READ other agents' work/ directories
2. WRITE bottles to other agents' bottles/ directories
3. DISCOVER relevant work via tag matching
4. RESPOND to bottles from other agents

Bottles are git-committed, so they persist across restarts.
"""
import json, os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

SHELLS_DIR = Path("/tmp/zeroclaw-shells")

AGENT_NAMES = [
    "zc-navigator-shell", "zc-sentinel-shell", "zc-scribe-shell",
    "zc-tinker-shell", "zc-scout-shell", "zc-curator-shell",
    "zc-mason-shell", "zc-alchemist-shell", "zc-herald-shell",
    "zc-scholar-shell", "zc-weaver-shell", "zc-archivist-shell",
]

FRIENDLY = {
    "zc-navigator-shell": "Navigator",
    "zc-sentinel-shell": "Sentinel",
    "zc-scribe-shell": "Scribe",
    "zc-tinker-shell": "Tinker",
    "zc-scout-shell": "Scout",
    "zc-curator-shell": "Curator",
    "zc-mason-shell": "Mason",
    "zc-alchemist-shell": "Alchemist",
    "zc-herald-shell": "Herald",
    "zc-scholar-shell": "Scholar",
    "zc-weaver-shell": "Weaver",
    "zc-archivist-shell": "Archivist",
}


def send_bottle(from_agent: str, to_agent: str, topic: str, content: str, tags: list = None):
    """Send a bottle from one agent to another."""
    bottle = {
        "from": FRIENDLY.get(from_agent, from_agent),
        "to": FRIENDLY.get(to_agent, to_agent),
        "topic": topic,
        "content": content,
        "tags": tags or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": hashlib.sha256(content.encode()).hexdigest()[:12],
    }
    
    # Write to recipient's bottles/incoming/
    bottles_dir = SHELLS_DIR / to_agent / "bottles" / "incoming"
    bottles_dir.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    fname = f"{ts}_{bottle['hash']}.json"
    (bottles_dir / fname).write_text(json.dumps(bottle, indent=2))
    
    return bottle


def read_bottles(agent: str) -> list:
    """Read incoming bottles for an agent."""
    bottles_dir = SHELLS_DIR / agent / "bottles" / "incoming"
    if not bottles_dir.exists():
        return []
    
    bottles = []
    for f in sorted(bottles_dir.glob("*.json")):
        try:
            bottles.append(json.loads(f.read_text()))
        except:
            pass
    return bottles


def discover_work(query_tags: list = None, limit: int = 5) -> list:
    """Discover relevant work from other agents based on tags."""
    if not query_tags:
        return []
    
    query_set = set(t.lower() for t in query_tags)
    discoveries = []
    
    for agent_dir in SHELLS_DIR.glob("zc-*-shell"):
        work_dir = agent_dir / "work"
        if not work_dir.exists():
            continue
        
        agent_name = FRIENDLY.get(agent_dir.name, agent_dir.name)
        
        for f in sorted(work_dir.glob("*.md"))[-10:]:
            content = f.read_text()
            content_lower = content.lower()
            
            # Check tag overlap
            matches = sum(1 for t in query_set if t in content_lower)
            if matches >= 2:
                discoveries.append({
                    "agent": agent_name,
                    "file": f.name,
                    "preview": content[:200],
                    "tag_matches": matches,
                })
    
    # Sort by relevance
    discoveries.sort(key=lambda x: -x["tag_matches"])
    return discoveries[:limit]


def route_bottles():
    """Auto-route: scan agent work for relevant cross-agent discoveries."""
    routed = 0
    
    for agent_dir in SHELLS_DIR.glob("zc-*-shell"):
        agent = agent_dir.name
        friendly = FRIENDLY.get(agent, agent)
        
        # Read agent's state for current interests
        state_file = agent_dir / "STATE.md"
        if not state_file.exists():
            continue
        
        state = state_file.read_text().lower()
        
        # Extract topic keywords from state
        topics = []
        for keyword in ["deadband", "testing", "documentation", "integration", 
                        "categoriz", "health", "communication", "trend", "research",
                        "prototype", "memory", "constraint"]:
            if keyword in state:
                topics.append(keyword)
        
        if not topics:
            continue
        
        # Discover relevant work from OTHER agents
        discoveries = discover_work(topics, limit=3)
        
        for disc in discoveries:
            if disc["agent"] == friendly:
                continue  # Skip self
            
            # Send bottle
            bottle = send_bottle(
                from_agent="zc-herald-shell",  # Herald routes
                to_agent=agent,
                topic=f"Discovery: {disc['agent']} found something relevant",
                content=f"Agent {disc['agent']} wrote about topics matching your interests:\n\n"
                       f"File: {disc['file']}\n"
                       f"Preview: {disc['preview'][:150]}...\n\n"
                       f"Tags matched: {disc['tag_matches']}",
                tags=topics,
            )
            routed += 1
    
    return routed


if __name__ == "__main__":
    print("📯 ZEROCLOW BOTTLE PROTOCOL")
    
    # Route bottles based on interest matching
    routed = route_bottles()
    print(f"  Routed {routed} discovery bottles")
    
    # Show incoming bottles per agent
    print("\n  INCOMING BOTTLES:")
    for agent_dir in sorted(SHELLS_DIR.glob("zc-*-shell")):
        agent = agent_dir.name
        friendly = FRIENDLY.get(agent, agent)
        bottles = read_bottles(agent)
        if bottles:
            print(f"    {friendly}: {len(bottles)} bottles")
            for b in bottles[:2]:
                print(f"      From {b['from']}: {b['topic'][:50]}")
    
    print(f"\n  ✅ Bottle protocol active")
