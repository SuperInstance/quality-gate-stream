import time

import pytest

from quartermaster_gc import GCSchedule, RetentionPolicy, TileGC


class TestRetentionPolicy:
    def test_keep_all(self):
        gc = TileGC(policy=RetentionPolicy.KEEP_ALL)
        gc.add_tile("t1", "room_a", time.time(), 1.0)
        gc.add_tile("t2", "room_a", time.time() - 1000, 0.1)
        report = gc.run_gc()
        assert report["marked_for_deletion"] == 0
        assert report["kept"] == 2

    def test_keep_recent(self):
        now = 1000.0
        gc = TileGC(policy=RetentionPolicy.KEEP_RECENT, max_age_seconds=100)
        gc.add_tile("t1", "room_a", now - 50, 1.0)
        gc.add_tile("t2", "room_a", now - 150, 1.0)
        report = gc.run_gc(now=now)
        assert report["marked_for_deletion"] == 1
        assert "t2" in gc.marked_for_deletion
        assert "t1" not in gc.marked_for_deletion

    def test_keep_important(self):
        gc = TileGC(policy=RetentionPolicy.KEEP_IMPORTANT, min_weight=5.0)
        gc.add_tile("t1", "room_a", time.time(), 10.0)
        gc.add_tile("t2", "room_a", time.time(), 3.0)
        report = gc.run_gc()
        assert report["marked_for_deletion"] == 1
        assert "t2" in gc.marked_for_deletion

    def test_keep_sampled(self):
        gc = TileGC(policy=RetentionPolicy.KEEP_SAMPLED, sample_rate=2)
        for i in range(10):
            gc.add_tile(f"t{i}", "room_a", time.time(), 1.0)
        report = gc.run_gc()
        assert report["kept"] == 5
        assert report["marked_for_deletion"] == 5

    def test_compound_policy_recent_and_important(self):
        now = 1000.0
        policy = RetentionPolicy.KEEP_RECENT | RetentionPolicy.KEEP_IMPORTANT
        gc = TileGC(policy=policy, max_age_seconds=100, min_weight=5.0)
        gc.add_tile("old_heavy", "room_a", now - 200, 10.0)
        gc.add_tile("new_light", "room_a", now - 10, 1.0)
        gc.add_tile("old_light", "room_a", now - 200, 1.0)
        report = gc.run_gc(now=now)
        # old_heavy is kept by KEEP_IMPORTANT
        # new_light is kept by KEEP_RECENT
        # old_light is deleted
        assert "old_heavy" not in gc.marked_for_deletion
        assert "new_light" not in gc.marked_for_deletion
        assert "old_light" in gc.marked_for_deletion
        assert report["kept"] == 2

    def test_compound_policy_three(self):
        now = 1000.0
        policy = (
            RetentionPolicy.KEEP_RECENT
            | RetentionPolicy.KEEP_IMPORTANT
            | RetentionPolicy.KEEP_SAMPLED
        )
        gc = TileGC(
            policy=policy, max_age_seconds=50, min_weight=100.0, sample_rate=10
        )
        gc.add_tile("old_heavy", "room_a", now - 200, 200.0)
        gc.add_tile("new_light", "room_a", now - 10, 1.0)
        gc.add_tile("old_sampled", "room_a", now - 200, 1.0)
        report = gc.run_gc(now=now)
        # old_heavy kept by important
        # new_light kept by recent
        # old_sampled maybe kept by sampled depending on hash
        assert "old_heavy" not in gc.marked_for_deletion
        assert "new_light" not in gc.marked_for_deletion
        assert report["total_tiles"] == 3

    def test_delete_marked(self):
        gc = TileGC(policy=RetentionPolicy.KEEP_IMPORTANT, min_weight=5.0)
        gc.add_tile("t1", "room_a", time.time(), 10.0)
        gc.add_tile("t2", "room_a", time.time(), 1.0)
        gc.run_gc()
        removed = gc.delete_marked()
        assert removed == 1
        assert len(gc.tiles) == 1
        assert gc.tiles[0].id == "t1"
        assert len(gc.marked_for_deletion) == 0

    def test_gc_report_structure(self):
        gc = TileGC()
        gc.add_tile("t1", "room_a", time.time(), 1.0)
        report = gc.run_gc()
        assert "total_tiles" in report
        assert "marked_for_deletion" in report
        assert "kept" in report
        assert "policy_names" in report
        assert report["policy_names"] == ["KEEP_ALL"]


class TestGCSchedule:
    def test_should_run_first_time(self):
        sched = GCSchedule(interval_seconds=60)
        assert sched.should_run(now=1000.0) is True

    def test_should_run_after_interval(self):
        sched = GCSchedule(interval_seconds=60)
        sched.record_run(now=1000.0)
        assert sched.should_run(now=1061.0) is True

    def test_should_not_run_before_interval(self):
        sched = GCSchedule(interval_seconds=60)
        sched.record_run(now=1000.0)
        assert sched.should_run(now=1050.0) is False

    def test_record_run_updates_last_run(self):
        sched = GCSchedule(interval_seconds=60)
        sched.record_run(now=2000.0)
        assert sched.last_run == 2000.0

    def test_schedule_with_tile_gc(self):
        sched = GCSchedule(interval_seconds=10)
        gc = TileGC(policy=RetentionPolicy.KEEP_RECENT, max_age_seconds=5)
        gc.add_tile("t1", "room_a", 0.0, 1.0)

        assert sched.should_run(now=15.0) is True
        report = gc.run_gc(now=15.0)
        sched.record_run(now=15.0)

        assert report["marked_for_deletion"] == 1
        assert sched.last_run == 15.0
        assert sched.should_run(now=20.0) is False
        assert sched.should_run(now=26.0) is True
