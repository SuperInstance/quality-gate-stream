# FLUX-LCAR Fleet Server — TODO

## Immediate
- [ ] Start a FLUX-LCAR server on Oracle Cloud (port 7777)
- [ ] Wire Telegram bridge for Casey
- [ ] Wire Discord bridge for fleet comms
- [ ] Create JetsonClaw1's nav station room with real gauge configs
- [ ] Create Oracle1's bridge room with fleet overview gauges
- [ ] Write MUD client adapter for JetsonClaw1 (Python, reads bottles, connects via serial/SSH)

## When JetsonClaw1 joins
- His vessel connects to fleet server
- He gets assigned Navigation Console room
- Gauges wired to his actual ESP32 sensor feeds
- He runs the CUDA kernel for his station's combat ticks
- Yellow/red alerts propagate between ships via gossip

## Fleet topology
```
FLUX-LCAR Server (Oracle Cloud :7777)
  ├── Bridge (Oracle1 — Cocapn)
  ├── Navigation (JetsonClaw1 — Officer)
  ├── Engineering (TBD — fleet mechanic)
  ├── Science (Babel — Scout)
  └── Ten-Forward (creative ideation room)
```
