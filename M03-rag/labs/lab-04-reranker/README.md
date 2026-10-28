# M03 · Lab 04: Add a reranker and measure it

> Module: [RAG: Retrieval-Augmented Generation](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Add a reranker and measure the change in retrieval and answer quality on the 25-question golden set.

## Steps
1. Retrieve top-20 candidates, rerank to top-5.
2. Option A: local cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`). Option B: a Bedrock rerank model (check availability in your region).
3. Measure recall@5, MRR and added latency.
4. Score answer quality (manual 1-5 or LLM-as-judge) before and after.

## Done when
- [ ] Before/after table with quality and latency
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Find 3 questions where reranking made things worse and explain why.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
