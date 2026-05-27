"""GateStream — process items through a sequence of quality gates."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from quality_gate.gate import QualityGate, GateResult, GateOutcome
from quality_gate.report import GateReport


@dataclass
class StreamItemResult:
    """The result of running one item through the entire stream."""

    item_index: int
    gate_results: List[GateResult] = field(default_factory=list)
    final_outcome: GateOutcome = GateOutcome.PASS
    stopped_at: Optional[str] = None  # gate name where processing stopped (fail-fast)


class GateStream:
    """Process items sequentially through a pipeline of quality gates.

    Supports:
    - Ordered gate pipeline
    - Fail-fast mode (stop on first FAIL)
    - Batch or single-item processing
    """

    def __init__(
        self,
        gates: Optional[Sequence[QualityGate]] = None,
        fail_fast: bool = True,
    ) -> None:
        self.gates: List[QualityGate] = list(gates or [])
        self.fail_fast = fail_fast

    def add_gate(self, gate: QualityGate) -> "GateStream":
        self.gates.append(gate)
        return self

    def process_item(self, item: Any) -> StreamItemResult:
        """Run a single item through all gates."""
        result = StreamItemResult(item_index=0)

        for gate in self.gates:
            gr = gate.evaluate(item)
            result.gate_results.append(gr)

            if gr.outcome == GateOutcome.FAIL and self.fail_fast:
                result.final_outcome = GateOutcome.FAIL
                result.stopped_at = gate.name
                return result

        # Overall outcome: worst among all gates
        if any(gr.outcome == GateOutcome.FAIL for gr in result.gate_results):
            result.final_outcome = GateOutcome.FAIL
        elif any(gr.outcome == GateOutcome.WARN for gr in result.gate_results):
            result.final_outcome = GateOutcome.WARN
        else:
            result.final_outcome = GateOutcome.PASS

        return result

    def process(self, items: Sequence[Any]) -> List[StreamItemResult]:
        """Process multiple items through the stream."""
        results: List[StreamItemResult] = []
        for i, item in enumerate(items):
            r = self.process_item(item)
            r.item_index = i
            results.append(r)
        return results

    def process_and_report(self, items: Sequence[Any]) -> GateReport:
        """Process items and return a summary GateReport."""
        results = self.process(items)
        return GateReport.from_stream_results(self, results)
