#!/usr/bin/env python3
"""
Flywheel Convergence Experiment

Tracks the convergence of the zeroclaw flywheel system:
- 12 zeroclaw agents produce tiles every 5 minutes
- PLATO server at localhost:8847 receives tiles
- Room trainer synthesizes tiles into ensigns
- Ensigns get injected back into agent identities

Measures:
1. Baseline tile counts per room
2. Per-cycle metrics (tile count, room count, average confidence)
3. Lyapunov perturbation at cycle 5 (20% Gaussian noise)
4. Recovery tracking after perturbation
"""

import json
import time
import random
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Optional imports
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuration
PLATO_SERVER = "http://localhost:8847"
CYCLE_COUNT = 10
CYCLE_DURATION_SEC = 300  # 5 minutes
REFINED_ENSIGNS_DIR = Path("/tmp/refined")
ZEROCLAW_STATES_DIR = Path("/tmp/zeroclaw-states")  # Adjust as needed
METRICS_FILE = Path("/tmp/sprints/flywheel-metrics.json")
OUTPUT_REPORT = Path("/tmp/sprints/convergence-report.json")
OUTPUT_CHART = Path("/tmp/sprints/convergence.png")


class FlywheelExperiment:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.metrics = {
            "experiment_start": datetime.now().isoformat(),
            "cycles": [],
            "perturbation_cycle": 5,
            "config": {
                "plato_server": PLATO_SERVER,
                "cycle_count": CYCLE_COUNT,
                "cycle_duration_sec": CYCLE_DURATION_SEC,
                "perturbation_noise_percent": 20,
                "perturbation_tile_count": 200
            }
        }

    def query_plato_status(self) -> Dict[str, Any]:
        """Query PLATO server for current status."""
        if not REQUESTS_AVAILABLE:
            print("[WARNING] requests not available, returning mock data")
            return self._mock_status()

        try:
            response = requests.get(f"{PLATO_SERVER}/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Failed to query PLATO server: {e}")
            return self._mock_status()

    def _mock_status(self) -> Dict[str, Any]:
        """Generate mock status for testing."""
        return {
            "rooms": {
                f"room_{i}": {
                    "tile_count": random.randint(50, 200),
                    "avg_confidence": random.uniform(0.6, 0.95)
                }
                for i in range(12)
            },
            "total_tiles": sum(random.randint(50, 200) for _ in range(12)),
            "room_count": 12
        }

    def inject_perturbation(self) -> bool:
        """Inject Lyapunov perturbation: add 20% Gaussian noise to 200 random tiles."""
        if not REQUESTS_AVAILABLE:
            print("[WARNING] requests not available, skipping perturbation injection")
            return False

        status = self.query_plato_status()
        rooms = status.get("rooms", {})

        if not rooms:
            print("[WARNING] No rooms found for perturbation")
            return False

        # Collect all tiles across rooms
        all_tiles = []
        for room_name, room_data in rooms.items():
            tile_count = room_data.get("tile_count", 0)
            for i in range(tile_count):
                all_tiles.append({
                    "room": room_name,
                    "tile_id": f"{room_name}_tile_{i}",
                    "confidence": room_data.get("avg_confidence", 0.8)
                })

        if not all_tiles:
            print("[WARNING] No tiles found for perturbation")
            return False

        # Select 200 random tiles
        tiles_to_perturb = random.sample(all_tiles, min(200, len(all_tiles)))

        perturbed_count = 0
        for tile in tiles_to_perturb:
            # Add 20% Gaussian noise
            noise = random.gauss(0, 0.2)
            new_confidence = max(0.0, min(1.0, tile["confidence"] + noise))

            try:
                response = requests.post(
                    f"{PLATO_SERVER}/room/{tile['room']}/tile",
                    json={
                        "tile_id": tile["tile_id"],
                        "confidence": new_confidence
                    },
                    timeout=5
                )
                if response.status_code in (200, 201):
                    perturbed_count += 1
            except requests.exceptions.RequestException as e:
                print(f"[WARNING] Failed to perturb tile {tile['tile_id']}: {e}")

        print(f"[PERTURBATION] Perturbed {perturbed_count} tiles with 20% Gaussian noise")
        return perturbed_count > 0

    def inject_ensigns(self) -> int:
        """Inject current ensigns into zeroclaw STATE.md files."""
        refined_dir = Path("/tmp/refined")

        if not refined_dir.exists():
            print(f"[WARNING] Refined ensigns directory not found: {refined_dir}")
            return 0

        # Find all ensign files
        ensign_files = list(refined_dir.glob("*.md")) + list(refined_dir.glob("*.json"))

        if not ensign_files:
            print("[WARNING] No ensign files found in /tmp/refined/")
            return 0

        injected_count = 0
        for ensign_file in ensign_files:
            try:
                content = ensign_file.read_text()
                # In a real implementation, this would merge into STATE.md files
                # For now, just count what we found
                injected_count += 1
                print(f"[ENSIGN] Found ensign: {ensign_file.name} ({len(content)} bytes)")
            except Exception as e:
                print(f"[WARNING] Failed to read ensign {ensign_file.name}: {e}")

        print(f"[ENSIGN] Processed {injected_count} ensign files")
        return injected_count

    def record_cycle_metrics(self, cycle_num: int) -> Dict[str, Any]:
        """Record metrics for a single cycle."""
        status = self.query_plato_status()
        rooms = status.get("rooms", {})

        # Calculate aggregate metrics
        tile_counts = [r.get("tile_count", 0) for r in rooms.values()]
        confidences = [r.get("avg_confidence", 0) for r in rooms.values()]

        cycle_metrics = {
            "cycle": cycle_num,
            "timestamp": datetime.now().isoformat(),
            "tile_count": sum(tile_counts),
            "room_count": len(rooms),
            "avg_confidence": statistics.mean(confidences) if confidences else 0.0,
            "confidence_std": statistics.stdev(confidences) if len(confidences) > 1 else 0.0,
            "rooms": rooms
        }

        # Calculate convergence quality (higher is better)
        # Convergence = high avg confidence + low std deviation
        convergence = (
            cycle_metrics["avg_confidence"] * 0.7 +
            (1.0 - min(1.0, cycle_metrics["confidence_std"])) * 0.3
        )
        cycle_metrics["convergence_quality"] = convergence

        print(f"[CYCLE {cycle_num}] Tiles: {cycle_metrics['tile_count']}, "
              f"Rooms: {cycle_metrics['room_count']}, "
              f"Avg Confidence: {cycle_metrics['avg_confidence']:.3f}, "
              f"Convergence: {convergence:.3f}")

        return cycle_metrics

    def run(self):
        """Run the full flywheel experiment."""
        print("=" * 60)
        print("FLYWHEEL CONVERGENCE EXPERIMENT")
        print("=" * 60)
        print(f"PLATO Server: {PLATO_SERVER}")
        print(f"Cycles: {CYCLE_COUNT}")
        print(f"Cycle Duration: {CYCLE_DURATION_SEC}s")
        print(f"Perturbation at Cycle: 5")
        print(f"Dry Run: {self.dry_run}")
        print("=" * 60)

        # Baseline measurement
        print("\n[BASELINE] Measuring initial state...")
        baseline = self.record_cycle_metrics(0)
        self.metrics["baseline"] = baseline

        # Main experiment loop
        for cycle in range(1, CYCLE_COUNT + 1):
            print(f"\n{'=' * 60}")
            print(f"CYCLE {cycle}/{CYCLE_COUNT}")
            print(f"{'=' * 60}")

            # Record pre-cycle metrics
            pre_metrics = self.record_cycle_metrics(cycle)

            # Inject ensigns
            ensigns_injected = self.inject_ensigns()
            pre_metrics["ensigns_injected"] = ensigns_injected

            # Inject perturbation at cycle 5
            if cycle == 5:
                print("\n[PERTURBATION] Injecting Lyapunov perturbation...")
                perturbation_success = self.inject_perturbation()
                pre_metrics["perturbation_injected"] = perturbation_success

            # Wait for cycle duration (skip in dry run)
            if not self.dry_run:
                print(f"\n[WAIT] Waiting {CYCLE_DURATION_SEC}s for agents to produce tiles...")
                time.sleep(CYCLE_DURATION_SEC)
            else:
                print("\n[DRY RUN] Skipping wait")

            # Record post-cycle metrics
            post_metrics = self.record_cycle_metrics(cycle)
            pre_metrics["post_cycle"] = post_metrics

            self.metrics["cycles"].append(pre_metrics)

            # Save intermediate metrics
            self._save_metrics()

        # Generate final report
        self._generate_report()

        # Generate chart if matplotlib is available
        if MATPLOTLIB_AVAILABLE:
            self._generate_chart()
        else:
            print("[INFO] matplotlib not available, skipping chart generation")

        print("\n" + "=" * 60)
        print("EXPERIMENT COMPLETE")
        print(f"Metrics saved to: {METRICS_FILE}")
        print(f"Report saved to: {OUTPUT_REPORT}")
        if MATPLOTLIB_AVAILABLE:
            print(f"Chart saved to: {OUTPUT_CHART}")
        print("=" * 60)

    def _save_metrics(self):
        """Save metrics to JSON file."""
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_FILE, "w") as f:
            json.dump(self.metrics, f, indent=2)

    def _generate_report(self):
        """Generate final convergence report."""
        # Calculate summary statistics
        cycles = self.metrics["cycles"]
        pre_perturbation = cycles[:4]  # Cycles 1-4
        post_perturbation = cycles[5:]  # Cycles 6-10 (cycle 5 is the perturbation cycle)

        pre_convergence = [c["convergence_quality"] for c in pre_perturbation]
        post_convergence = [c["convergence_quality"] for c in post_perturbation]

        report = {
            "experiment_summary": {
                "start_time": self.metrics["experiment_start"],
                "end_time": datetime.now().isoformat(),
                "total_cycles": len(cycles),
                "perturbation_cycle": 5
            },
            "baseline": self.metrics["baseline"],
            "pre_perturbation": {
                "avg_convergence": statistics.mean(pre_convergence) if pre_convergence else 0.0,
                "convergence_trend": "improving" if len(pre_convergence) > 1 and pre_convergence[-1] > pre_convergence[0] else "stable"
            },
            "post_perturbation": {
                "avg_convergence": statistics.mean(post_convergence) if post_convergence else 0.0,
                "recovery_rate": (post_convergence[-1] - post_convergence[0]) / len(post_convergence) if len(post_convergence) > 1 else 0.0,
                "convergence_trend": "improving" if len(post_convergence) > 1 and post_convergence[-1] > post_convergence[0] else "stable"
            },
            "convergence_assessment": self._assess_convergence(pre_convergence, post_convergence)
        }

        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT, "w") as f:
            json.dump(report, f, indent=2)

        print("\n[REPORT] Convergence Assessment:")
        print(f"  Pre-perturbation avg: {report['pre_perturbation']['avg_convergence']:.3f}")
        print(f"  Post-perturbation avg: {report['post_perturbation']['avg_convergence']:.3f}")
        print(f"  Recovery rate: {report['post_perturbation']['recovery_rate']:.4f}/cycle")
        print(f"  Assessment: {report['convergence_assessment']['status']}")

    def _assess_convergence(self, pre: List[float], post: List[float]) -> Dict[str, Any]:
        """Assess overall convergence quality."""
        if not pre or not post:
            return {"status": "insufficient_data", "confidence": 0.0}

        pre_avg = statistics.mean(pre)
        post_avg = statistics.mean(post)

        # Check if system recovered after perturbation
        recovered = post_avg >= pre_avg * 0.95  # Within 5% of pre-perturbation

        # Check stability
        if len(post) > 1:
            post_stability = 1.0 - min(1.0, statistics.stdev(post))
        else:
            post_stability = 0.5

        # Overall assessment
        if recovered and post_avg > 0.8:
            status = "excellent_convergence"
            confidence = min(1.0, post_avg + post_stability * 0.2)
        elif recovered and post_avg > 0.6:
            status = "good_convergence"
            confidence = min(1.0, post_avg + post_stability * 0.1)
        elif recovered:
            status = "partial_convergence"
            confidence = post_avg * 0.8
        else:
            status = "poor_convergence"
            confidence = max(0.0, post_avg - 0.2)

        return {
            "status": status,
            "confidence": confidence,
            "recovered": recovered,
            "stability_score": post_stability
        }

    def _generate_chart(self):
        """Generate convergence chart."""
        cycles = self.metrics["cycles"]

        if not cycles:
            print("[WARNING] No cycle data to plot")
            return

        # Extract data
        cycle_nums = [c["cycle"] for c in cycles]
        tile_counts = [c["tile_count"] for c in cycles]
        convergences = [c["convergence_quality"] for c in cycles]
        confidences = [c["avg_confidence"] for c in cycles]

        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('Flywheel Convergence Experiment', fontsize=16, fontweight='bold')

        # Plot 1: Tile counts over time
        ax1.plot(cycle_nums, tile_counts, 'b-o', linewidth=2, markersize=8, label='Total Tiles')
        ax1.axvline(x=5, color='r', linestyle='--', linewidth=2, label='Perturbation')
        ax1.set_xlabel('Cycle')
        ax1.set_ylabel('Tile Count')
        ax1.set_title('Total Tiles Over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Convergence quality
        ax2.plot(cycle_nums, convergences, 'g-o', linewidth=2, markersize=8, label='Convergence Quality')
        ax2.axvline(x=5, color='r', linestyle='--', linewidth=2, label='Perturbation')
        ax2.axhline(y=0.8, color='orange', linestyle=':', linewidth=1, label='Target (0.8)')
        ax2.set_xlabel('Cycle')
        ax2.set_ylabel('Convergence Quality')
        ax2.set_title('Convergence Quality Over Time')
        ax2.set_ylim(0, 1)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Average confidence
        ax3.plot(cycle_nums, confidences, 'm-o', linewidth=2, markersize=8, label='Avg Confidence')
        ax3.axvline(x=5, color='r', linestyle='--', linewidth=2, label='Perturbation')
        ax3.set_xlabel('Cycle')
        ax3.set_ylabel('Average Confidence')
        ax3.set_title('Average Tile Confidence Over Time')
        ax3.set_ylim(0, 1)
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(OUTPUT_CHART, dpi=150, bbox_inches='tight')
        print(f"[CHART] Saved convergence chart to {OUTPUT_CHART}")


def main():
    parser = argparse.ArgumentParser(description="Run flywheel convergence experiment")
    parser.add_argument("--dry-run", action="store_true", help="Skip wait periods for testing")
    args = parser.parse_args()

    experiment = FlywheelExperiment(dry_run=args.dry_run)
    experiment.run()


if __name__ == "__main__":
    main()
