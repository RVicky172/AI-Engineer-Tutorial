# M02 · LLM Fundamentals, Prompting, Tool Calling and Structured Outputs

**Priority:** Must have · **Roadmap week:** 1

Every agent issue eventually traces to the model, the prompt, or the tool contract. You need to reason about all three.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
Reference solutions are built and tested offline. Read [LEARNINGS.md](LEARNINGS.md) after the labs; run every offline check with `labs/check.sh` (live runs: see [labs/SETUP.md](labs/SETUP.md)).

- [ ] [Lab 01: One extraction task, three techniques](labs/lab-01-extraction-three-ways/README.md)
- [ ] [Lab 02: Tool design for an IT-support agent](labs/lab-02-tool-design-it-support/README.md)
- [ ] [Lab 03: Prompt regression suite](labs/lab-03-prompt-regression-suite/README.md)

## Self-check (answer aloud, no notes)
- [ ] Why would a model repeatedly call the wrong tool, and how do you fix it without changing the model?
- [ ] How do you reduce token spend on a long-running agent session by 40%?

## Folder layout
```
M02-llm-fundamentals/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
├── LEARNINGS.md       ← cross-lab lessons
└── labs/
    ├── SETUP.md       ← environment setup
    ├── check.sh       ← every offline quality gate
    ├── common/        ← llm_common: provider switch, cost tally, fake model
    ├── lab-01-extraction-three-ways/
    ├── lab-02-tool-design-it-support/
    └── lab-03-prompt-regression-suite/
```
