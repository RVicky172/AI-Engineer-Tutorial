# M03 · Lab 01: RAG pipeline on pgvector + chunk-size experiment

> Module: [RAG: Retrieval-Augmented Generation](../../README.md) · Study first: [docs/guide.md](../../docs/guide.md) · Environment: [labs/SETUP.md](../SETUP.md)

## Goal
Build a RAG pipeline over 50-100 internal-style documents using pgvector. Compare 3 chunk sizes and report recall@5 for each.

## Steps
1. Create a corpus in `corpus/`: 50-100 runbooks, KB articles and resolved-ticket write-ups (Markdown is fine; include a few PDFs and tables).
2. Write a 25-question golden set `golden.yaml`: question, relevant doc IDs, reference answer.
3. Ingestion: parse -> chunk -> embed -> insert into a table with `embedding vector(N)`, `doc_id`, `chunk_text`, `metadata jsonb`.
4. Create an HNSW index (`USING hnsw (embedding vector_cosine_ops)`).
5. Run three configurations (e.g. 256 / 512 / 1024 tokens, 10-15% overlap) into separate tables.
6. Compute recall@5 and MRR for each configuration on the golden set.
7. Add generation: answer using the top-k chunks and cite `doc_id`s.

## Done when
- [ ] `results.md` with recall@5 and MRR per chunk size
- [ ] Answers include citations that point at real documents
- [ ] `NOTES.md` in this folder explains what you built, what broke, and what you would do differently

## Stretch
Add BM25 (rank-bm25 or PostgreSQL full-text) and combine with vectors using Reciprocal Rank Fusion. Does hybrid beat vector-only?

## Your work
Put your code in this folder (e.g. `src/`, `tests/`). Keep a short `NOTES.md` here:

```markdown
## What I built
## Commands to run it
## Results / numbers
## What broke and how I fixed it
## What I'd explain in an interview
```
