# Lab 04 results: reranking the top 20 down to 5

Embedder `BAAI/bge-small-en-v1.5` · reranker `cross-encoder/ms-marco-MiniLM-L-6-v2` · 256-token chunks · 20 candidates -> top 5 · run 2026-10-28 16:41 UTC

## Retrieval before and after

| Config | recall@5 | evidence@5 | coverage@5 | MRR | Rerank p50 (ms) | Rerank p95 (ms) |
|---|---|---|---|---|---|---|
| vector | 100% | 96% | 90% | 0.86 | - | - |
| **vector + rerank** | 100% | 100% | 94% | 0.96 | 126 | 148 |
| hybrid | 100% | 100% | 96% | 0.95 | - | - |
| **hybrid + rerank** | 100% | 100% | 94% | 0.96 | 127 | 161 |

## Rank of the first relevant chunk: before -> after

| Question | Tags | vector | hybrid |
|---|---|---|---|
| q01 | keyword | 1 -> 1 | 1 -> 1 |
| q02 | paraphrase | 2 -> 2 | 2 -> 2 |
| q03 | paraphrase | 1 -> 1 | 1 -> 1 |
| q04 | paraphrase | 1 -> 1 | 1 -> 1 |
| q05 | keyword, multi | 1 -> 1 | 1 -> 1 |
| q06 | multi | 2 -> 1 | 1 -> 1 |
| q07 | keyword | 1 -> 1 | 1 -> 1 |
| q08 | keyword | 1 -> 1 | 1 -> 1 |
| q09 | paraphrase | 2 -> 1 | 1 -> 1 |
| q10 | multi | 1 -> 1 | 1 -> 1 |
| q11 | keyword | 1 -> 1 | 1 -> 1 |
| q12 | multi, paraphrase | 1 -> 1 | 1 -> 1 |
| q13 | paraphrase | 1 -> 1 | 1 -> 1 |
| q14 | paraphrase | 1 -> 1 | 1 -> 1 |
| q15 | keyword | 2 -> 1 | 1 -> 1 |
| q16 |  | 1 -> 1 | 1 -> 1 |
| q17 |  | 4 -> 1 | 4 -> 1 |
| q18 | pdf | 1 -> 1 | 1 -> 1 |
| q19 | pdf | 1 -> 1 | 1 -> 1 |
| q20 | pdf | 1 -> 1 | 1 -> 1 |
| q21 | multi | 1 -> 1 | 1 -> 1 |
| q22 | multi | 1 -> 1 | 1 -> 1 |
| q23 |  | 1 -> 2 (worse) | 1 -> 2 (worse) |
| q24 |  | 1 -> 1 | 1 -> 1 |
| q25 | multi | 3 -> 1 | 1 -> 1 |

## Where reranking made vector worse (1)

**q23**: How long do we keep daily backups of the file server?  
relevant: rb-backup-restore-file-server · coverage@5 100% -> 100%  
before: rb-backup-restore-file-server, inc-2026-09-backup-failure, rb-backup-restore-file-server  
after: inc-2026-09-backup-failure, rb-backup-restore-file-server, inc-2026-09-backup-failure


## Where reranking made hybrid worse (2)

**q06**: Can I restart the ERP application servers during month-end close?  
relevant: pol-change-management, rb-erp-app-restart · coverage@5 100% -> 50%  
before: rb-erp-app-restart, rb-erp-month-end-support, inc-2026-06-erp-release-rollback  
after: rb-erp-app-restart, inc-2026-06-erp-release-rollback, rb-erp-month-end-support

**q23**: How long do we keep daily backups of the file server?  
relevant: rb-backup-restore-file-server · coverage@5 100% -> 100%  
before: rb-backup-restore-file-server, inc-2026-09-backup-failure, inc-2026-09-backup-failure  
after: inc-2026-09-backup-failure, rb-backup-restore-file-server, inc-2026-09-backup-failure

## Conclusion

_Is the quality gain worth the added latency? For each 'worse' question, say why the cross-encoder preferred the wrong chunk (it was trained on web search, not runbooks)._
