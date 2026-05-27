"""ThresholdConfig — configurable limits for gate scoring."""

from dataclasses import dataclass


@dataclass
class ThresholdConfig:
    """Thresholds that map aggregate scores to pass / warn / fail.

    * ``pass_threshold`` — score >= this → PASS
    * ``warn_threshold`` — score >= this but < pass_threshold → WARN
    * Anything below ``warn_threshold`` → FAIL
    """

    pass_threshold: float = 0.8
    warn_threshold: float = 0.5

    def __post_init__(self) -> None:
        if not (0.0 <= self.warn_threshold <= self.pass_threshold <= 1.0):
            raise ValueError(
                f"Thresholds must satisfy 0.0 <= warn ({self.warn_threshold}) "
                f"<= pass ({self.pass_threshold}) <= 1.0"
            )
