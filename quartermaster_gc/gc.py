"""Quartermaster garbage-collection module for tile management."""

import enum
import hashlib
import time as _time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class RetentionPolicy(enum.Flag):
    """Policies controlling which tiles are kept during GC."""

    KEEP_ALL = 1
    KEEP_RECENT = 2
    KEEP_IMPORTANT = 4
    KEEP_SAMPLED = 8


@dataclass
class Tile:
    """A single tile tracked by the GC."""

    id: str
    room: str
    timestamp: float
    weight: float


class TileGC:
    """Tile garbage-collector that marks tiles for deletion based on a retention policy."""

    def __init__(
        self,
        policy: RetentionPolicy = RetentionPolicy.KEEP_ALL,
        max_age_seconds: Optional[float] = None,
        min_weight: Optional[float] = None,
        sample_rate: Optional[int] = None,
    ):
        self.policy = policy
        self.max_age_seconds = max_age_seconds
        self.min_weight = min_weight
        self.sample_rate = sample_rate
        self.tiles: List[Tile] = []
        self.marked_for_deletion: List[str] = []

    # ------------------------------------------------------------------
    # Tile management
    # ------------------------------------------------------------------

    def add_tile(
        self, tile_id: str, room: str, timestamp: float, weight: float
    ) -> None:
        self.tiles.append(
            Tile(id=tile_id, room=room, timestamp=timestamp, weight=weight)
        )

    # ------------------------------------------------------------------
    # Policy evaluation helpers
    # ------------------------------------------------------------------

    def _keep_all_check(self, tile: Tile) -> bool:
        return RetentionPolicy.KEEP_ALL in self.policy

    def _keep_recent_check(self, tile: Tile, now: float) -> bool:
        if RetentionPolicy.KEEP_RECENT not in self.policy:
            return False
        if self.max_age_seconds is None:
            return True
        return (now - tile.timestamp) <= self.max_age_seconds

    def _keep_important_check(self, tile: Tile) -> bool:
        if RetentionPolicy.KEEP_IMPORTANT not in self.policy:
            return False
        if self.min_weight is None:
            return True
        return tile.weight >= self.min_weight

    def _keep_sampled_check(self, tile: Tile) -> bool:
        if RetentionPolicy.KEEP_SAMPLED not in self.policy:
            return False
        if self.sample_rate is None or self.sample_rate <= 0:
            return True
        return (sum(tile.id.encode()) % self.sample_rate) == 0

    # ------------------------------------------------------------------
    # GC operations
    # ------------------------------------------------------------------

    def mark(self, now: Optional[float] = None) -> None:
        """Mark tiles for deletion according to the active policy."""
        if now is None:
            now = _time.time()

        self.marked_for_deletion = []

        # If KEEP_ALL is part of the policy (even in a compound policy),
        # every tile is considered "kept" by this rule.
        for tile in self.tiles:
            kept = False

            # KEEP_ALL always keeps everything
            if self._keep_all_check(tile):
                kept = True
            else:
                # For compound policies (no KEEP_ALL), a tile is kept if
                # *any* sub-policy says to keep it.
                kept = (
                    self._keep_recent_check(tile, now)
                    or self._keep_important_check(tile)
                    or self._keep_sampled_check(tile)
                )

            if not kept:
                self.marked_for_deletion.append(tile.id)

    def sweep(self) -> int:
        """Remove tiles that were previously marked for deletion."""
        to_remove = set(self.marked_for_deletion)
        self.tiles = [t for t in self.tiles if t.id not in to_remove]
        removed = len(to_remove)
        self.marked_for_deletion = []
        return removed

    def run_gc(self, now: Optional[float] = None) -> Dict:
        """Run mark + sweep and return a report dict."""
        self.mark(now)

        kept = len(self.tiles) - len(self.marked_for_deletion)
        policy_names = sorted(p.name for p in RetentionPolicy if p in self.policy)

        return {
            "total_tiles": len(self.tiles),
            "marked_for_deletion": len(self.marked_for_deletion),
            "kept": kept,
            "policy_names": policy_names,
        }

    def delete_marked(self) -> int:
        """Sweep marked tiles. Alias kept for ergonomics."""
        return self.sweep()

    def stats(self) -> Dict:
        """Return summary statistics without running GC."""
        return {
            "total_tiles": len(self.tiles),
            "marked_for_deletion": len(self.marked_for_deletion),
        }


class GCSchedule:
    """Simple interval-based scheduler for GC runs."""

    def __init__(self, interval_seconds: float):
        self.interval_seconds = interval_seconds
        self.last_run: Optional[float] = None

    def should_run(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = _time.time()
        if self.last_run is None:
            return True
        return (now - self.last_run) >= self.interval_seconds

    def record_run(self, now: Optional[float] = None) -> None:
        if now is None:
            now = _time.time()
        self.last_run = now
