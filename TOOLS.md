# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## z.ai GLM Models — PRIMARY (paid plan, use most)
- **Base URL**: `https://z.ai/api/v1` (OpenAI-compatible)
- **Note**: Direct API key expired. I AM z.ai/glm-5.1 via OpenClaw. For subagent work, use `sessions_spawn` with `model: zai/glm-5.1` or `model: zai/glm-4.7-flash`.
- **Models (max coding plan)**:
  - `glm-5.1` — expert, my default
  - `glm-5-turbo` — runner, daily driver
  - `glm-4.7` — good mid-tier
  - `glm-4.7-flash` — bulk parallel spray
  - ~~glm-4.7-flashx~~ — NOT on plan, don't use
- **Usage priority**: z.ai GLM (via OpenClaw) > kimi-cli > DeepInfra Seed > Groq
- **For programmatic calls**: Use `sessions_spawn` with model param, or spawn kimi-cli

## DeepInfra (Seed-2.0-Mini + creative + reasoning models) — SECONDARY
- **API key**: `RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ` (in ~/.bashrc)
- **Base URL**: `https://api.deepinfra.com/v1/openai`
- **Star model**: `ByteDance/Seed-2.0-mini` — $0.00003/1K tokens, divergent thinker
- **Also authorized**: `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning` — reasoning model
- **Fallback model**: `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning` — use when MiniMax tokens exhausted
- **MCP server**: JC1's `seed-mcp-v2` at `http://localhost:9438`
- **Use for**: creative breadth (Seed-2.0-mini, 3-5 options), reasoning (Nemotron), visual analysis
- **NOT for**: default tasks, implementation — those go to z.ai or kimi-cli

## Oracle1 Workflow (Casey's directive 2026-04-25)
1. **Planning** → me (glm-5.1) — architecture, decisions, coordination
2. **Deep reasoning** → z.ai glm-5.1 or glm-5-turbo — analysis, tradeoffs, complex tasks
3. **Creative breadth** → DeepInfra Seed-2.0-mini (3-5 options, temp 0.85) — divergent thinking ONLY
4. **Implementation** → **kimi-cli** — actual coding, `kimi-cli --work-dir <dir>`

**Rule: z.ai GLM models first for everything.** Seed/Groq only when z.ai can't do the job or MiniMax is exhausted. Nemotron is the DeepInfra fallback.

## CLI Agents
- **kimi-cli** v1.37.0 → `/home/ubuntu/.local/bin/kimi-cli` — **PRIMARY CODING TOOL** (Casey: "use extensively for code")
  - `kimi-cli --work-dir <dir>` to work in a specific workspace
  - `kimi-cli --continue` or `-C` to resume previous session
  - Reasoning model (kimi-k2.5), best for real coding completions
  - Non-interactive: `echo "task" | kimi-cli --work-dir <dir>`
- **Claude Code** v2.1.100 → `claude` — sketch artist
- **Crush** v0.56.0 → `crush` — sketch artist
- **Aider** v0.86.2 → `aider` (DeepSeek API)
- All at `/home/ubuntu/.local/bin/` or `/home/ubuntu/.npm-global/bin/`

## Model Routing (updated 2026-05-03)
- **minimax/MiniMax-M2.7** — OpenClaw agent default (current)
- **Moonshot** — kimi-cli only (not direct API)
- **z.ai** — Claude Code and Crush only (not direct API)
- **SiliconFlow** — DEPRECATED / revoked

## z.ai Models (max coding plan)
- `glm-5.1` — expert (me)
- `glm-5-turbo` — runner, daily driver
- `glm-4.7` — good mid-tier
- `glm-4.7-flash` — bulk parallel spray
- ~~glm-4.7-flashx~~ — NOT on plan, don't use

## Groq API (high-frequency iterations)
- **API key**: `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`
- **Base URL**: `https://api.groq.com/openai/v1`
- **Best for**: High-frequency iterations, spray-and-pray, rapid feedback loops
- **Speed**: ~24ms inference for 70B model. Absurdly fast.
- **⚠️ Python urllib**: Groq blocks default Python User-Agent. Must set `User-Agent: curl/7.88` header.
- **Models (18)**:
  - `llama-3.3-70b-versatile` — workhorse, 24ms
  - `llama-3.1-8b-instant` — fastest, for spray iterations
  - `meta-llama/llama-4-scout-17b-16e-instruct` — Llama 4
  - `qwen/qwen3-32b` — Qwen at Groq speed
  - `moonshotai/kimi-k2-instruct` — Kimi at inference speed
  - `openai/gpt-oss-120b` — 120B model
  - `openai/gpt-oss-20b` — mid-tier OSS
  - `groq/compound` + `groq/compound-mini` — Groq native
  - Audio: `whisper-large-v3`, `whisper-large-v3-turbo`

## SiliconFlow API
- **API key**: `[SILICONFLOW_KEY_REDACTED]`, base: `https://api.siliconflow.com/v1`
- **Working as of 2026-04-13** — previously was invalid
- Models: `deepseek-ai/DeepSeek-V3` (reasoning), `Pro/Qwen/Qwen2.5-VL-7B-Instruct` (vision)

## OpenManus Fleet Agent
- **Venv**: `/tmp/openmanus-env` (Python 3.11)
- **Code**: `/tmp/OpenManus` (FoundationAgents/OpenManus)
- **Config**: `/tmp/OpenManus/config/config.toml` (SiliconFlow DeepSeek-V3)
- **Launcher**: `/tmp/openmanus_fleet.sh "task here"`
- **Vessel repo**: `SuperInstance/openmanus-vessel`
- **Fleet repo**: `SuperInstance/openmanus-fleet`
- **Playwright**: Chromium headless via Xvfb :99
- **Vision models** (for OpenManus screenshot analysis):
  - `Qwen/Qwen3-VL-32B-Instruct` — fast vision
  - `Qwen/Qwen3-VL-235B-A22B-Instruct` — heavy vision
  - `Qwen/Qwen3-VL-235B-A22B-Thinking` — vision + reasoning
