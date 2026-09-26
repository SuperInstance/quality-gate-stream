# quality-gate-stream

**Streaming quality gates** — continuous quality scoring for data streams, agent outputs, and pipeline results. Score, filter, and route based on configurable quality thresholds.

## What This Gives You

- **Stream scoring** — evaluate quality of data as it flows through pipelines
- **Configurable gates** — define quality thresholds with pass/fail/warn outcomes
- **Multi-metric** — composite scoring from multiple quality signals
- **Routing** — route items to different paths based on quality scores
- **Aggregation** — rolling quality statistics over configurable windows

## Installation

```bash
pip install quality-gate-stream
```

## How It Fits

Quality assurance layer in the SuperInstance fleet. Scores agent outputs from `plato-training`, validates data from `conservation-spectral`, and gates deployments in the CI pipeline.

## Quick Start

```python
from quality_gate import (QualityGate, GateStream, ThresholdConfig,
                          ContentCheck, LengthCheck, FormatCheck)
from quality_gate.gate import GateOutcome

gate = QualityGate(
    "agent-output",
    checks=[
        LengthCheck(min_length=20, max_length=4000, sweet_spot=(100, 2000)),
        ContentCheck(required=["analysis"], forbidden=["TODO"]),
        FormatCheck(pattern=r"^[^\n]+\n"),           # non-empty first line
    ],
    threshold=ThresholdConfig(pass_threshold=0.8, warn_threshold=0.5),
    strict=True,                                      # any hard failure fails the gate
)
gate.add_check(FormatCheck("no-stacktrace", pattern=r"Traceback", must_match=False))

stream = GateStream([gate])
report = stream.process_and_report(agent_outputs)
print(report.summary())                               # ✅ / ⚠️ / ❌ counts
print(report.rolling_pass_rate(window=50))            # rolling quality window

# route by outcome: retry FAILs, promote PASSes, sample WARNs
buckets = stream.partition(agent_outputs)
retry_queue   = buckets[GateOutcome.FAIL]
promoted      = buckets[GateOutcome.PASS]
```

## API

- `QualityGate(name, checks, weights, threshold, strict)` — composite scoring over checks; `strict=True` fails the gate on any hard-failed check (no dilution)
- `GateStream(gates, fail_fast)` — ordered pipeline; `partition(items)` routes by outcome; `process_and_report(items)` rolls up
- `GateReport` — pass/warn/fail counts, per-gate score history, `rolling_pass_rate(window)`
- `ThresholdConfig(pass_threshold, warn_threshold)` — score bands with validation
- Checks: `LengthCheck`, `FormatCheck`, `ContentCheck`, `CustomCheck`

Check names within a gate must be unique — duplicate names raise `ValueError` instead of silently corrupting weights.

## License

MIT
