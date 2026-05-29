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

## License

MIT
