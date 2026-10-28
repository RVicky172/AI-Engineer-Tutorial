# M03 · RAG: Retrieval-Augmented Generation — Study Guide

> **Priority:** Must have · **Week:** 2 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Almost every customer deployment connects the agent to private knowledge: runbooks, tickets, wikis, policies. The model can only be as good as what you retrieve. **Retrieval quality decides answer quality.**

## Learning objectives
- Describe every stage of a RAG pipeline and what can go wrong at each.
- Choose a chunking strategy, embedding model and vector store for a given corpus.
- Implement hybrid search, metadata filters and reranking.
- Enforce document-level access control at retrieval time.
- Measure retrieval and answer quality with a golden set.

---

## 1. The pipeline
```
INGEST:  source → parse → clean → chunk → embed → index (+ metadata)
QUERY:   question → (rewrite) → retrieve top-k → filter → rerank → build prompt → generate → cite
```

| Stage | Decisions | Typical problems |
|---|---|---|
| Parse | PDF/HTML/Office extraction, tables, images | broken tables, headers/footers repeated, lost structure |
| Chunk | size, overlap, strategy | answers split across chunks, chunks too generic |
| Embed | model, dimensions, normalisation | domain vocabulary poorly represented, model mismatch between index and query |
| Index | vector store, index type (HNSW/IVF), metadata | stale data, no filters, duplicate docs |
| Retrieve | k, similarity metric, hybrid | relevant chunk ranked 12th |
| Rerank | cross-encoder / rerank model | latency cost |
| Generate | prompt, citations, "don't know" behaviour | ignores context, mixes sources, hallucinated citations |

## 2. Chunking strategies
| Strategy | How | Good for |
|---|---|---|
| Fixed size | N tokens with overlap (10-20%) | baseline, uniform text |
| Recursive | split on headings → paragraphs → sentences until under size | Markdown, docs with structure |
| Semantic | split where embedding similarity between sentences drops | long prose with topic shifts |
| Hierarchical (parent-child) | embed small chunks, return their larger parent | precise matching + enough context |

Rules of thumb: keep the title/section heading in each chunk (contextual header); never split tables mid-row; store `doc_id`, `section`, `updated_at`, and ACL metadata. **Measure** — chunk size is an empirical choice (Lab 01).

## 3. Embeddings and vector search
- An embedding model maps text to a vector; similar meaning → nearby vectors (cosine similarity).
- Use the **same model** for documents and queries. Changing the model means re-embedding everything.
- **ANN indexes** (HNSW in pgvector/OpenSearch) trade a little recall for big speed.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE chunks (
  id bigserial PRIMARY KEY, doc_id text, chunk_text text,
  metadata jsonb, allowed_groups text[], embedding vector(1024)
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);

SELECT doc_id, chunk_text, 1 - (embedding <=> %(q)s) AS score
FROM chunks
WHERE allowed_groups && %(user_groups)s          -- filter first
ORDER BY embedding <=> %(q)s
LIMIT 5;
```

**Hybrid search:** vectors are great at meaning, bad at exact identifiers (error codes, hostnames, `INC0012345`). BM25/keyword is the opposite. Combine with **Reciprocal Rank Fusion**: `score = Σ 1 / (60 + rank_i)`.

**Reranking:** retrieve 20-50 candidates cheaply, then a cross-encoder or rerank model scores each (query, chunk) pair jointly and keeps the top 5. Usually the biggest quality jump for the effort.

## 4. Stores on AWS
| Option | When |
|---|---|
| **pgvector** on RDS/Aurora PostgreSQL | you already run Postgres; want SQL + vectors + ACL joins in one place |
| **OpenSearch** (managed or Serverless) | large scale, hybrid search built in, existing OpenSearch skills |
| **Bedrock Knowledge Bases** | managed ingestion/chunking/sync + Retrieve/RetrieveAndGenerate APIs; less control, faster start. Supports several vector store back-ends — check current options and pricing |

## 5. Access control in RAG
- Attach ACL metadata (`allowed_groups`, `tenant_id`) to every chunk at ingestion, from the source system's permissions.
- **Filter inside the query, before top-k.** Post-filtering leaks (data reaches your process) and hurts recall (top-5 might all be filtered out).
- The user's identity/groups come from the **authenticated request**, never from the model or prompt.
- Multi-tenant: separate indexes or mandatory tenant filter; test for leakage explicitly.
- Keep ACLs in sync when source permissions change.

## 6. Evaluation
Build a **golden set**: 25-100 real questions with the IDs of relevant documents and a reference answer.

| Metric | Measures |
|---|---|
| **recall@k** | fraction of questions where a relevant doc appears in the top k |
| **MRR** | mean of 1/rank of the first relevant result |
| **Faithfulness / groundedness** | is every claim in the answer supported by retrieved context? |
| **Answer relevance** | does the answer address the question? |

Evaluate retrieval and generation **separately** — that's how you know which half to fix.

## 7. Common problems and fixes
| Problem | Fix |
|---|---|
| Stale index | incremental sync on change events (S3 events, CDC, webhooks); `updated_at` metadata; scheduled full re-sync |
| Bad chunk boundaries | recursive/heading-aware chunking, overlap, parent-child |
| Tables and PDFs | layout-aware parsers; convert tables to Markdown; chunk per table |
| Duplicate content | hash-based dedup at ingestion; prefer latest version |
| Long-context stuffing | more chunks ≠ better: models miss facts in the middle and cost rises; rerank and send fewer, better chunks |
| Exact IDs not found | hybrid search with BM25 |

---

## Self-check (try first, then open)
<details><summary>Retrieval returns the right document but the answer is wrong. Where do you look?</summary>

Check: is the right **chunk** (not just document) in the context and near the top? Was it truncated by context limits? Is the prompt telling the model to use only the context and cite? Are conflicting/outdated chunks also present? Is the model ignoring context due to strong prior knowledge? Check faithfulness score, look at the exact prompt sent (trace), test with fewer/better-ordered chunks, and try a stronger model as a comparison.
</details>

<details><summary>How do you keep a vector index fresh when source documents change daily?</summary>

Event-driven incremental ingestion: on create/update/delete in the source (S3 events, webhook, CDC), re-chunk and re-embed only that document, delete its old chunks by `doc_id`, update ACL metadata. Add a periodic reconciliation job comparing source hashes/`updated_at` vs. index. Monitor freshness lag as a metric. With Bedrock Knowledge Bases, trigger data source sync (ingestion jobs) on change.
</details>

## Resources
- pgvector README (index types, operators)
- Amazon Bedrock User Guide: Knowledge Bases (chunking, metadata filtering, Retrieve API)
- Amazon OpenSearch Service docs: k-NN and hybrid search
- Papers/blogs: Reciprocal Rank Fusion; "Lost in the Middle" (long-context behaviour); Anthropic "Contextual Retrieval"

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-pgvector-rag-chunking/README.md)
