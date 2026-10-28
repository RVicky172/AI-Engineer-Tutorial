# M10 · Observability and Production Troubleshooting

**Priority:** Must have · **Roadmap week:** 7

Production troubleshooting is core to the role. The strongest candidates can explain how they find root cause in minutes.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: End-to-end OpenTelemetry traces for an agent](labs/lab-01-otel-tracing/README.md)
- [ ] [Lab 02: Agent dashboard and alarms](labs/lab-02-cloudwatch-dashboard-alarms/README.md)
- [ ] [Lab 03: Game day: five faults, timed diagnosis](labs/lab-03-game-day/README.md)

## Self-check (answer aloud, no notes)
- [ ] Users report the agent is slow only in the afternoon. How do you investigate?
- [ ] The agent answers confidently but incorrectly after a release. What do you compare?

## Folder layout
```
M10-observability/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-otel-tracing/
    ├── lab-02-cloudwatch-dashboard-alarms/
    └── lab-03-game-day/
```
