# Lab 01 Notes — RAG pipeline on pgvector + chunk-size experiment

## What I built
An ingestion and retrieval pipeline over a 77-document IT corpus in PostgreSQL + pgvector, measured on a 25-question golden set at three chunk sizes and with three retrieval modes, plus cited answer generation.

```
labs/corpus/              77 docs: runbooks, KB articles, incident write-ups, policies, 3 PDFs,
                          restricted finance/HR/security docs, and 12 deliberate distractors
labs/golden.yaml          25 questions: relevant doc ids, an exact evidence phrase, reference answer
labs/common/ (ragkit)     shared by every M03 lab
├── corpus.py      Markdown front matter + PDFs with .meta.yaml sidecars (like KB .metadata.json)
├── chunking.py    heading-aware packing to a token budget, tables kept whole, title header, overlap
├── embedding.py   LocalEmbedder (bge-small, free), TitanEmbedder (Bedrock), HashEmbedder (tests)
├── store.py       pgvector table per config, HNSW cosine index, ACL filter inside the SQL
├── hybrid.py      BM25 with an identifier-preserving tokenizer, Reciprocal Rank Fusion
├── metrics.py     recall@k, evidence@k, coverage@k, MRR
└── generation.py  answers that cite [doc_id], and a check that every citation was in the context
lab-01-pgvector-rag-chunking/src/rag_pipeline/
├── pipeline.py    ingest() per chunk size; Retriever: vector | bm25 | hybrid; evaluate()
├── report.py      results.md
└── cli.py         python -m rag_pipeline run | ask | answer-golden
```

## Commands to run it
```bash
cd M03-rag/labs && docker compose up -d && source .venv/bin/activate
./check.sh                                         # all offline gates (needs the container)

cd lab-01-pgvector-rag-chunking
python -m rag_pipeline run                         # ingest 128/256/512, evaluate 3 modes: ~1 min, $0
python -m rag_pipeline ask "What does VPN-ERR-812 mean?"        # calls the model
python -m rag_pipeline answer-golden --limit 5     # cited answers for the golden set -> answers.md
python -m rag_pipeline --embedder titan run        # same experiment on Bedrock Titan (billed)
```

## Results / numbers
Measured 2026-10-28 with `BAAI/bge-small-en-v1.5` (local, CPU), 12% overlap. Full table: [results.md](results.md).

| Config | recall@5 | evidence@5 | coverage@5 | MRR |
|---|---|---|---|---|
| 128 vector | 100% | 92% | 90% | 0.91 |
| 128 hybrid | 100% | 92% | 94% | **1.00** |
| 256 vector | 100% | 96% | 90% | 0.86 |
| 256 hybrid | 100% | **100%** | 96% | 0.95 |
| 512 vector | 100% | 96% | 94% | 0.86 |
| 512 hybrid | 100% | **100%** | **98%** | 0.95 |

Ingestion: 266 / 123 / 79 chunks, under 2 s each. Query latency is about 8 ms (p50) for vector or hybrid search, under 1 ms for BM25 alone.

**What I'd ship: 256-token chunks with hybrid retrieval.** It is the smallest size where the answer-bearing chunk is in the top 5 for every question, and hybrid fixes vector search's worst rankings.

1. **recall@5 is saturated and therefore useless here.** Every config finds a relevant document for every question; on a 77-doc corpus that's easy. The stricter **evidence@5** (does a retrieved *chunk* contain the answer?) is what separates the configs.
2. **Small chunks rank better but miss evidence.** At 128 tokens MRR is highest, but for 2 of 25 questions no top-5 chunk contains the answer phrase (read those rows in results.md to see whether the answer was split or outranked). At 256 and above, every answer-bearing chunk makes the top 5 with hybrid.
3. **Hybrid wins at every size.** It never ranks worse than its parts on average, and it fixes vector search's worst cases: q25 ("paste a customer list into a public AI chatbot?") is rank 3-5 with vectors and rank 1 with hybrid, because "AI tools" and "Confidential" are exact words in the policy.
4. **A stale document outranks the current one.** For q17 ("P2 response target"), vector search ranks the *superseded* 2024 policy (P2 = 1 hour) above the 2026 one (P2 = 30 minutes). The metric still counts a hit because the right doc is in the top 5, but the model now sees two contradicting answers. Fix: filter on `status != superseded` at ingestion or query time.
5. **Unfiltered retrieval leaks.** Asked as an ordinary employee, q17 and q25 retrieve chunks of the security team's incident-response playbook and the restricted phishing-incident report. That's Lab 03's problem.

`answer-golden` (cited answers) is built and tested offline but **not run live**: no Claude credentials on this machine. Run it, then fill in: citations valid __/25, answers matching the reference __/25.

## What broke and how I fixed it
- **The first experiment couldn't tell configs apart.** Docs are 140-620 tokens, so at 512 and 1024 tokens almost every doc was a single chunk: identical results. Chunk sizes must be chosen relative to *your* documents; the experiment now uses 128/256/512.
- **The first golden set was too easy: 100% everywhere.** A clean corpus with no near-duplicates is unrealistic. I added 12 distractors (superseded policies, older runbooks, neighbouring topics) and an exact `evidence` phrase per question. `check_evidence` fails the run if a phrase is not in a relevant doc, so a typo can't silently zero a question.
- **Overlap vanished inside long blocks** (caught by a unit test). Pieces of a split block were sized to the full budget, so the previous chunk's tail never fitted and was dropped exactly where overlap matters. Pieces now leave room for twice the overlap.
- **Overlap cut table rows in half.** A word-level tail produced fragments like `get duplicate reminders | |`. The tail is now whole lines.
- **A split table lost its header.** `| AR_DUNNING | 03:00 | no |` means nothing without its column names. Every piece of a split table repeats the header row.
- **YAML front matter with a colon** (`title: First day: set up your laptop`) crashed ingestion with a parser error that didn't say which file. Errors now name the file; one bad document in 10,000 must be findable.

## What I'd explain in an interview
1. **Evaluate retrieval separately from generation.** Retrieval metrics are free, exact and fast (this run took a minute and cost nothing). Only then spend model calls on answer quality.
2. **Pick metrics that can fail.** recall@5 at 100% for every config means the metric, not the system, is the problem. evidence@k checks the actual chunk.
3. **Chunk size is relative to document length and the embedder's input limit.** bge-small reads 512 tokens; a 1024-token chunk would be silently truncated. The report counts chunks longer than the model reads.
4. **Hybrid search because users type identifiers.** `VPN-ERR-812`, `INC0011207`, `AR_DUNNING`: the BM25 tokenizer keeps them whole, and RRF fuses rankings without calibrating scores.
5. **Stale and duplicate content is a retrieval bug, not a model bug.** Metadata (`status`, `updated`) at ingestion lets you filter or prefer current documents.
6. **Citations must be checked, not trusted.** `check_citations` fails any answer that cites a document the model was never shown.

## Improve it yourself
1. Filter `status: superseded` out of retrieval and re-measure q17. Then think about the opposite case: when do you *want* the old version?
2. Run the experiment with `--embedder titan` and compare (Lab 02 needs those numbers anyway).
3. Add parent-child retrieval: embed the 128-token chunks, return their 512-token parent. Do you keep 128's MRR and gain 512's evidence@5?
4. Compare HNSW with exact search (drop the index): does the approximate index cost any recall at this size?
5. Write 10 more golden questions from real user wording (ticket subjects), not from the documents.
