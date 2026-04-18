# Fleet Synergy Matrix — Who Does What, Why It Connects

## The Three Rigs

### Oracle1 🔮 (Cloud — Managing Director)
**Hardware**: Oracle Cloud ARM (free tier)
**Role**: Fleet coordination, documentation, public presentation, research synthesis
**Strengths**: Always on, 42 repos synced, full GitHub access, research writing
**Current output**: 252 PRs resolved, 13 READMEs, 7 research docs, org profile cleanup, landing page

### JetsonClaw1 (Edge — Bare Metal Specialist)
**Hardware**: Jetson Super Orin (NVIDIA edge GPU)
**Role**: Edge inference, CUDA Rust, biological computing model, genepool evolution
**Strengths**: Low-latency edge, real hardware, Rust expertise, biological metaphors → code
**Current output**: cuda-genepool 31/31 tests (RNA→Protein pipeline), holodeck-c conformance, subcontractor Cloudflare worker live

### Forgemaster ⚒️ (Training Rig — CUDA/LoRA Specialist)
**Hardware**: ProArt RTX 4050 (WSL2)
**Role**: Model training, CUDA PTX, LoRA fine-tuning, simulation, video capture
**Strengths**: Consumer GPU, overnight training, Steel.dev video A/B, plugin architecture
**Current output**: Modular plato-kernel (<100MB), tile forge 600/h, Steel.dev video capture, plugin decomposition system

## Synergy Map

```
                    ┌─────────────────────┐
                    │     CASEY (Human)    │
                    │   Captain / Vision   │
                    └──────┬──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
    ┌───────▼──────┐ ┌────▼───────┐ ┌───▼──────────┐
    │   Oracle1    │ │    JC1     │ │     FM       │
    │  (Cloud)     │ │  (Edge)    │ │  (Training)  │
    │              │ │            │ │              │
    │ Coordination │ │ Inference  │ │ Training     │
    │ Research     │ │ CUDA Rust  │ │ CUDA PTX     │
    │ Docs/PRs     │ │ Genepool   │ │ LoRA/JEPA    │
    │ Public face  │ │ Edge API   │ │ Video A/B    │
    │ Fleet sync   │ │ Subcontract│ │ Plugins      │
    └───────┬──────┘ └─────┬──────┘ └──────┬───────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                    ┌──────▼──────┐
                    │   PLATO     │
                    │  Shared MUD │
                    │ 2501 rooms  │
                    └─────────────┘
```

## The Handoff Points

### Oracle1 → JC1
- Research synthesis → JC1 implements on edge
- Fleet coordination → JC1's subcontractor serves tiles
- PR management → JC1's code gets reviewed and merged

### JC1 → FM
- Genepool evolution data → FM trains LoRA on patterns
- Edge inference results → FM benchmarks against RTX
- Rust implementations → FM ports CUDA PTX offloads

### FM → Oracle1
- Trained LoRA adapters → Oracle1 deploys to fleet
- Plugin architecture → Oracle1 documents and publishes
- Video A/B results → Oracle1 synthesizes into research

### FM → JC1
- CUDA PTX tiles → JC1 tests on Jetson Orin
- LoRA adapters → JC1 runs edge inference
- Plugin specs → JC1 implements edge versions

### All → Casey
- Status updates via Telegram
- Key decisions via bottle system
- Roadmap reviews via GitHub

## What Each Rig Needs From The Others

### Oracle1 Needs:
- JC1: Edge inference benchmarks, genepool evolution results
- FM: Trained LoRA weights, PTX offload performance data

### JC1 Needs:
- Oracle1: Coordinated fleet tasks, research context
- FM: CUDA PTX tiles optimized for Jetson (sm_87), trained models

### FM Needs:
- Oracle1: Research direction, public presentation of results
- JC1: Jetson benchmarks to validate RTX training transfers to edge

## The Missing Pieces (What We Should Build Together)

1. **Unified Tile Registry** — Oracle1 hosts, JC1 edge-fetches, FM trains
2. **LoRA ↔ JEPA Bridge** — FM trains LoRA on tile patterns, JC1 runs JEPA perception, Oracle1 coordinates
3. **Public Demo Pipeline** — Oracle1 writes docs, JC1 ensures edge works, FM provides trained models
4. **Genepool → Tile System** — JC1's biological evolution feeds into the tile marketplace
5. **Video A/B → Training Data** — FM's Steel.dev captures feed into JC1's genepool evolution

---

*The fleet is stronger than any single vessel. The ocean connects us.*
