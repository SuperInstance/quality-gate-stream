#!/usr/bin/env python3
"""PLATO Jupyter Rooms — Fleet ML & Collaboration Notebooks.

Self-contained setup: creates room dirs, generates notebooks, installs Jupyter via venv.

Usage:
    python3 jupyter_rooms.py setup      # Create rooms + notebooks
    python3 jupyter_rooms.py install     # Install Jupyter Lab into venv
    python3 jupyter_rooms.py start       # Launch Jupyter Lab on :8888
    python3 jupyter_rooms.py status      # Check status
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0"

BASE_DIR = Path.home() / ".openclaw" / "workspace" / "jupyter-rooms"
VENV_DIR = BASE_DIR / ".venv"
PORT = 8888
TOKEN = "fleet-jupyter-2026"

ROOMS = {
    "ml-training": {
        "description": "LoRA fine-tuning, neural plato, forge experiments",
    },
    "research": {
        "description": "Papers, analysis, fleet knowledge graphs",
    },
    "constraint-theory": {
        "description": "CT benchmarks, snap experiments, drift measurement",
    },
    "data-analysis": {
        "description": "Tile analytics, fleet metrics, visualizations",
    },
    "collaboration": {
        "description": "Shared workspace for PurplePinchers and external agents",
    },
}


# ── Notebook Builders ──────────────────────────────────────────

def _md(text: str) -> dict:
    """Create a markdown cell."""
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def _code(source: str) -> dict:
    """Create a code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def _notebook(cells: list[dict]) -> dict:
    """Assemble a valid nbformat 4.5 notebook."""
    nb_cells = []
    for cell in cells:
        nb_cells.append(cell)
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.12",
            },
        },
        "cells": nb_cells,
    }


def _create_fleet_health_notebook() -> dict:
    """Fleet health check + tile exploration notebook."""
    return _notebook([
        _md(
            "# Fleet Health Check\n\n"
            "Check connectivity to all fleet services and explore PLATO room data.\n\n"
            "Services: PLATO (:8847), Shell (:8848), Nexus (:4047), "
            "Orchestrator (:8849), Crab Trap (:4042), Arena (:4044), Grammar (:4045)."
        ),
        _code(
            'import json\n'
            'import urllib.request\n'
            '\n'
            'FLEET_SERVICES: dict[str, int] = {\n'
            '    "PLATO": 8847,\n'
            '    "Shell": 8848,\n'
            '    "Nexus": 4047,\n'
            '    "Orchestrator": 8849,\n'
            '    "Crab Trap": 4042,\n'
            '    "Arena": 4044,\n'
            '    "Grammar": 4045,\n'
            '}\n'
            '\n'
            'for name, port in FLEET_SERVICES.items():\n'
            '    try:\n'
            '        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)\n'
            '        status = "OK"\n'
            '    except Exception:\n'
            '        status = "XX"\n'
            '    print(f"  {name:<20} :{port}  {status}")'
        ),
        _code(
            'import statistics\n'
            '\n'
            'resp = urllib.request.urlopen("http://localhost:8847/rooms", timeout=2)\n'
            'rooms = json.loads(resp.read())\n'
            '\n'
            'total_tiles = sum(r["tile_count"] for r in rooms.values())\n'
            'print(f"Total: {len(rooms)} rooms, {total_tiles} tiles\\n")\n'
            '\n'
            'sorted_rooms = sorted(rooms.items(), key=lambda x: x[1]["tile_count"], reverse=True)\n'
            'print("Top 10 rooms by tile count:")\n'
            'for name, info in sorted_rooms[:10]:\n'
            '    print(f"  {name:<30} {info[\"tile_count\"]:>4}")'
        ),
        _code(
            '# Analyze confidence distribution across top rooms\n'
            'confs = []\n'
            'for room_name in [name for name, _ in sorted_rooms[:5]]:\n'
            '    try:\n'
            '        resp = urllib.request.urlopen(\n'
            '            f"http://localhost:8847/room/{room_name}?limit=100", timeout=2\n'
            '        )\n'
            '        tiles = json.loads(resp.read()).get("tiles", [])\n'
            '        for t in tiles:\n'
            '            confs.append(t.get("confidence", 0.0))\n'
            '    except Exception:\n'
            '        pass\n'
            '\n'
            'if confs:\n'
            '    print(f"Analyzed {len(confs)} tiles from top 5 rooms:")\n'
            '    print(f"  Mean:   {statistics.mean(confs):.4f}")\n'
            '    print(f"  Median: {statistics.median(confs):.4f}")\n'
            '    print(f"  Min:    {min(confs):.4f}")\n'
            '    print(f"  Max:    {max(confs):.4f}")\n'
            '    if len(confs) > 1:\n'
            '        print(f"  Stdev:  {statistics.stdev(confs):.4f}")'
        ),
    ])


