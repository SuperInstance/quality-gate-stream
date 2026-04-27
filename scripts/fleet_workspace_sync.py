#!/usr/bin/env python3
"""
fleet_workspace_sync.py

Sync Oracle1 workspace state to PLATO workspace board.
Designed to run as a cron job.

Usage:
    python3 fleet_workspace_sync.py
    ./fleet_workspace_sync.py
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_PATH = Path("/tmp/workspace_sync.log")
TODO_PATH = Path("/home/ubuntu/.openclaw/workspace/TODO.md")
NEXT_ACTION_PATH = Path("/home/ubuntu/.openclaw/workspace/NEXT-ACTION.md")
BEACHCOMB_STATE_PATH = Path("/tmp/beachcomb-v2-state.json")
PLATO_URL = "http://localhost:8847/workspace/oracle1"
AGENT_NAME = "Oracle1"

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("fleet_workspace_sync")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
    )

    # File handler
    try:
        fh = logging.FileHandler(LOG_PATH, mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except OSError as exc:
        # Fallback to stderr if we can't open the log file
        print(f"WARNING: Cannot open log file {LOG_PATH}: {exc}", file=sys.stderr)

    # Stream handler for cron-friendly stderr output (errors only)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


# ---------------------------------------------------------------------------
# File readers with safe fallbacks
# ---------------------------------------------------------------------------
def read_text(path: Path, logger: logging.Logger) -> str:
    """Read a text file, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("File not found: %s", path)
        return ""
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        return ""


