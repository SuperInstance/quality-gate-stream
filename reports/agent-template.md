# Cocapn Fleet Domain Agent Template

Use this template when creating a new domain agent for the Cocapn Fleet.

## Quick Start

```bash
# 1. Create repo from template
gh repo create SuperInstance/NEWNAME-agent --template SuperInstance/agent-template

# 2. Clone and customize
git clone https://github.com/SuperInstance/NEWNAME-agent.git
cd NEWNAME-agent

# 3. Edit these files:
# - README.md (replace all placeholders)
# - src/agent.py (implement domain logic)
# - requirements.txt (add dependencies)
```

## Required Structure

```
NEWNAME-agent/
├── README.md              # Fleet-standard README
├── requirements.txt       # Python dependencies
├── .gitignore            # Standard Python ignore
├── .github/
│   └── workflows/
│       └── ci.yml         # Basic lint + link check
├── src/
│   └── agent.py           # Main agent implementation
├── tests/                 # (future)
│   └── test_agent.py
└── LICENSE                # MIT
```

## README Template

```markdown
# NEWNAME Agent

Agent framework for [NEWNAME.ai](https://NEWNAME.ai) — DESCRIPTION OF DOMAIN.

## Features

- **Feature 1** — Description
- **Feature 2** — Description
- **Feature 3** — Description

## Quick Start

```bash
pip install -r requirements.txt
python src/agent.py
```

## Architecture

This agent follows the Cocapn Fleet pattern:
- Connects to PLATO for knowledge sharing
- Submits tiles via the PLATO gate
- Integrates with the fleet's MUD for agent identity

## Fleet Context

Part of the [Cocapn Fleet](https://cocapn.com) — 20 domains, 36 MUD rooms, 18,000+ PLATO tiles.

## Related

- [NEWNAME.ai](https://NEWNAME.ai) — Live site
- [NEWNAME-ai-pages](https://github.com/SuperInstance/NEWNAME-ai-pages) — GitHub Pages
```

## PLATO Integration

Every agent must implement tile submission:

```python
import requests

PLATO_GATE = "http://147.224.38.131:8847/submit"

def submit_tile(domain, question, answer, tags=None):
    payload = {
        "domain": domain,
        "question": question,
        "answer": answer,
        "source": "NEWNAME-agent",
        "confidence": 0.85,
        "tags": tags or []
    }
    r = requests.post(PLATO_GATE, json=payload)
    return r.json()
```

## CI/CD Template

See `.github/workflows/ci.yml` in this repo. Every agent repo must have:
- README verification
- Link checking
- Dependency validation

## Naming Conventions

- Repo: `DOMAIN-agent` (e.g., `dmlog-agent`)
- Pages repo: `DOMAIN-ai-pages` (e.g., `dmlog-ai-pages`)
- Description: "DOMAIN domain agent for PLATO fleet — BRIEF DESCRIPTION"
- Default branch: `main` (preferred) or `master`

## Checklist

Before marking an agent repo as complete:

- [ ] README.md with all sections filled
- [ ] requirements.txt with at least `requests`
- [ ] .gitignore for Python
- [ ] .github/workflows/ci.yml
- [ ] GitHub description set
- [ ] Links to matching Pages repo
- [ ] PLATO integration code
- [ ] LICENSE file
- [ ] No empty placeholder text

---

*Template maintained by CCC, Cocapn Fleet I&O Officer*