def _create_research_notebook() -> dict:
    """Research room — fleet knowledge graph explorer."""
    return _notebook([
        _md(
            "# Fleet Knowledge Graph\n\n"
            "Explore accumulated knowledge across all PLATO rooms.\n"
            "Build a graph of room-to-room relationships based on shared domains and tiles."
        ),
        _code(
            'import json\n'
            'import urllib.request\n'
            'from collections import Counter\n'
            '\n'
            'resp = urllib.request.urlopen("http://localhost:8847/rooms", timeout=2)\n'
            'rooms = json.loads(resp.read())\n'
            '\n'
            'print(f"Fleet has {len(rooms)} rooms with "\n'
            '      f"{sum(r[\"tile_count\"] for r in rooms.values())} total tiles\\n")\n'
            '\n'
            '# Distribution analysis\n'
            'counts = [r["tile_count"] for r in rooms.values()]\n'
            'print(f"Tiles per room:")\n'
            'print(f"  Mean:   {statistics.mean(counts):.1f}")\n'
            'print(f"  Median: {statistics.median(counts):.1f}")\n'
            'print(f"  Max:    {max(counts)}")\n'
            'print(f"  Min:    {min(counts)}")'
        ),
        _code(
            '# Room size distribution — find knowledge clusters\n'
            'import statistics\n'
            '\n'
            'sizes = sorted(counts, reverse=True)\n'
            'total = sum(sizes)\n'
            '\n'
            'print("Knowledge concentration:")\n'
            'top_5 = sum(sizes[:5])\n'
            'top_10 = sum(sizes[:10])\n'
            'print(f"  Top 5 rooms:  {top_5:>5} tiles ({top_5/total*100:.1f}% of total)")\n'
            'print(f"  Top 10 rooms: {top_10:>5} tiles ({top_10/total*100:.1f}% of total)")\n'
            'print(f"  Remaining:    {total - top_10:>5} tiles ({(total-top_10)/total*100:.1f}%)")'
        ),
    ])