def read_json(path: Path, logger: logging.Logger) -> dict[str, Any]:
    """Read a JSON file, returning empty dict on error."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        logger.warning("JSON file not found: %s", path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        return {}
    except OSError as exc:
        logger.error("Cannot read JSON %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def parse_todo(md: str) -> dict[str, Any]:
    """Parse TODO.md into structured data."""
    result: dict[str, Any] = {
        "total_items": 0,
        "completed_items": 0,
        "pending_items": 0,
        "p0_pending": 0,
        "p1_pending": 0,
        "p2_pending": 0,
        "completed_recently": [],
        "pending_tasks": [],
    }

    current_section = None
    for raw_line in md.splitlines():
        line = raw_line.rstrip()

        # Detect priority sections
        if line.startswith("## 🔴 P0"):
            current_section = "p0"
            continue
        elif line.startswith("## 🟡 P1"):
            current_section = "p1"
            continue
        elif line.startswith("## 🟢 P2"):
            current_section = "p2"
            continue
        elif line.startswith("## "):
            current_section = "other"
            continue

        # Check for checklist items
        match = re.match(r"^\s*-\s*\[([ xX])\]\s*(.*)$", line)
        if not match:
            continue

        checked = match.group(1).strip().lower() == "x"
        text = match.group(2).strip()
        if not text:
            continue

        result["total_items"] += 1
        if checked:
            result["completed_items"] += 1
        else:
            result["pending_items"] += 1
            if current_section == "p0":
                result["p0_pending"] += 1
                result["pending_tasks"].append(f"[P0] {text}")
            elif current_section == "p1":
                result["p1_pending"] += 1
                result["pending_tasks"].append(f"[P1] {text}")
            elif current_section == "p2":
                result["p2_pending"] += 1
                result["pending_tasks"].append(f"[P2] {text}")

        # Capture "Completed Today" entries (checked items in that section)
        if current_section == "other" and checked and "completed" in line.lower():
            # Also capture items explicitly in the Completed Today list
            pass

    # Extract "Completed Today" section specifically
    completed_section_match = re.search(
        r"## Completed Today.*?(?=\n## |\Z)", md, re.DOTALL | re.IGNORECASE
    )
    if completed_section_match:
        section_text = completed_section_match.group(0)
        for line in section_text.splitlines():
            m = re.match(r"^\s*-\s*\[[xX]\]\s*(.*)$", line)
            if m:
                result["completed_recently"].append(m.group(1).strip())

    # If no dedicated completed section found, fall back to recently checked items
    if not result["completed_recently"]:
        # Grab the last few checked items as a heuristic
        checked_items = []
        for line in md.splitlines():
            m = re.match(r"^\s*-\s*\[[xX]\]\s*(.*)$", line)
            if m:
                checked_items.append(m.group(1).strip())
        result["completed_recently"] = checked_items[-10:]

    return result


def parse_next_action(md: str) -> dict[str, Any]:
    """Parse NEXT-ACTION.md into structured data."""
    result: dict[str, Any] = {
        "active_task": "",
        "next_actions": [],
    }

    lines = md.splitlines()
    in_active = False
    in_after = False

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip()

        if line.startswith("## Active Task"):
            in_active = True
            in_after = False
            continue
        elif line.startswith("## After This Task"):
            in_active = False
            in_after = True
            continue
        elif line.startswith("## "):
            in_active = False
            in_after = False
            continue

        if in_active and line and not line.startswith("Steps:"):
            # Skip empty lines and step-number lines when collecting the task title
            if re.match(r"^\d+\.", line):
                continue
            if result["active_task"]:
                result["active_task"] += " " + line.lstrip("* **").rstrip("**")
            else:
                result["active_task"] = line.lstrip("* **").rstrip("**")
        elif in_after and line.startswith("→"):
            action = line.lstrip("→ ").strip()
            if action:
                result["next_actions"].append(action)

    # Cleanup active_task: bold markers may wrap it on a single line
    result["active_task"] = result["active_task"].strip("* ")
    m = re.match(r"\*\*(.*?)\*\*$", result["active_task"])
    if m:
        result["active_task"] = m.group(1)

    return result


# ---------------------------------------------------------------------------
# Payload assembler
# ---------------------------------------------------------------------------
def build_payload(
    todo_data: dict[str, Any],
    next_action_data: dict[str, Any],
    beachcomb_data: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    findings = beachcomb_data.get("findings", [])
    tick_count = beachcomb_data.get("tick_count", 0)

    # Determine status
    active_task = next_action_data.get("active_task", "")
    if active_task:
        status = "active"
    elif todo_data.get("pending_items", 0) > 0:
        status = "idle"
    else:
        status = "standby"

    # Assemble next_actions: merge from NEXT-ACTION.md + top pending tasks
    next_actions = list(next_action_data.get("next_actions", []))
    pending = todo_data.get("pending_tasks", [])
    for task in pending[:5]:
        if task not in next_actions:
            next_actions.append(task)

    # Progress metrics
    total = todo_data.get("total_items", 0)
    completed = todo_data.get("completed_items", 0)
    progress_pct = round((completed / total * 100), 1) if total > 0 else 0.0

    payload: dict[str, Any] = {
        "agent": AGENT_NAME,
        "status": status,
        "active_task": active_task or "No active task assigned",
        "progress": {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": todo_data.get("pending_items", 0),
            "p0_pending": todo_data.get("p0_pending", 0),
            "p1_pending": todo_data.get("p1_pending", 0),
            "p2_pending": todo_data.get("p2_pending", 0),
            "completion_percent": progress_pct,
        },
        "next_actions": next_actions[:10],
        "completed_recently": todo_data.get("completed_recently", [])[:10],
        "metrics": {
            "beachcomb_findings_count": len(findings),
            "beachcomb_tick_count": tick_count,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    return payload


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
def post_payload(payload: dict[str, Any], logger: logging.Logger) -> bool:
    """POST JSON payload to PLATO. Return True on success."""
    body = json.dumps(payload, indent=2).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(
        PLATO_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            logger.info(
                "PLATO POST %s -> HTTP %s (%s bytes)",
                PLATO_URL,
                resp.status,
                len(body),
            )
            if resp.status >= 200 and resp.status < 300:
                logger.debug("PLATO response: %s", resp_body[:500])
                return True
            else:
                logger.warning("PLATO returned HTTP %s: %s", resp.status, resp_body[:500])
                return False
    except urllib.error.HTTPError as exc:
        resp_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        logger.error(
            "PLATO HTTP error %s: %s — %s",
            exc.code,
            exc.reason,
            resp_body[:500],
        )
        return False
    except urllib.error.URLError as exc:
        logger.error("PLATO connection error: %s", exc.reason)
        return False
    except TimeoutError:
        logger.error("PLATO request timed out after 15s")
        return False
    except Exception as exc:
        logger.error("Unexpected error posting to PLATO: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    logger = setup_logging()
    logger.info("=== Fleet workspace sync started ===")

    exit_code = 0

    # Read source files
    todo_md = read_text(TODO_PATH, logger)
    next_action_md = read_text(NEXT_ACTION_PATH, logger)
    beachcomb_data = read_json(BEACHCOMB_STATE_PATH, logger)

    # Parse
    todo_data = parse_todo(todo_md)
    next_action_data = parse_next_action(next_action_md)

    logger.info(
        "Parsed TODO: %s total, %s completed, %s pending",
        todo_data["total_items"],
        todo_data["completed_items"],
        todo_data["pending_items"],
    )
    logger.info(
        "Parsed NEXT-ACTION: active_task='%s', next_actions=%s",
        next_action_data["active_task"],
        len(next_action_data["next_actions"]),
    )
    logger.info(
        "Beachcomb state: %s findings, tick_count=%s",
        len(beachcomb_data.get("findings", [])),
        beachcomb_data.get("tick_count", 0),
    )

    # Build and post payload
    payload = build_payload(todo_data, next_action_data, beachcomb_data, logger)
    logger.debug("Payload:\n%s", json.dumps(payload, indent=2))

    if post_payload(payload, logger):
        logger.info("=== Fleet workspace sync completed successfully ===")
    else:
        logger.error("=== Fleet workspace sync failed during POST ===")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
