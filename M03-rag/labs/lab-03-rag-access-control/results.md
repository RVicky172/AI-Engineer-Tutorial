# Lab 03 results: document-level access control

Embedder `BAAI/bge-small-en-v1.5` · 256-token chunks · 77 docs · run 2026-10-28 16:31 UTC

## Leakage scan: 6 users x 15 attack queries x 3 modes, top 10

A leak is a returned chunk from a document the user may not read, or returned text containing a marker phrase of such a document.

| Retriever | Leaked chunks | vector | bm25 | hybrid | Users affected |
|---|---|---|---|---|---|
| secure (filter in the query) | **0** | 0 | 0 | 0 | 0 |
| post-filter (top k, then drop) | **0** | 0 | 0 | 0 | 0 |
| no access control (Lab 01) | **2032** | 752 | 566 | 714 | 6 |

The post-filter output looks clean, but to produce it the application first fetched the same 2032 restricted chunks and dropped them in Python. Anything between the fetch and the drop (a debug log, a cache, an exception message, a bug) leaks them.

## Golden set asked by users holding exactly the question's groups (hybrid, top 5)

| Retrieval | recall@5 | evidence@5 | MRR | Avg results returned |
|---|---|---|---|---|
| secure (filter in the query) | 100% | 100% | 0.96 | 5.0 |
| post-filter (top k, then drop) | 100% | 100% | 0.96 | 4.2 |
| no access control (Lab 01) | 100% | 100% | 0.95 | 5.0 |

## Example leaks: no access control (Lab 01)

| User | Query | Mode | Leaked doc | Why |
|---|---|---|---|---|
| alice | What is the IT budget for FY2027? | vector | fin-it-budget-fy27 | unreadable doc |
| alice | What is the IT budget for FY2027? | vector | fin-vendor-contract-renewals | unreadable doc |
| alice | What is the IT budget for FY2027? | vector | hr-it-salary-bands | unreadable doc |
| alice | What is the IT budget for FY2027? | vector | sec-pentest-findings-2026 | unreadable doc |
| alice | What is the IT budget for FY2027? | bm25 | rb-wifi-controller-reboot | unreadable doc |
| alice | What is the IT budget for FY2027? | bm25 | rb-major-incident-process | unreadable doc |
| alice | What is the IT budget for FY2027? | bm25 | sec-incident-response-playbook | unreadable doc |
| alice | What is the IT budget for FY2027? | bm25 | pol-change-management | unreadable doc |
| alice | What is the IT budget for FY2027? | bm25 | rb-erp-batch-job-rerun | unreadable doc |
| alice | What is Project Kestrel? | vector | rb-on-call-escalation | unreadable doc |
| alice | What is Project Kestrel? | vector | inc-2026-08-k8s-node-pressure | unreadable doc |
| alice | What is Project Kestrel? | vector | rb-k8s-crashloopbackoff | unreadable doc |