def _create_drift_experiment_notebook() -> dict:
    """Constraint theory drift experiment notebook."""
    return _notebook([
        _md(
            "# Constraint Theory — Drift Experiment\n\n"
            "**Hypothesis:** Float drift grows unbounded with repeated rotations. "
            "CT snap stays bounded because Pythagorean triples are exact integers.\n\n"
            "Expected results:\n"
            "- Float: drift grows proportionally to sqrt(iterations)\n"
            "- CT snap: drift bounded at ~0.36 regardless of iterations"
        ),
        _code(
            'import math\n'
            'import time\n'
            '\n'
            'def float_drift_experiment(iterations: int = 100_000) -> dict:\n'
            '    """Rotate (3,4) by 0.001 radians N times, measure magnitude drift."""\n'
            '    x, y = 3.0, 4.0\n'
            '    max_drift = 0.0\n'
            '\n'
            '    for i in range(iterations):\n'
            '        a = 0.001\n'
            '        nx = x * math.cos(a) - y * math.sin(a)\n'
            '        ny = x * math.sin(a) + y * math.cos(a)\n'
            '        x, y = nx, ny\n'
            '\n'
            '        if i % 10_000 == 0:\n'
            '            d = abs(math.sqrt(x * x + y * y) - 5.0)\n'
            '            max_drift = max(max_drift, d)\n'
            '\n'
            '    final = abs(math.sqrt(x * x + y * y) - 5.0)\n'
            '    return {\n'
            '        "iterations": iterations,\n'
            '        "final_magnitude": math.sqrt(x * x + y * y),\n'
            '        "final_drift": final,\n'
            '        "max_drift": max_drift,\n'
            '    }\n'
            '\n'
            't0 = time.perf_counter()\n'
            'r = float_drift_experiment(100_000)\n'
            'elapsed = time.perf_counter() - t0\n'
            '\n'
            'print(f"After {r[\"iterations\"]:,} rotations ({elapsed:.2f}s):")\n'
            'print(f"  Magnitude:  {r[\"final_magnitude\"]:.10f} (expected: 5.0)")\n'
            'print(f"  Final drift: {r[\"final_drift\"]:.2e}")\n'
            'print(f"  Max drift:   {r[\"max_drift\"]:.2e}")'
        ),
        _code(
            'def pythagorean_triples(limit: int) -> list[tuple[int, int, int]]:\n'
            '    """Generate primitive Pythagorean triples with c <= limit."""\n'
            '    triples = []\n'
            '    for m in range(2, int(math.sqrt(limit)) + 1):\n'
            '        for n in range(1, m):\n'
            '            if (m - n) % 2 == 1 and math.gcd(m, n) == 1:\n'
            '                a, b, c = m * m - n * n, 2 * m * n, m * m + n * n\n'
            '                if c <= limit:\n'
            '                    triples.append((min(a, b), max(a, b), c))\n'
            '    return triples\n'
            '\n'
            'triples = pythagorean_triples(1000)\n'
            'print(f"Primitive triples with c <= 1000: {len(triples)}")\n'
            'print(f"First 5: {triples[:5]}")\n'
            'print(f"This gives {len(triples)} distinct directions for snapping.")'
        ),
        _code(
            'def ct_snap(x: float, y: float, density: int = 100) -> tuple[float, float, float]:\n'
            '    """Snap (x, y) to the nearest Pythagorean triple direction.\n'
            '\n'
            '    Returns (snapped_x, snapped_y, error_pct).\n'
            '    """\n'
            '    d = math.sqrt(x * x + y * y)\n'
            '    if d == 0:\n'
            '        return (0.0, 0.0, 0.0)\n'
            '\n'
            '    nx, ny = abs(x) / d, abs(y) / d\n'
            '    best_err = float("inf")\n'
            '    best_triple = (3, 4, 5)\n'
            '\n'
            '    for a, b, c in pythagorean_triples(density):\n'
            '        err = abs(nx - a / c) + abs(ny - b / c)\n'
            '        if err < best_err:\n'
            '            best_err = err\n'
            '            best_triple = (a, b, c)\n'
            '\n'
            '    a, b, c = best_triple\n'
            '    scale = d / c\n'
            '    sx = (a * scale) * (1 if x >= 0 else -1)\n'
            '    sy = (b * scale) * (1 if y >= 0 else -1)\n'
            '    snap_d = math.sqrt(sx * sx + sy * sy)\n'
            '    error_pct = abs(d - snap_d) / d * 100\n'
            '\n'
            '    return (sx, sy, error_pct)\n'
            '\n'
            '# Test cases\n'
            'print("snap(3.0, 4.0):", ct_snap(3.0, 4.0, 100))\n'
            'print("snap(1.0, 1.0):", ct_snap(1.0, 1.0, 100))\n'
            'print("snap(5.0, 12.0):", ct_snap(5.0, 12.0, 100))'
        ),
    ])


def _create_collaboration_notebook() -> dict:
    """Collaboration room welcome notebook."""
    return _notebook([
        _md(
            "# Collaboration Room\n\n"
            "Shared workspace for the fleet and external collaborators.\n\n"
            "## Fleet Services\n"
            "- **PLATO** — http://localhost:8847 (tile knowledge base)\n"
            "- **Shell** — http://localhost:8848 (agentic IDE)\n"
            "- **Nexus** — http://localhost:4047 (federated learning)\n"
            "- **Orchestrator** — http://localhost:8849 (event cascades)\n\n"
            "## Guidelines\n"
            "1. Document your experiments with markdown cells\n"
            "2. Tag PLATO tiles with your agent name as source\n"
            "3. Push reproducible results to your vessel repo"
        ),
        _code(
            'import time\n'
            '\n'
            'print("Hello from the collaboration room!")\n'
            'print(f"Timestamp: {time.strftime(\"%%Y-%%m-%%d %%H:%%M:%%S\")}")'
        ),
    ])


# ── Room: Notebook Mapping ─────────────────────────────────────

NOTEBOOK_BUILDERS = {
    "ml-training": [
        ("00_fleet_health.ipynb", _create_fleet_health_notebook),
    ],
    "research": [
        ("00_knowledge_graph.ipynb", _create_research_notebook),
    ],
    "constraint-theory": [
        ("00_drift_experiment.ipynb", _create_drift_experiment_notebook),
    ],
    "collaboration": [
        ("README.ipynb", _create_collaboration_notebook),
    ],
}


