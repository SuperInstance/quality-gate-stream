# cocapn Analysis

# Cocapn Analysis

## 1. Purpose
Cocapn is an open-source agent framework where "the repository IS the agent" — every repo you create is a self-contained AI entity that remembers, learns, and grows. It uses a dual-repo pattern: a private brain (memory, personality, secrets) and a public face (website, domain), with Git serving as the database for persistent state.

## 2. Architecture
**Monorepo Structure** with 8 core packages:
- `cli` — Command-line tool for agent management
- `ui` / `ui-minimal` — React-based chat interfaces (Vite + Tailwind)
- `local-bridge` — Local execution runtime
- `cloud-agents` — Cloudflare Workers deployment (wrangler)
- `protocols` — A2A (agent-to-agent) communication schemas
- `create-cocapn` — Template scaffolding CLI
- `modules` — Pluggable extensions (search, zotero, habits)
- `templates` — Pre-built agent configurations

**Core Concepts:**
- `soul.md` — Agent personality definition
- JSON schemas for memory facts, agent definitions, module manifests
- Fleet protocol for multi-agent coordination

## 3. Tech Stack
| Category | Technologies |
|----------|-------------|
| Languages | TypeScript (373 files), JavaScript (24) |
| Frontend | React, Vite, Tailwind CSS, Playwright (e2e) |
| Backend | Cloudflare Workers, Miniflare, Docker |
| Tooling | npm, Vitest, ESLint, Prettier |
| CI/CD | GitHub Actions (ci, publish, review workflows) |
| Schemas | JSON Schema |

## 4. Maturity
**Early MVP / Prototype** — Version 0.1.0 with extensive documentation but minimal runtime dependencies (0 npm deps). Significant planning artifacts (roadmap files, architecture docs, design docs) suggest active development rather than production readiness. CI/CD is configured but coverage unknown.

## 5. Strengths
- **Novel Concept** — "Repo as agent" provides elegant persistence and versioning
- **Offline-First Design** — Git as database enables full ownership and portability
- **Comprehensive Documentation** — Extensive architecture, security, and workflow docs
- **Modular Architecture** — Clean package separation, plugin system, knowledge packs
- **Dual-Repo Security** — Separation of private brain from public face

## 6. Gaps
- **Zero Runtime Dependencies** — Suspicious for an AI framework; may be incomplete
- **Sparse Examples** — Only 2 example modules and minimal templates
- **Complex UX** — Two-repo pattern requires user coordination
- **Testing Evidence** — Test structure exists but results unclear
- **Production Hardening** — Security audits documented but not implemented
- **Performance Validation** — No benchmarks or scalability data

## 7. Connections
Likely integrations with SuperInstance/Lucineer ecosystem:
- **Template repositories** — Agent definitions, personalities, skill cartridges
- **Protocol specs** — A2A communication standards, fleet coordination
- **Module registry** — Perplexity, Zotero, and other extensions
- **Cloud infrastructure** — Workers deployment pipelines
- **UI component library** — Shared chat/magazine interfaces
- **Knowledge graph tools** — Memory fact management and retrieval

The `schemas/` directory suggests shared contracts with other tools, and the `.offline-queue.json` indicates eventual sync with external services.