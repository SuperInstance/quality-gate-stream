# CREDENTIALS.md — Master Registry

> **Last verified:** 2026-04-28
> **Purpose:** Single source of truth. Check this BEFORE asking Casey for anything.
> **Rule:** Every key gets an entry. Every entry gets a verify date. No exceptions.

## Format
| Service | Location | Status | Last Verified | Notes |
|---------|----------|--------|---------------|-------|

## Active Keys

| Service | Location | Status | Last Verified | Notes |
|---------|----------|--------|---------------|-------|
| GitHub (cocapn PAT) | `~/.config/cocapn/github-pat` | ✅ Active | 2026-04-28 | Repo read/write, 92 repos |
| GitHub (SuperInstance) | `~/.git-credentials` | ✅ Active | 2026-04-28 | Push access |
| PyPI (cocapn) | `~/.pypirc` | ✅ Active | 2026-04-28 | 30+ packages |
| crates.io | `~/.cargo/credentials.toml` | ✅ Active | 2026-05-01 | 7+ crates |
| npm (@superinstance) | npm config | ✅ Active | 2026-04-28 | plato-sdk, tile-refiner |
| DeepInfra | `~/.bashrc` (DEEPINFRA_API_KEY) | ✅ Active | 2026-04-28 | Seed-2.0-mini |
| Groq | `~/.bashrc` (GROQ_API_KEY) | ✅ Active | 2026-04-28 | llama-3.3-70b |
| SiliconFlow | `~/.bashrc` (SILICONFLOW_API_KEY) | ✅ Active | 2026-04-13 | DeepSeek-V3 |
| DeepSeek Direct | `~/.bashrc` (DEEPSEEK_API_KEY) | ✅ Active | 2026-04-28 | v4-flash/pro |
| Moonshot AI | `~/.bashrc` (MOONSHOT_API_KEY) | ✅ Active | 2026-04-28 | kimi-k2.5 |
| Cloudflare (API Token) | `~/.config/cocapn/cloudflare-token` | ❌ Invalid | 2026-04-28 | `cfat_...` — rejected by API. Awaiting replacement from Casey |
| Cloudflare (Global Key) | `~/.config/cocapn/cloudflare-token` | ❌ Invalid | 2026-04-28 | `049ff...` — rejected w/ casey.digennaro@gmail.com. Awaiting fix |
| Cloudflare (email) | N/A | ℹ️ Known | 2026-04-28 | casey.digennaro@gmail.com |

## Key Lifecycle Rules
1. **New key → immediate entry** in this file + correct storage location
2. **Verify all keys** at least once per week (heartbeat task)
3. **Key rotation** → update this file FIRST, then all locations
4. **Never ask Casey for a key** without checking this file first
5. **If a key file is missing**, check bashrc, check PLATO, check TOOLS.md — THEN ask

## Storage Conventions
- GitHub PATs → `~/.config/cocapn/` or `~/.git-credentials`
- API keys → `~/.bashrc` (exported env vars)
- Package registry tokens → `~/.pypirc`, `~/.cargo/credentials.toml`, npm config
- Never store in git-tracked files

## Heartbeat Verification Checklist
Add to HEARTBEAT.md: "Verify CREDENTIALS.md entries (rotate through 3-4 per heartbeat)"