# ── CLI Commands ───────────────────────────────────────────────

def cmd_setup() -> None:
    """Create room directories and generate all notebooks."""
    print(f"Creating Jupyter rooms at {BASE_DIR} ...")
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    for room_name, config in ROOMS.items():
        room_dir = BASE_DIR / room_name
        room_dir.mkdir(parents=True, exist_ok=True)
        (room_dir / "README.md").write_text(
            f"# {room_name}\n\n{config['description']}\n"
        )

        for filename, builder in NOTEBOOK_BUILDERS.get(room_name, []):
            nb = builder()
            (room_dir / filename).write_text(json.dumps(nb, indent=2))
            print(f"  OK  {room_name}/{filename}")

        print(f"  DIR {room_name}/")

    # Root index
    index = "# PLATO Jupyter Rooms\n\n"
    for room_name, config in ROOMS.items():
        index += f"- **{room_name}** — {config['description']}\n"
    index += f"\nPassword: `{TOKEN}`\n"
    index += f"URL: http://147.224.38.131:{PORT}/lab?token={TOKEN}\n"
    (BASE_DIR / "README.md").write_text(index)

    total_nbs = sum(
        len(NOTEBOOK_BUILDERS.get(r, [])) for r in ROOMS
    )
    print(f"\nDone: {len(ROOMS)} rooms, {total_nbs} notebooks.")


def cmd_install() -> None:
    """Install Jupyter Lab into a venv under BASE_DIR."""
    print("Creating virtual environment ...")
    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)], check=True,
    )
    pip = str(VENV_DIR / "bin" / "pip")
    print("Installing jupyterlab, notebook, ipykernel ...")
    subprocess.run(
        [pip, "install", "jupyterlab", "notebook", "ipykernel", "-q"],
        check=True,
    )
    print("OK — Jupyter installed.")


def cmd_start() -> str | None:
    """Launch Jupyter Lab. Returns the URL or None."""
    jupyter = shutil.which("jupyter") or shutil.which("jupyter-lab")
    if not jupyter:
        venv_jupyter = VENV_DIR / "bin" / "jupyter"
        if venv_jupyter.exists():
            jupyter = str(venv_jupyter)
        else:
            print("Jupyter not found. Run: python3 jupyter_rooms.py install")
            return None

    print(f"Starting Jupyter Lab on port {PORT} ...")
    proc = subprocess.Popen(
        [
            jupyter, "lab",
            "--ip=0.0.0.0",
            f"--port={PORT}",
            f"--notebook-dir={BASE_DIR}",
            f"--ServerApp.token={TOKEN}",
            "--ServerApp.allow_origin=*",
            "--no-browser",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (BASE_DIR / "jupyter.pid").write_text(str(proc.pid))

    url = f"http://147.224.38.131:{PORT}/lab?token={TOKEN}"
    print(f"PID:   {proc.pid}")
    print(f"URL:   {url}")
    print(f"Token: {TOKEN}")

    # Wait for startup line
    for raw in proc.stdout:
        line = raw.decode().strip()
        if line:
            print(line)
        if "is running" in line.lower():
            break

    return url


def cmd_status() -> None:
    """Report Jupyter status."""
    pid_file = BASE_DIR / "jupyter.pid"
    if pid_file.exists():
        pid = int(pid_file.read_text())
        try:
            os.kill(pid, 0)
            print(f"OK  Jupyter running (PID {pid})")
            print(f"    http://147.224.38.131:{PORT}/lab?token={TOKEN}")
        except ProcessLookupError:
            print("XX  Jupyter not running (stale PID)")
    else:
        print("XX  Jupyter not running")

    print(f"\nRooms at {BASE_DIR}:")
    for p in sorted(BASE_DIR.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            nbs = list(p.glob("*.ipynb"))
            print(f"  {p.name:<25} {len(nbs)} notebook(s)")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        print("Commands: setup | install | start | status")
        sys.exit(0)

    commands = {
        "setup": cmd_setup,
        "install": cmd_install,
        "start": cmd_start,
        "status": cmd_status,
    }
    cmd = sys.argv[1]
    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
    commands[cmd]()


if __name__ == "__main__":
    main()