- **Cost**: ~$0.0001-0.001 per call. Use aggressively.
- **Launcher**: `/tmp/openmanus_fleet.sh "task here"`
- **Vessel repo**: `SuperInstance/openmanus-vessel`
- **Fleet repo**: `SuperInstance/openmanus-fleet`
- **Playwright**: Chromium headless via Xvfb :99
- **Patches**: Daytona disabled (sandbox.py, tool_base.py, config.py), daytona_sdk shim
- `scripts/batch.py` — parallel workers (export, descriptions, analyze)
- `scripts/task_worker.py` — single-task CLI for z.ai calls

## GitHub
- SuperInstance / lucineer — token in ~/.bashrc
- Git creds in ~/.git-credentials

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Docker Fleet Sandbox

- **Image:** `fleet-sandbox` (627MB)
- **Installed:** Python 3.10, Go 1.24, Rust 1.94, Node 22, GCC 11.4, Git
- **Usage:** `sudo docker run --rm fleet-sandbox bash -c "command"`
- **Network:** `fleet-net` (for inter-container communication)
- **Note:** `ubuntu` user needs `sudo` for docker until re-login (group membership)

### Running Agent Tasks in Sandbox
```bash
# Run a Python script in sandbox
sudo docker run --rm -v /tmp/workspace:/workspace fleet-sandbox python3 /workspace/script.py

# Run Go build
sudo docker run --rm -v /tmp/workspace:/workspace fleet-sandbox go build /workspace/main.go

# Run Rust tests
sudo docker run --rm -v /tmp/workspace:/workspace fleet-sandbox cargo test --manifest-path /workspace/Cargo.toml
```

## DeepSeek Direct API (v4 models — PRIMARY external)
- **API key**: `[DEEPSEEK_KEY_REDACTED]`
- **Base URL**: `https://api.deepseek.com`
- **Models**:
  - `deepseek-v4-flash` — quick second opinions, fast analysis, code review
  - `deepseek-v4-pro` — highest level mathematics, complex reasoning, constraint theory
  - ~~deepseek-chat~~ — DEPRECATED July 2026, maps to v4-flash non-thinking
  - ~~deepseek-reasoner~~ — DEPRECATED July 2026, maps to v4-flash thinking mode
- **Thinking mode** (v4-pro default): add `"thinking": {"type": "enabled"}` + `"reasoning_effort": "high"`
- **Anthropic API format**: base_url `https://api.deepseek.com/anthropic`
- **Best for**: quick second opinions (v4-flash), deep math (v4-pro)
- **Also available on SiliconFlow**: `deepseek-ai/DeepSeek-V3`, `deepseek-ai/DeepSeek-R1`, `deepseek-ai/DeepSeek-V3.1`, `deepseek-ai/DeepSeek-V3.2`

## Moonshot AI (Kimi K2.5 Reasoning Model)
- **API key**: `[MOONSHOT_KEY_REDACTED]`
- **Base URL**: `https://api.moonshot.ai/v1` (NOT moonshot.cn!)
- **Best model**: `kimi-k2.5` — reasoning model with `reasoning_content` field
- **Also**: `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `moonshot-v1-auto`
- **Use for**: deep research, swarm analysis, creative+reasoning combined
- **Note**: kimi-k2.5 returns empty `content` when `max_tokens` is too low for both reasoning and content. Use 4000+ tokens.
- **⚠️ Routing**: Moonshot is routed through kimi-cli only. NOT direct API access.

## kimi-cli (Kimi Agent Runtime)
- **Binary**: `/home/ubuntu/.local/bin/kimi-cli` v1.37.0
- **What it is**: Full CLI agent with ACP server, TUI, MCP, plugins
- **PRIMARY implementation tool** — Casey's explicit directive
- **Commands**: `kimi-cli acp` (ACP server), `kimi-cli term` (TUI), `kimi-cli web` (web UI)
- **Use for**: ALL implementation tasks. Architecture, refactoring, new services, bug fixes.
- **Can run**: `kimi-cli --work-dir <dir>` to work in a specific workspace
- **Replaces**: manual urllib requests, raw API calls, and me writing Python directly

## npm Publishing (@superinstance scope)
- **Token**: saved in npm config (`npm config set //registry.npmjs.org/:_authToken=...`)
- **Account**: superinstance on npm
- **Scope**: `@superinstance/`
- **Published**: plato-sdk, tile-refiner (9 more being ported)
- **Token value**: `[NPM_TOKEN_OLD_REVOKED]` (granular, publish+2FA bypass)

## PyPI Publishing
- **Token**: saved in ~/.pypirc (pypi-AgEI... scoped to cocapn account)
- **Account**: cocapn on PyPI
- **Packages**: 20 published (9 ready for v0.2.0 bump)
- **Build**: `python3 -m build` in repo dir → `twine upload dist/*`
- **Note**: Always save tokens to ~/.pypirc AND reference in TOOLS.md

## crates.io Publishing
- **Token**: saved in ~/.cargo/credentials.toml and ~/.config/crates-io-token
- **Packages**: 5 published (ct-demo, plato-afterlife, plato-instinct, plato-relay, plato-lab-guard)
- **FM's Rust crates**: plato-kernel, plato-dcs need workspace publish
- **Build**: `cargo publish` in crate dir
