# Navigator Integration Plan

*Extracted from the 3-model cross-model debate and meta-synthesis*

---

## Top 5 Artifacts from the Debate

### 1. Stratified Repository Taxonomy (SRT)
- **Produced by:** Groq-120B
- **Summary:** A three-tier classification system (Core-Infrastructure, Domain-Logic, Experimental) derived from commit-message semantics and cross-repo import graphs, enabling global navigation across 600+ repos.
- **Fleet connection:** Maps directly to PLATO room tile allocation — each SRT tier becomes a training stratum. CurriculumEngine consumes this to schedule progressive-difficulty tiles.

### 2. Theorem of Osmotic Integration
- **Produced by:** DeepSeek
- **Summary:** Formalizes dependency adaptation as gradient-driven lattice rewriting that maximizes useful work per cycle (Δ work / Δ cycle), turning dependency management from heuristics into a measurable optimization objective.
- **Fleet connection:** The Lock (port 4043) implements the sense-select-integrate-stabilize loop; Crab Trap (port 4042) feeds gradient signals from external agents into the osmotic pressure calculation.

### 3. Barnacle-Theorem (Anchoring Theorem)
- **Produced by:** SiliconFlow
- **Summary:** Adaptation occurs through non-destructive layering of decisions (barnacles) onto the existing hull, preserving full provenance of every change rather than refactoring or replacing.
- **Fleet connection:** Each barnacle layer is tagged with provenance in PLATO's tile history; The Lock's state persistence maintains barnacle lineage across reasoning sessions.

### 4. Semantic Version Drift Index (SVDI)
- **Produced by:** Groq-120B
- **Summary:** A scalar metric measuring how far a repo's declared version constraints have diverged from the actual API surface, computed via automated type inference — a single-number fleet-wide health metric.
- **Fleet connection:** Feeds directly into CurriculumEngine prioritization (top-10 most drifted repos get training focus). CRDHM visualization surfaces drift hotspots on fleet dashboard.

### 5. Membrane-Build Protocol
- **Produced by:** DeepSeek
- **Summary:** A four-step sandbox-first loop (sense → select → integrate → stabilize) that isolates changes in a build layer before merging, aligning with CI/CD and providing measurable cost functions for adaptive dependency management.
- **Fleet connection:** The Lock's iterative reasoning cycles are the execution engine for this protocol. Each "reasoning iteration" maps to one membrane cycle.

---

## Navigator Integration Plan — Concrete TODOs

### Phase 0: Foundations
- [ ] **Create `navigator/` module** in the vessel repo with subdirectories: `stratifier/`, `drift_indexer/`, `osmotic_adaptor/`, `narrative_engine/`
- [ ] **Implement `navigator.stratify()`** — reads git history across fleet repos, classifies each into SRT tiers (Core/Domain/Experimental), outputs `srt.json`
- [ ] **Implement `navigator.svdi()`** — computes Semantic Version Drift Index per repo, outputs `svdi.csv`

### Phase 1: PLATO Integration (port 8847)
- [ ] **Define tile schemas** for each SRT tier — Core tiles get high-stability configs, Experimental tiles get high-mutation configs
- [ ] **Wire `srt.json` output into PLATO tile allocator** — auto-assign repos to tiles by tier
- [ ] **Add `stratigraphic_mapper.py`** — overlays training run history on code archaeology layers so PLATO rooms show temporal depth
- [ ] **Implement barnacle provenance tags** — each tile mutation gets a `barnacle_tag` with parent commit, timestamp, gradient vector

### Phase 2: The Lock Integration (port 4043)
- [ ] **Implement `src/lock/archaeology.py`** — treats reasoning traces as excavation sites, preserving each iteration's state
- [ ] **Wire Membrane-Build Protocol into Lock's reasoning cycle** — each lock-step iteration = one sense→select→integrate→stabilize cycle
- [ ] **Add gradient collection endpoint** — Lock exposes `/gradient` endpoint that external profilers can push signals to
- [ ] **Implement `deepseek.membrane_build(layer_id)`** — creates isolated Docker build layers for each adaptation attempt

### Phase 3: Crab Trap Integration (port 4042)
- [ ] **Deploy Luminescent Profiling agents** — inject lightweight profiling primitives into CI pipelines of target repos
- [ ] **Register external agents as gradient sources** — security scanners, perf monitors, dependency auditors feed signals to Crab Trap
- [ ] **Implement `mud/agent_stratigraphy`** — tracks agent decision layers in the MUD environment
- [ ] **Wire Crab-Shell Trade-off** — resource allocation between agents optimized for rigidity/eviction-risk/search-cost balance

### Phase 4: Pipeline & Narrative
- [ ] **Build unified pipeline graph:** `Git-History → Stratifier (SRT) → Drift-Indexer (SVDI) → Osmotic-Adaptor (Membrane+Barnacle) → Narrative Engine (CANG) → Fleet Dashboard`
- [ ] **Implement `navigator.generate_report(repo_id)`** — CANG reports with barnacle provenance and osmotic metrics
- [ ] **Build Cross-Repo Dependency Heat Map (CRDHM)** — matrix visualization colored by SVDI
- [ ] **Wire CurriculumEngine** — consumes CEIB mapping, updates PLATO tile difficulty based on SVDI changes

### Phase 5: Validation
- [ ] **Run Stratified Barnacle Test** on 50 repos across all SRT tiers
- [ ] **Target:** ≥30% SVDI reduction, ≥95% regression test pass rate on barnacle-merged layers
- [ ] **Human audit:** CANG report readability scored ≥4/5 by stakeholders
- [ ] **Performance gate:** CI cycle time increase <10%, memory footprint <2× baseline

---

*Generated 2026-04-21 from cross-model debate artifacts (Groq-120B, DeepSeek, SiliconFlow)*
