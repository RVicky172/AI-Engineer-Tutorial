# Lab 04 Notes — Add a reranker and measure it

## What I built
A second retrieval stage: take the first stage's top 20, score each (question, chunk) pair with a cross-encoder, keep the top 5. Measured before and after on the golden set, for both vector and hybrid first stages.

```
src/rerank/
├── rerankers.py   CrossEncoderReranker (Option A, local), BedrockReranker (Option B, Rerank API),
│                  LexicalReranker (tests and a baseline a real reranker must beat)
├── experiment.py  compare(): same 20 candidates -> before (top 10) vs after (reranked top 10),
│                  rerank latency, and worse() for the stretch goal
├── judge.py       LLM-as-judge: 1-5 against the reference answer, structured output
├── report.py      results.md
└── cli.py         python -m rerank run | answers
tests/             8 tests, 98% coverage; the Bedrock request is validated by botocore's Stubber
```

**Why two stages:** the embedder (a bi-encoder) turns question and chunk into vectors *separately*, so one pass over the corpus is cheap, but it never sees them together. A cross-encoder reads the question and chunk as *one* input, and is far more accurate at judging relevance, but needs a model call per chunk. So: cheap recall over everything, expensive precision over 20.

## Commands to run it
```bash
cd M03-rag/labs && docker compose up -d && source .venv/bin/activate
cd lab-04-reranker
pytest
python -m rerank run                         # live, local models, ~1 min, $0 -> results.md
python -m rerank answers --limit 5           # answers + judge, before/after (calls Claude)
python -m rerank --reranker bedrock --bedrock-model-arn arn:aws:bedrock:us-west-2::foundation-model/amazon.rerank-v1:0 run
```

## Results / numbers
Measured 2026-10-28: bge-small first stage, `cross-encoder/ms-marco-MiniLM-L-6-v2` on CPU, 256-token chunks, 20 candidates → top 5. Full report: [results.md](results.md).

| Config | evidence@5 | coverage@5 | MRR | Added latency p50 / p95 |
|---|---|---|---|---|
| vector | 96% | 90% | 0.86 | |
| **vector + rerank** | **100%** | 94% | **0.96** | 126 / 143 ms |
| hybrid | 100% | 96% | 0.95 | |
| **hybrid + rerank** | 100% | 94% | 0.96 | 127 / 149 ms |

(recall@5 is 100% in every row; see Lab 01 for why it's saturated.)

1. **Reranking turns plain vector search into something as good as hybrid**: MRR 0.86 → 0.96. Most of the gain is the first relevant chunk moving from rank 2-4 to rank 1.
2. **It fixes the stale-document problem from Lab 01.** q17 ("P2 response target"): the current policy moves from rank 4 to rank 1, above the superseded 2024 version. The cross-encoder reads "response target for a P2" against "30 minutes, business hours" in the current table, instead of comparing two nearly identical document vectors.
3. **On top of hybrid, the gain is small** (0.95 → 0.96) and it costs coverage (96% → 94%). Hybrid had already fixed most rankings.
4. **The cost is ~125 ms per question on a laptop CPU**, for 20 pairs. That's acceptable for a chat assistant, but it's per question: it scales with candidates, not corpus size.

**What I'd ship:** hybrid first stage, and add the reranker only if answer-quality evals (`answers`) show it helps. On retrieval metrics alone, hybrid without reranking is nearly as good and 125 ms faster.

### Stretch: where reranking made things worse
Two questions, under both first stages; I looked for three and there were only two.
- **q23** "How long do we keep daily backups of the file server?" The relevant runbook falls from rank 1 to 2, below the September *backup failure* incident. The incident is all about daily backups of the file server, so it matches the question's words better, but it never states the retention period. The cross-encoder was trained on MS MARCO (web search: "does this passage answer the query?"), and in that data, passages dense with the query's terms usually are the answer.
- **q06** "Can I restart the ERP servers during month-end close?" (hybrid) It pushes the change-management policy (which says "no normal changes to ERP during close") out of the top 5, so coverage drops from 100% to 50%. The runbook chunk and two ERP incident chunks all talk about restarting the ERP and score higher. The policy talks about changes in general, and the model doesn't know a restart is a change. Half of a two-document answer is lost.

Both are the same failure: **term-dense but non-answering chunks beat the answer-bearing chunk.** Fixes: a reranker fine-tuned on in-domain pairs, adding the doc type ("policy", "incident") to the chunk header, or keeping one chunk per document in the top 5 (diversity).

### Answer quality (not run yet)
`python -m rerank answers` generates an answer from the top 5 before and after reranking, then has Claude grade both against the reference answer (1-5, structured output). It's built and tested offline, but **not run live**: no Claude credentials on this machine. Fill in: mean score before __ → after __. Then hand-check 5 grades. A judge is a model too, and "partly correct" vs "mostly correct" is where judges disagree with people.

## What broke and how I fixed it
- **"Worse" missed a real regression.** My first definition only checked the rank of the first relevant chunk and lost evidence. Hybrid's coverage dropped (96% → 94%) yet `worse()` listed only q23. q06 lost one of its two relevant documents, which "first relevant rank" can't see. Coverage drops now count.
- **The Bedrock request shape is easy to get wrong** (`inlineDocumentSource`, `textDocument`, `bedrockRerankingConfiguration`). The test runs the real boto3 client with botocore's `Stubber`, which validates every parameter against the service's API model offline. A typo fails the test, not the first billed call.
- **Shared code moved into `ragkit`.** Lab 04 needed Lab 01's three-way retriever; copying it a third time would have meant three copies to fix. `ragkit.retrieval` (Mode, Retriever) and `ragkit.store.build_table` are now shared by Labs 01, 03 and 04.

## What I'd explain in an interview
1. **Bi-encoder for recall, cross-encoder for precision.** Embeddings scale to millions of chunks because each is encoded once; a cross-encoder scores each pair with the question, so you only run it on a short list.
2. **Measure the latency budget, not just quality.** +125 ms p50 / +145 ms p95 for 20 candidates on CPU. Halve the candidates and it roughly halves.
3. **Rerankers have a training distribution.** MS MARCO is web search. Chunks that repeat the question's words without answering it beat the real answer. Read the regressions, not just the average.
4. **Evaluate retrieval and answers separately.** Retrieval gains (MRR +0.10) don't automatically become answer gains if the answer chunk was already in the top 5; that's why `answers` exists.

## Improve it yourself
1. Run `answers` for all 25 questions and hand-check 5 judge scores.
2. Try `cross-encoder/ms-marco-MiniLM-L-12-v2` or `BAAI/bge-reranker-base`: is the extra latency worth it?
3. Rerank 10 instead of 20 candidates: what do you lose?
4. Add the document type to every chunk's header ("Policy: Change management") and re-run: does q06 recover?
5. Option B on Bedrock (`amazon.rerank-v1:0` or Cohere Rerank 3.5) in a region that has it: compare quality, latency and price per 1,000 queries.
