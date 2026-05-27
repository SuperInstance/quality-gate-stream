"""Comprehensive tests for the quality_gate package."""

import pytest

from quality_gate.check import (
    CheckResult,
    ContentCheck,
    CustomCheck,
    FormatCheck,
    LengthCheck,
)
from quality_gate.gate import GateOutcome, GateResult, QualityGate
from quality_gate.report import GateReport
from quality_gate.stream import GateStream, StreamItemResult
from quality_gate.threshold import ThresholdConfig


# ---------------------------------------------------------------------------
# ThresholdConfig
# ---------------------------------------------------------------------------

class TestThresholdConfig:
    def test_defaults(self):
        t = ThresholdConfig()
        assert t.pass_threshold == 0.8
        assert t.warn_threshold == 0.5

    def test_custom(self):
        t = ThresholdConfig(pass_threshold=0.9, warn_threshold=0.6)
        assert t.pass_threshold == 0.9

    def test_invalid_warn_above_pass(self):
        with pytest.raises(ValueError):
            ThresholdConfig(pass_threshold=0.3, warn_threshold=0.9)

    def test_negative_threshold(self):
        with pytest.raises(ValueError):
            ThresholdConfig(warn_threshold=-0.1)

    def test_equal_thresholds(self):
        t = ThresholdConfig(pass_threshold=0.7, warn_threshold=0.7)
        assert t.pass_threshold == t.warn_threshold


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

class TestLengthCheck:
    def test_within_bounds(self):
        c = LengthCheck(min_length=5, max_length=100)
        r = c.run("hello world")
        assert r.passed
        assert r.score == 1.0

    def test_too_short(self):
        c = LengthCheck(min_length=10)
        r = c.run("hi")
        assert not r.passed
        assert r.score == 0.0

    def test_too_long(self):
        c = LengthCheck(max_length=5)
        r = c.run("a" * 20)
        assert not r.passed
        assert r.score == 0.3

    def test_sweet_spot(self):
        c = LengthCheck(min_length=0, max_length=1000, sweet_spot=(50, 200))
        # inside sweet spot
        r = c.run("x" * 100)
        assert r.score == 1.0
        # below sweet spot
        r = c.run("x" * 25)
        assert 0.5 < r.score < 1.0


class TestFormatCheck:
    def test_matches(self):
        c = FormatCheck(pattern=r"^\d{3}-\d{4}$")
        assert c.run("123-4567").passed

    def test_no_match(self):
        c = FormatCheck(pattern=r"^\d{3}-\d{4}$")
        assert not c.run("abc-defg").passed

    def test_forbidden_match(self):
        c = FormatCheck(pattern=r"spam", must_match=False)
        assert c.run("clean text").passed
        assert not c.run("this is spam here").passed


class TestContentCheck:
    def test_required_present(self):
        c = ContentCheck(required=["hello", "world"])
        r = c.run("hello brave new world")
        assert r.passed
        assert r.score == 1.0

    def test_required_missing(self):
        c = ContentCheck(required=["python", "rust"])
        r = c.run("I like python")
        assert not r.passed
        assert r.score == 0.5

    def test_forbidden_found(self):
        c = ContentCheck(forbidden=["bad", "evil"])
        r = c.run("this is bad")
        assert not r.passed
        assert r.score == 0.0

    def test_case_insensitive(self):
        c = ContentCheck(required=["Hello"], case_sensitive=False)
        assert c.run("hello there").passed

    def test_case_sensitive(self):
        c = ContentCheck(required=["Hello"], case_sensitive=True)
        r = c.run("hello there")
        assert not r.passed


class TestCustomCheck:
    def test_custom_pass(self):
        fn = lambda item: CheckResult(score=1.0, passed=True, message="ok")
        c = CustomCheck(name="custom", fn=fn)
        r = c.run("anything")
        assert r.passed

    def test_custom_fail(self):
        fn = lambda item: CheckResult(score=0.0, passed=False, message="bad")
        c = CustomCheck(name="custom", fn=fn)
        assert not c.run("anything").passed


# ---------------------------------------------------------------------------
# QualityGate
# ---------------------------------------------------------------------------

class TestQualityGate:
    def test_empty_gate_passes(self):
        g = QualityGate(name="empty")
        r = g.evaluate("hello")
        assert r.outcome == GateOutcome.PASS
        assert r.score == 1.0

    def test_single_check_pass(self):
        g = QualityGate(
            name="len_gate",
            checks=[LengthCheck(min_length=3)],
            threshold=ThresholdConfig(pass_threshold=0.8, warn_threshold=0.4),
        )
        r = g.evaluate("hello")
        assert r.outcome == GateOutcome.PASS

    def test_single_check_fail(self):
        g = QualityGate(
            name="len_gate",
            checks=[LengthCheck(min_length=100)],
        )
        r = g.evaluate("short")
        assert r.outcome == GateOutcome.FAIL

    def test_weighted_checks(self):
        g = QualityGate(
            name="mixed",
            checks=[
                LengthCheck(name="len", min_length=5),  # passes
                ContentCheck(name="content", required=["missing"]),  # fails
            ],
            weights={"len": 3.0, "content": 1.0},
            threshold=ThresholdConfig(pass_threshold=0.8, warn_threshold=0.4),
        )
        r = g.evaluate("hello world")
        # len=1.0 (w=3), content=0.0 (w=1) → aggregate = 3/(3+1) = 0.75 → WARN
        assert r.outcome == GateOutcome.WARN

    def test_add_check_chaining(self):
        g = QualityGate(name="chain").add_check(LengthCheck(min_length=1))
        r = g.evaluate("x")
        assert r.outcome == GateOutcome.PASS

    def test_result_has_details(self):
        g = QualityGate(
            name="detail",
            checks=[LengthCheck(name="len", min_length=1)],
        )
        r = g.evaluate("ok")
        assert "len" in r.details
        assert r.details["len"]["score"] == 1.0


