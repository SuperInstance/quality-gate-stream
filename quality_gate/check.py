"""Check types — individual quality checks that produce 0–1 scores."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Pattern, Sequence


@dataclass
class CheckResult:
    """Outcome of a single check."""

    score: float  # 0.0 – 1.0
    passed: bool
    message: str


class Check(ABC):
    """Base class for all quality checks."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, item: Any) -> CheckResult:
        ...


class LengthCheck(Check):
    """Check that a string's length falls within acceptable bounds."""

    def __init__(
        self,
        name: str = "length",
        min_length: int = 0,
        max_length: int = 10_000,
        sweet_spot: Optional[tuple[int, int]] = None,
    ) -> None:
        super().__init__(name)
        self.min_length = min_length
        self.max_length = max_length
        self.sweet_spot = sweet_spot  # (low, high) — scores 1.0 inside this range

    def run(self, item: Any) -> CheckResult:
        text = str(item)
        length = len(text)

        if length < self.min_length:
            return CheckResult(
                score=0.0, passed=False,
                message=f"length {length} below minimum {self.min_length}",
            )
        if length > self.max_length:
            return CheckResult(
                score=0.3, passed=False,
                message=f"length {length} exceeds maximum {self.max_length}",
            )

        if self.sweet_spot:
            low, high = self.sweet_spot
            if low <= length <= high:
                score = 1.0
            elif length < low:
                score = 0.5 + 0.5 * (length / low) if low > 0 else 0.5
            else:
                overshoot = length - high
                score = max(0.5, 1.0 - 0.5 * (overshoot / (self.max_length - high)))
        else:
            # Linear mapping: full score for anything in bounds
            score = 1.0

        return CheckResult(
            score=round(score, 4), passed=True,
            message=f"length {length} within bounds",
        )


class FormatCheck(Check):
    """Check that a string matches a required format (regex)."""

    def __init__(
        self,
        name: str = "format",
        pattern: str = r".*",
        flags: int = 0,
        must_match: bool = True,
    ) -> None:
        super().__init__(name)
        self.pattern: Pattern = re.compile(pattern, flags)
        self.must_match = must_match

    def run(self, item: Any) -> CheckResult:
        text = str(item)
        match = self.pattern.search(text)

        if self.must_match:
            if match:
                return CheckResult(score=1.0, passed=True, message="format matches")
            return CheckResult(
                score=0.0, passed=False,
                message=f"format does not match pattern '{self.pattern.pattern}'",
            )
        else:
            if not match:
                return CheckResult(score=1.0, passed=True, message="format constraint satisfied")
            return CheckResult(
                score=0.0, passed=False,
                message=f"format incorrectly matches forbidden pattern '{self.pattern.pattern}'",
            )


class ContentCheck(Check):
    """Check that content contains (or avoids) specified keywords/phrases."""

    def __init__(
        self,
        name: str = "content",
        required: Optional[Sequence[str]] = None,
        forbidden: Optional[Sequence[str]] = None,
        case_sensitive: bool = False,
    ) -> None:
        super().__init__(name)
        self.required = list(required or [])
        self.forbidden = list(forbidden or [])
        self.case_sensitive = case_sensitive

    def run(self, item: Any) -> CheckResult:
        text = str(item)
        search_text = text if self.case_sensitive else text.lower()
        failures: List[str] = []

        found_required = 0
        for kw in self.required:
            kw_search = kw if self.case_sensitive else kw.lower()
            if kw_search in search_text:
                found_required += 1

        for kw in self.forbidden:
            kw_search = kw if self.case_sensitive else kw.lower()
            if kw_search in search_text:
                failures.append(f"contains forbidden '{kw}'")

        if failures:
            return CheckResult(score=0.0, passed=False, message="; ".join(failures))

        if self.required:
            score = found_required / len(self.required)
            passed = score == 1.0
            return CheckResult(
                score=round(score, 4), passed=passed,
                message=f"found {found_required}/{len(self.required)} required keywords",
            )

        return CheckResult(score=1.0, passed=True, message="no content violations")


class CustomCheck(Check):
    """Run an arbitrary callable as a check."""

    def __init__(
        self,
        name: str,
        fn: Callable[[Any], CheckResult],
    ) -> None:
        super().__init__(name)
        self.fn = fn

    def run(self, item: Any) -> CheckResult:
        return self.fn(item)
