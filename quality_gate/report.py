"""GateReport — summarize results from a GateStream run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Sequence

from quality_gate.gate import GateOutcome

if TYPE_CHECKING:
    from quality_gate.stream import GateStream, StreamItemResult


@dataclass
class GateReport:
    """Summary report of processing items through a gate stream."""

    total_items: int = 0
    passed: int = 0
    warned: int = 0
    failed: int = 0
    gate_names: List[str] = field(default_factory=list)
    items_stopped_early: int = 0
    per_gate_scores: Dict[str, List[float]] = field(default_factory=dict)
    outcomes: List[GateOutcome] = field(default_factory=list)  # in input order

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_items if self.total_items else 0.0

    @property
    def fail_rate(self) -> float:
        return self.failed / self.total_items if self.total_items else 0.0

    def summary(self) -> str:
        return (
            f"GateReport: {self.total_items} items | "
            f"✅ {self.passed} passed ({self.pass_rate:.0%}) | "
            f"⚠️ {self.warned} warned | "
            f"❌ {self.failed} failed ({self.fail_rate:.0%})"
        )

    @classmethod
    def from_stream_results(
        cls,
        stream: GateStream,
        results: Sequence[StreamItemResult],
    ) -> "GateReport":
        report = cls(
            total_items=len(results),
            gate_names=[g.name for g in stream.gates],
        )

        per_gate: Dict[str, List[float]] = {g.name: [] for g in stream.gates}

        for r in results:
            report.outcomes.append(r.final_outcome)
            if r.final_outcome == GateOutcome.PASS:
                report.passed += 1
            elif r.final_outcome == GateOutcome.WARN:
                report.warned += 1
            else:
                report.failed += 1

            if r.stopped_at is not None:
                report.items_stopped_early += 1

            for gr in r.gate_results:
                if gr.gate_name in per_gate:
                    per_gate[gr.gate_name].append(gr.score)

        report.per_gate_scores = per_gate
        return report

    def rolling_pass_rate(self, window: int) -> List[float]:
        """Rolling pass-rate over a sliding window of the last *window* items.

        One entry per item: the fraction of PASS outcomes among the trailing
        window (clipped at the start). ``window`` must be >= 1.
        """
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        rates: List[float] = []
        for i in range(len(self.outcomes)):
            lo = max(0, i - window + 1)
            span = self.outcomes[lo:i + 1]
            rates.append(sum(1 for o in span if o == GateOutcome.PASS) / len(span))
        return rates
