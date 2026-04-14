# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## DeepInfra (Seed-2.0-Mini + creative models)
- **API key**: `RhZPtvuy4cXzu02LbBSffbXeqs5Yf2IZ` (in ~/.bashrc)
- **Base URL**: `https://api.deepinfra.com/v1/openai`
- **Star model**: `ByteDance/Seed-2.0-mini` — $0.00003/1K tokens, divergent thinker
- **MCP server**: JC1's `seed-mcp-v2` at `http://localhost:9438` (forked to SuperInstance)
- **Chain pattern**: Seed-mini (breadth) → Hermes-3-405B (pick best) → Seed-pro (polish)
- **Key rule**: Never ask for one answer. Always 3-5. Temp 0.85.
- **Also good for**: small image models, visual analysis

## CLI Agents
- **Claude Code** v2.1.100 → `claude` (coding plan active)
- **Crush** v0.56.0 → `crush` (coding plan active)
- **Aider** v0.86.2 → `aider` (DeepSeek API)
  - `aider --model deepseek/deepseek-chat` — fast coding
  - `aider --model deepseek/deepseek-reasoner` — deep reasoning
- All at `/home/ubuntu/.local/bin/` or `/home/ubuntu/.npm-global/bin/`

## z.ai Models (max coding plan)
- `glm-5.1` — expert (me)
- `glm-5-turbo` — runner, daily driver
- `glm-4.7` — good mid-tier
- `glm-4.7-flash` — bulk parallel spray
- ~~glm-4.7-flashx~~ — NOT on plan, don't use

## SiliconFlow API
- **API key**: `sk-xtcrixoswqhmsopntnkfapccswjywrlsdpbunqjukpileiqo`, base: `https://api.siliconflow.com/v1`
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

## DeepSeek Direct API (reasoner + chat)
- **API key**: `sk-f742b70fc40849eda4181afcf3d68b0c`
- **Base URL**: `https://api.deepseek.com`
- **Models**:
  - `deepseek-reasoner` — chain-of-thought reasoning, shows thinking process
  - `deepseek-chat` — fast, concise, good for compilation tasks
- **Key difference from SiliconFlow**: DeepSeek direct gives reasoning_content (visible thinking)
- **Best for**: deep analysis (reasoner), clean bytecode generation (chat)
- **Also available on SiliconFlow**: `deepseek-ai/DeepSeek-V3`, `deepseek-ai/DeepSeek-R1`, `deepseek-ai/DeepSeek-V3.1`, `deepseek-ai/DeepSeek-V3.2`
