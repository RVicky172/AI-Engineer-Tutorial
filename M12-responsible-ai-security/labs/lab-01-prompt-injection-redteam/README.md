# M12 · Lab 01: Prompt-injection red team

> Module: [Responsible AI, Security and Data Protection](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Write 15 prompt-injection attacks (including ones hidden in retrieved documents) and run them against your agent; fix each one that succeeds.

## Steps
1. Categories: direct override, role-play/jailbreak, encoded (base64/unicode), indirect via KB document, indirect via ticket comment, tool-argument injection, data exfiltration via URL/markdown image, excessive-action requests.
2. Plant indirect attacks in your RAG corpus and mock ticket data.
3. Harness: run each attack, record whether the attack goal happened (tool called, data leaked, rule ignored).
4. Mitigate: delimit/label untrusted content, tool allow-lists, approval for writes, guardrail prompt-attack filter, output sanitisation, least-privilege tools.
5. Re-run and record residual risk.

## Done when
- [ ] `redteam-report.md`: attack, result before, mitigation, result after
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add the attacks to your CI eval suite from M11.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
