"""QualityGate — evaluates items through checks and produces pass/fail/warn results."""

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from quality_gate.check import Check
from quality_gate.threshold import ThresholdConfig


class GateOutcome(enum.Enum):
    """Possible outcomes of a quality gate evaluation."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class GateResult:
    """Result of evaluating a single item through a gate."""

    gate_name: str
    outcome: GateOutcome
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class QualityGate:
    """A named gate containing one or more checks, with threshold-based outcomes.

    Each check returns a 0–1 score. The gate aggregates scores (weighted average)
    and maps the aggregate to PASS / WARN / FAIL using a ThresholdConfig.
    """

    def __init__(
        self,
        name: str,
        checks: Optional[Sequence[Check]] = None,
        weights: Optional[Dict[str, float]] = None,
        threshold: Optional[ThresholdConfig] = None,
    ) -> None:
        self.name = name
        self.checks: List[Check] = list(checks or [])
        self.weights: Dict[str, float] = weights or {}
        self.threshold = threshold or ThresholdConfig()

    def add_check(self, check: Check, weight: float = 1.0) -> "QualityGate":
        """Add a check to this gate. Returns self for chaining."""
        self.checks.append(check)
        self.weights.setdefault(check.name, weight)
        return self

    def evaluate(self, item: Any) -> GateResult:
        """Evaluate *item* through every check and produce a GateResult."""
        if not self.checks:
            return GateResult(
                gate_name=self.name,
                outcome=GateOutcome.PASS,
                score=1.0,
                details={"message": "no checks configured"},
            )

        total_weight = 0.0
        weighted_sum = 0.0
        failures: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        for check in self.checks:
            w = self.weights.get(check.name, 1.0)
            result = check.run(item)
            weighted_sum += result.score * w
            total_weight += w
            details[check.name] = {
                "score": result.score,
                "passed": result.passed,
                "message": result.message,
            }
            if not result.passed:
                failures.append(f"{check.name}: {result.message}")
            elif result.score < 1.0:
                warnings.append(f"{check.name}: {result.message}")

        aggregate = weighted_sum / total_weight if total_weight > 0 else 1.0
        outcome = self._resolve_outcome(aggregate, failures)

        return GateResult(
            gate_name=self.name,
            outcome=outcome,
            score=round(aggregate, 4),
            details=details,
            failures=failures,
            warnings=warnings,
        )

    def _resolve_outcome(self, score: float, failures: List[str]) -> GateOutcome:
        if score >= self.threshold.pass_threshold:
            return GateOutcome.PASS
        if score >= self.threshold.warn_threshold:
            return GateOutcome.WARN
        return GateOutcome.FAIL
