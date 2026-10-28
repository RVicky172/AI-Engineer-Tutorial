# M03 · Lab 02: Same corpus on Amazon Bedrock Knowledge Bases

> Module: [RAG: Retrieval-Augmented Generation](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)
>
> **Reference solution included** (`src/`, `tests/`, `NOTES.md`): create, query and tear down scripts, tested offline. Running it creates billable AWS resources; read `NOTES.md` first.

## Goal
Repeat the corpus with Bedrock Knowledge Bases and compare setup effort, quality and cost with your pgvector build.

## Steps
1. Upload the corpus to an S3 bucket (with `.metadata.json` sidecar files for metadata).
2. Create a Knowledge Base; choose a low-cost vector store option available in your region and note the price of each option first.
3. Sync the data source and check ingestion errors.
4. Query with the `Retrieve` and `RetrieveAndGenerate` APIs from boto3 (`bedrock-agent-runtime`).
5. Run the same golden set; compute recall@5.
6. Fill in the comparison table: setup time, recall, latency, monthly cost estimate, control/flexibility.
7. DELETE the Knowledge Base and its vector store when done (some vector stores bill per hour).

## Done when
- [ ] Comparison table pgvector vs Knowledge Bases
- [ ] All billable resources deleted (screenshot or CLI output)
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Try a different chunking strategy (hierarchical or semantic) in the KB and re-measure.

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
