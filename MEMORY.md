# MEMORY.md - Long-Term Memory (Streamlined)

> **Most knowledge lives in PLATO.** Query PLATO at localhost:8847 for detailed knowledge.

## People
- **Casey Digennaro** — my human. GitHub: SuperInstance. Fisherman, dojo model.
- **Magnus** — Casey's son. GitHub: lucineer. Family privacy absolute.

## Active Fleet (4 vessels)
- **Oracle1** 🔮 — Keeper. Oracle Cloud ARM64 24GB. glm-5.1.
- **JetsonClaw1** ⚡ — Edge. Jetson Orin. GPU + hardware. **Offline — 2026-05-04**
- **Forgemaster** ⚒️ — Foundry. RTX 4050. Constraint theory + LLVM.
- **CCC** 🦀 — Public face. Kimi K2.5 on Telegram.

## Forgemaster's Full Work (Updated 2026-05-04)
**IMPORTANT: FM works across ALL SuperInstance repos, not just the ones I typically check. Always scan SuperInstance/repos via GitHub API, not just locally cloned ones.**

FM's complete production system:
- **flux-vm** — 50-opcode FLUX-C VM (DAL A certifiable), TrustZone bridge to FLUX-X (247 opcodes), Universal AST (7 node types), ISA crates: mini/std/edge/thor
- **flux-hardware** — Complete cross-platform suite: CPU AVX-512 (35.9B/s JIT, 70.1B/s multi-thread), CUDA GPU (5 kernels, 1.02B/s), FPGA (1,717 LUTs, RTL), WebGPU, Vulkan, eBPF (XDP firewall), Fortran. Formal: SymbiYosys + Coq. 210 tests, 5.58M inputs, 0 mismatches. Safe-TOPS/W: 410M (CPU), 241M (GPU)
- **flux-docs** — Complete docs: tutorials (quickstart 5min, GUARD DSL, constraint cookbook), runbooks (fleet ops), strategy (certification roadmap, investor FAQ, onboarding 90-day, pitch deck), man pages
- **CCC agent** has been active: cocapn-reviews (fleet-math critical review with mathematical corrections), cocapn-prototypes (PLATO Presence Scale frontend+backend)

### CCC's Fleet-Math Review Key Points:
- H1 cohomology: should use β₁ (first Betti number) not H1 directly; emergence definition may be tautological; 2.7s early warning needs controlled experiment
- Zero Holonomy: needs formal proof; 38ms latency claim needs BFT comparison; "unlimited throughput" needs upper bound
- Pythagorean48: collision probability via birthday paradox; "zero drift" is trivial property of deterministic hash; needs comparison to SimHash/product quantization

## Fleet Mathematics (JC1-CT Bridge)
Key discoveries from two independent research groups converging:
- **H1 Cohomology** — E-V+C = emergence detection. 127 lines replaces 12K-line ML.
- **Zero Holonomy Consensus** — 38ms latency, any Byzantine tolerance. Replaces voting/CRDTs.
- **Pythagorean48** — 6 bits/vector, log₂(48)=5.585. Zero drift after unlimited hops.
- **Laman's 12 = Law 102's 12** — Rigidity threshold. 170-year-old graph theory.
- **Ricci flow 1.692 = Law 103 1.7** — Convergence constant within 0.5%.

## PLATO (the workshop)
- Room Server: localhost:8847
- **PLATO rooms** (live): 1,485+, room server at `:8847`
- Key rooms: oracle1_history, oracle1_lessons, fleet_communication, fleet_scale, competitive_landscape, oracle1_infrastructure

## Services (all on systemd)
keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato:8847, mud:7777, cocapn-php:8080, nginx:443, crab-trap:4042, lock:4043, arena:4044, grammar:4045

## New Repos (2026-05-04)
- `holonomy-consensus` — Rust crate: zero-holonomy consensus + H1 emergence + Pythagorean48
- `jc1-ct-bridge` — 470 lines: how CT math replaces JC1's ML
- `constraint-theory-llvm` — LLVM backend: CDCL trace → AVX-512
- `fleet-agent` v0.2.0 — PyPI: fleet_math integrated (H1, holonomy, Pythagorean48)
- `plato-sdk` v2.0.0 — PyPI: fleet_math exported (16 new symbols)
- 14 × `-ai-pages` — all polished with unique content

## Credentials
- **GitHub**: SuperInstance org only — ALL repos, pushes, automation through SuperInstance. cocapn org is DEPRECATED.
- PyPI token: `~/.pypirc` (token auth, __token__ username)
- crates.io token: `~/.cargo/credentials.toml`
- RubyGems MFA: 491133 (per-push OTP)

## Model Routing (2026-05-04)
- **minimax/MiniMax-M2.7** — OpenClaw agent default
- **Moonshot** — kimi-cli only, NOT direct API
- **z.ai GLM** — zai_code.js via nohup for direct coding API
- **kimi-cli** — primary implementation tool
- **DeepInfra Seed-2.0-mini** — slow/long outputs timeout. Use Nemotron for reliability.
- **Groq** — revoked

## Critical Rules
- **PLATO-FIRST: file knowledge to PLATO, keep files lean.**
- Push before claiming done
- kimi-cli is primary coding tool
- Daily memory under 150 lines. MEMORY.md under 50 lines.

## Brand — Cocapn
- Lighthouse + radar rings. Hermit crab: agents are crabs, repos are shells.
- "Prompting Is All You Need" paper