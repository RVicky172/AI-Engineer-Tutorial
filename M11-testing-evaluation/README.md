# M11 · Testing and Evaluation of Agentic Systems

**Priority:** Must have · **Roadmap week:** 7

The job description lists functional, integration, security, performance, resiliency, evaluation and user acceptance testing before rollout.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: 40-case scenario evaluation gated in CI](labs/lab-01-scenario-eval-ci/README.md)
- [ ] [Lab 02: LLM-as-judge vs your own scoring](labs/lab-02-llm-judge-calibration/README.md)
- [ ] [Lab 03: Load test with 50 concurrent users](labs/lab-03-load-test/README.md)

## Self-check (answer aloud, no notes)
- [ ] How do you know a prompt change made the agent better rather than just different?
- [ ] What are the limits of LLM-as-judge?

## Folder layout
```
M11-testing-evaluation/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-scenario-eval-ci/
    ├── lab-02-llm-judge-calibration/
    └── lab-03-load-test/
```