# ---------------------------------------------------------------------------
# GateStream
# ---------------------------------------------------------------------------

class TestGateStream:
    def _make_gates(self):
        gate1 = QualityGate(
            name="length_check",
            checks=[LengthCheck(min_length=5)],
        )
        gate2 = QualityGate(
            name="content_check",
            checks=[ContentCheck(required=["ok"])],
        )
        return [gate1, gate2]

    def test_all_pass(self):
        s = GateStream(gates=self._make_gates())
        r = s.process_item("ok this is fine")
        assert r.final_outcome == GateOutcome.PASS

    def test_fail_fast(self):
        s = GateStream(gates=self._make_gates(), fail_fast=True)
        r = s.process_item("bad")  # too short → fails gate1
        assert r.final_outcome == GateOutcome.FAIL
        assert r.stopped_at == "length_check"

    def test_no_fail_fast(self):
        s = GateStream(gates=self._make_gates(), fail_fast=False)
        r = s.process_item("bad")
        assert r.final_outcome == GateOutcome.FAIL
        assert r.stopped_at is None  # runs all gates

    def test_batch(self):
        s = GateStream(gates=self._make_gates())
        results = s.process(["ok text", "short", "ok another one ok"])
        assert len(results) == 3
        assert results[0].final_outcome == GateOutcome.PASS
        assert results[1].final_outcome == GateOutcome.FAIL

    def test_add_gate(self):
        s = GateStream().add_gate(QualityGate(name="g", checks=[LengthCheck(min_length=1)]))
        r = s.process_item("x")
        assert r.final_outcome == GateOutcome.PASS


# ---------------------------------------------------------------------------
# GateReport
# ---------------------------------------------------------------------------

class TestGateReport:
    def test_summary(self):
        s = GateStream(gates=[
            QualityGate(name="g1", checks=[LengthCheck(min_length=3)]),
        ])
        report = s.process_and_report(["hello", "hi", "world"])
        assert report.total_items == 3
        assert report.passed == 2
        assert report.failed == 1
        assert "✅" in report.summary()

    def test_pass_rate(self):
        report = GateReport(total_items=10, passed=7, warned=2, failed=1)
        assert report.pass_rate == 0.7
        assert report.fail_rate == 0.1

    def test_from_stream_results(self):
        s = GateStream(gates=[
            QualityGate(name="g1", checks=[LengthCheck(min_length=3)]),
            QualityGate(name="g2", checks=[ContentCheck(required=["ok"])]),
        ])
        results = s.process(["ok hello", "ok"])
        report = GateReport.from_stream_results(s, results)
        assert report.gate_names == ["g1", "g2"]
        assert "g1" in report.per_gate_scores
        assert len(report.per_gate_scores["g1"]) == 2

    def test_stopped_early_count(self):
        s = GateStream(gates=[
            QualityGate(name="g1", checks=[LengthCheck(min_length=10)]),
            QualityGate(name="g2", checks=[LengthCheck(min_length=1)]),
        ], fail_fast=True)
        report = s.process_and_report(["short", "this is long enough"])
        assert report.items_stopped_early == 1


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_pipeline(self):
        """End-to-end: build gates, stream items, get report."""
        gate1 = QualityGate(
            name="format",
            checks=[FormatCheck(pattern=r"^[\w\s,.-]+$")],
        )
        gate2 = QualityGate(
            name="length",
            checks=[LengthCheck(min_length=10, max_length=500, sweet_spot=(50, 200))],
        )
        gate3 = QualityGate(
            name="content",
            checks=[ContentCheck(required=["important"], forbidden=["TODO", "FIXME"])],
        )

        stream = GateStream(gates=[gate1, gate2, gate3], fail_fast=True)

        items = [
            "This is important and well-formed content",
            "short",
            "This has a TODO in it which is important",
            "X" * 600 + " important",  # too long
        ]

        results = stream.process(items)
        report = GateReport.from_stream_results(stream, results)

        # Item 0: 42 chars, >= min_length=10, format ok, content ok → PASS
        assert results[0].final_outcome == GateOutcome.PASS
        assert results[1].final_outcome == GateOutcome.FAIL  # too short
        assert results[2].final_outcome == GateOutcome.FAIL  # contains forbidden TODO
        assert report.total_items == 4
