# Lab 01 results: chunk size and retrieval mode

Embedder: `BAAI/bge-small-en-v1.5` (384 dims, reads 512 tokens) · overlap 12% · corpus 77 docs · run 2026-10-28 16:21 UTC

## Ingestion

| Chunk size (tokens) | Chunks | Avg tokens | Longer than the model reads | Ingest (s) |
|---|---|---|---|---|
| 128 | 266 | 98 | 0 | 1.7 |
| 256 | 123 | 183 | 0 | 1.6 |
| 512 | 79 | 257 | 0 | 1.7 |

## Retrieval (25 golden questions)

recall@5: a relevant document is among the top 5 chunks. evidence@5: a top-5 chunk contains the answer phrase (stricter). coverage@5: share of all relevant documents found (matters for multi-doc questions). MRR over the top 10.

| Config | recall@5 | evidence@5 | coverage@5 | MRR | p50 latency (ms) | keyword hits | multi hits | paraphrase hits | pdf hits |
|---|---|---|---|---|---|---|---|---|---|
| 128 vector | 100% | 92% | 90% | 0.91 | 8 | 6/6 | 7/7 | 7/7 | 3/3 |
| 128 bm25 | 100% | 92% | 92% | 0.94 | 0 | 6/6 | 7/7 | 7/7 | 3/3 |
| 128 hybrid | 100% | 92% | 94% | 1.00 | 9 | 6/6 | 7/7 | 7/7 | 3/3 |
| 256 vector | 100% | 96% | 90% | 0.86 | 7 | 6/6 | 7/7 | 7/7 | 3/3 |
| 256 bm25 | 100% | 92% | 96% | 0.89 | 0 | 6/6 | 7/7 | 7/7 | 3/3 |
| 256 hybrid | 100% | 100% | 96% | 0.95 | 8 | 6/6 | 7/7 | 7/7 | 3/3 |
| 512 vector | 100% | 96% | 94% | 0.86 | 7 | 6/6 | 7/7 | 7/7 | 3/3 |
| 512 bm25 | 100% | 100% | 96% | 0.88 | 0 | 6/6 | 7/7 | 7/7 | 3/3 |
| 512 hybrid | 100% | 100% | 98% | 0.95 | 8 | 6/6 | 7/7 | 7/7 | 3/3 |

## Rank of the first relevant chunk per question

`-` means no relevant chunk in the top 10. Rows where any config misses the top 5 are the ones to read.

| Question | Tags | 128 vector | 128 bm25 | 128 hybrid | 256 vector | 256 bm25 | 256 hybrid | 512 vector | 512 bm25 | 512 hybrid |
|---|---|---|---|---|---|---|---|---|---|---|
| q01 | keyword | 1 | 1 | 1 | 1 | 5 | 1 | 1 | 5 | 1 |
| q02 | paraphrase | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 4 | 3 |
| q03 | paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q04 | paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q05 | keyword, multi | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q06 | multi | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 |
| q07 | keyword | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q08 | keyword | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q09 | paraphrase | 2 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 |
| q10 | multi | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q11 | keyword | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q12 | multi, paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q13 | paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q14 | paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q15 | keyword | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 |
| q16 |  | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q17 |  | 1 | 2 | 1 | 4 | 2 | 4 | 4 | 2 | 3 |
| q18 | pdf | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 2 | 1 |
| q19 | pdf | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q20 | pdf | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q21 | multi | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q22 | multi | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q23 |  | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 2 | 1 |
| q24 |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| q25 | multi | 4 | 1 | 1 | 3 | 1 | 1 | 5 | 1 | 1 |

## Conclusion

_Which chunk size and mode would you ship, and why? Which question types does each mode miss? Read the misses before trusting the averages: 1 question is 4 points here._
