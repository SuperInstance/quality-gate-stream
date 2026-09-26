"""Review pins — honesty pass 2026-09-27.

Every test here failed before the fix it pins:
- duplicate check names silently corrupt weights/details/aggregate
- _resolve_outcome's `failures` parameter was dead (diluted hard failures PASS)
- README claimed routing and rolling windows; neither existed
- pyproject built `quartermaster-gc`, so `pip install quality-gate-stream`
  (the README's own install line) could never provide `quality_gate`
"""
import pytest

from quality_gate.check import ContentCheck, CustomCheck, CheckResult
from quality_gate.gate import GateOutcome, QualityGate
from quality_gate.stream import GateStream
from quality_gate.threshold import ThresholdConfig


# ---------------------------------------------------------------------------
# duplicate check names must not silently corrupt scoring
# ---------------------------------------------------------------------------

class TestDuplicateCheckNames:
    def test_add_check_rejects_duplicate_name(self):
        g = QualityGate("g")
        g.add_check(ContentCheck("content", required=["alpha"]))
        with pytest.raises(ValueError, match="duplicate check name"):
            g.add_check(ContentCheck("content", required=["beta"]))

    def test_constructor_rejects_duplicate_names(self):
        with pytest.raises(ValueError, match="duplicate check name"):
            QualityGate("g", checks=[
                ContentCheck("content", required=["alpha"]),
                ContentCheck("content", required=["beta"]),
            ])

    def test_distinct_names_keep_independent_weights(self):
        g = QualityGate("g", threshold=ThresholdConfig(pass_threshold=0.9,
                                                        warn_threshold=0.5))
        g.add_check(ContentCheck("first", required=["alpha"]), weight=1.0)
        g.add_check(ContentCheck("second", required=["beta"]), weight=9.0)
        r = g.evaluate("alpha only")  # 1.0*1 + 0.0*9 -> 0.1 -> FAIL
        assert r.score == 0.1
        assert r.outcome == GateOutcome.FAIL
        assert set(r.details) == {"first", "second"}


# ---------------------------------------------------------------------------
# strict mode: a hard-failed check must be able to fail the gate
# (previously the `failures` signal was computed then ignored, so one
# hard failure could be diluted to a PASS by passing checks)
# ---------------------------------------------------------------------------

class TestStrictMode:
    def _gate(self, strict):
        g = QualityGate("g", strict=strict,
                        threshold=ThresholdConfig(pass_threshold=0.9,
                                                  warn_threshold=0.5))
        g.add_check(ContentCheck("hard", required=["must-be-there"]), weight=1.0)
        g.add_check(ContentCheck("soft", required=["nice"]), weight=9.0)
        return g

    def test_diluted_failure_passes_in_lenient_mode(self):
        r = self._gate(strict=False).evaluate("nice to see you")
        assert r.score == 0.9
        assert r.outcome == GateOutcome.PASS  # hard failure diluted — documented lenient default

    def test_hard_failure_fails_gate_in_strict_mode(self):
        r = self._gate(strict=True).evaluate("nice to see you")
        assert r.outcome == GateOutcome.FAIL
        assert any("hard" in f for f in r.failures)

    def test_strict_mode_passes_when_all_checks_pass(self):
        r = self._gate(strict=True).evaluate("nice must-be-there")
        assert r.outcome == GateOutcome.PASS


# ---------------------------------------------------------------------------
# routing — README promises it; the stream must deliver it
# ---------------------------------------------------------------------------

class TestRouting:
    def _stream(self):
        return GateStream([
            QualityGate("g", checks=[ContentCheck("c", required=["ok"])],
                        threshold=ThresholdConfig(pass_threshold=0.9,
                                                  warn_threshold=0.5)),
        ])

    def test_partition_groups_items_by_outcome(self):
        s = self._stream()
        parts = s.partition(["ok a", "ok b", "bad one"])
        assert [i for i, _ in parts[GateOutcome.PASS]] == [0, 1]
        assert [i for i, _ in parts[GateOutcome.FAIL]] == [2]

    def test_partition_carries_original_items(self):
        s = self._stream()
        parts = s.partition([{"doc": "ok one"}, {"doc": "ok two"}])
        assert parts[GateOutcome.PASS][0][1] == {"doc": "ok one"}

    def test_partition_empty_stream(self):
        parts = GateStream([]).partition(["anything"])
        assert parts[GateOutcome.PASS][0][0] == 0  # no gates -> PASS


# ---------------------------------------------------------------------------
# rolling windows — README promises rolling stats; the report must deliver
# ---------------------------------------------------------------------------

class TestRollingWindows:
    def test_rolling_pass_rate_slides(self):
        s = GateStream([
            QualityGate("g", checks=[ContentCheck("c", required=["ok"])],
                        threshold=ThresholdConfig(pass_threshold=0.9,
                                                  warn_threshold=0.5)),
        ])
        report = s.process_and_report(["ok", "bad", "ok", "ok"])
        # outcomes in order: PASS, FAIL, PASS, PASS
        assert list(report.outcomes) == [
            GateOutcome.PASS, GateOutcome.FAIL, GateOutcome.PASS, GateOutcome.PASS,
        ]
        assert report.rolling_pass_rate(window=2) == [1.0, 0.5, 0.5, 1.0]
        # one entry per item, window clipped at the start
        assert report.rolling_pass_rate(window=4) == [1.0, 0.5, 2 / 3, 0.75]

    def test_rolling_window_larger_than_items(self):
        s = GateStream([])
        report = s.process_and_report(["a", "b"])
        assert report.rolling_pass_rate(window=10) == [1.0, 1.0]

    def test_rolling_window_rejects_zero(self):
        from quality_gate.report import GateReport
        with pytest.raises(ValueError):
            GateReport().rolling_pass_rate(window=0)
