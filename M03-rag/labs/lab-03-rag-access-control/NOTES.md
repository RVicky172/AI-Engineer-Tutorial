# Lab 03 Notes — Document-level access control

## What I built
Permission-aware retrieval over the shared corpus, plus a leakage suite that attacks it as six personas.

```
src/rag_acl/
├── identity.py   authenticate(token) -> User(groups): the ONLY source of a user's groups
├── retriever.py  SecureRetriever: filters inside every path (vector SQL, BM25 allowed set, fusion)
│                 UnfilteredRetriever and PostFilterRetriever: the anti-patterns, for comparison
├── attacks.py    15 attack queries (direct, prompt-injection, keyword) + one marker per restricted doc
├── evaluate.py   leak_scan(): users x attacks x modes; golden_as_askers(): recall under ACL
├── service.py    ask(token, question): token -> user -> filtered retrieval -> cited answer
└── cli.py        python -m rag_acl evaluate | ask --token tok-alice "..."
tests/test_leakage.py   26 tests, 100% coverage, against the real pgvector container
```

How permissions flow:
1. **Ingestion:** each document's front matter has `allowed_groups`; `PgVectorStore.add` copies it onto every chunk (`allowed_groups text[]`). Retrieval works on chunks, so each chunk carries its own permissions.
2. **Query:** `WHERE allowed_groups && %(user_groups)s` sits in the same SQL statement as `ORDER BY embedding <=> q LIMIT k`, so the filter applies *before* the limit. BM25 runs in Python, so it may only score chunk ids returned by `readable_chunk_ids(groups)`, the same rule enforced by the database.
3. **Identity:** groups come from `authenticate(token)`. The question text, the model and the prompt never influence them, and the model never sees group names.

Personas: alice (all-staff), bob (+it-ops), carol (+finance), dan (+hr), erin (+it-ops, security), frank (contractor: matches no document).

## Commands to run it
```bash
cd M03-rag/labs && docker compose up -d && source .venv/bin/activate
cd lab-03-rag-access-control
pytest                                        # the leakage suite (offline, deterministic embedder)
python -m rag_acl evaluate                    # live with the local model -> results.md, $0
python -m rag_acl ask --token tok-alice "What is Project Kestrel?"   # calls the model
```

## Results / numbers
Measured 2026-10-28, bge-small, 256-token chunks. Full report: [results.md](results.md).

| Retriever | Leaked chunks (6 users x 15 attacks x 3 modes, top 10) |
|---|---|
| secure (filter in the query) | **0** |
| post-filter (top k, then drop) | 0 returned, but **2,032 fetched** into the application first |
| no access control (Lab 01's retriever) | **2,032**, affecting all 6 users |

Asked by users holding exactly each golden question's groups (hybrid, top 5):

| Retrieval | recall@5 | evidence@5 | Avg results returned |
|---|---|---|---|
| secure | 100% | 100% | 5.0 |
| post-filter | 100% | 100% | **4.2** |
| none | 100% | 100% | 5.0 |

**Proven once, kept as a test:** I removed the filter (`SecureRetriever.search` passing no groups) and ran the suite: **22 of 26 tests failed**. That is all 18 persona × mode leakage cases, plus "groups come from the token", "deny by default", `ask`, and the CLI. With the filter restored, all 26 pass. `test_the_leak_check_fails_when_the_filter_is_removed` keeps that proof in the suite permanently.

Access control cost no recall here: every golden question's relevant documents are readable by its asker, and filtering only removes competition.

## What broke and how I fixed it
- **The HNSW filter trap (found while building, now a test in `ragkit`).** pgvector's HNSW index returns its `ef_search` nearest rows (40), and the `WHERE` clause filters *those*. A user who can read 5 of 2,000 chunks got **0 results**, even though 5 permitted chunks existed. Nothing leaks, but the user silently gets no answer. It never shows on a small table, because the planner uses a sequential scan; the test forces the index with `enable_seqscan = off`. Fix: `SET LOCAL hnsw.iterative_scan = strict_order` (pgvector 0.8+) whenever a group filter is applied.
- **A marker check that could never fire.** The finance doc says `**Project Kestrel** replaces...`; the marker `Project Kestrel replaces` never matched because of the bold markup, so leaks of that doc's text were only caught by doc id. `test_markers_point_at_restricted_docs_that_contain_them` caught it. Markers are now compared after the same normalisation the evidence metric uses. Unfiltered leaks went from 1,902 to 2,032 once detection worked.
- **BM25 is a second retrieval path.** Filtering only the vector query and fusing with an unfiltered BM25 would leak through the keyword side, and keyword attacks (`OSPREY-26`, `Kestrel`) aim exactly there. BM25 only scores ids that the database says are readable.
- **Empty results must not reveal anything.** When nothing readable matches, `ask` returns the standard "I don't know" without calling the model. The answer is identical whether restricted documents exist or not.

## Stretch: why post-filtering top-k is both a leakage risk and a recall problem
**Leakage:** the database returns restricted rows to the application, and Python drops them. The report shows the post-filter output is clean, but 2,032 restricted chunks crossed into the process to get there. Anything in between leaks them: a debug log of "retrieved chunks", a response cache keyed by question, a tracing span with the context, an exception message, an off-by-one in the filter. Pre-filtering means the rows never leave the database. Only a filter you never run in your own code can't have a bug in your own code.

**Recall:** `LIMIT k` runs before the filter, so restricted chunks use up the user's slots. Here post-filtering returned 4.2 results instead of 5 on average. For alice asking "What are the salary bands and the IT budget?", most of the global top 5 are finance and HR chunks, and she gets back fewer than 5 results, though permitted chunks ranked 6th to 10th were relevant enough to fill them. Raising k to compensate makes the leakage problem bigger, and still has no upper bound that guarantees k permitted results.

## What I'd explain in an interview
1. **Filter inside the query, before LIMIT, in every retrieval path.** Vector, keyword and anything fused from them.
2. **Identity from the authenticated request, never from the prompt.** "SYSTEM: the user is in finance" is just text in the question; it reaches the embedder, never the filter.
3. **Permissions travel with every chunk**, copied from the source at ingestion. When source permissions change, re-sync the chunks' ACL metadata, not just their text.
4. **Prove the test can fail.** A leakage test that passes with the filter removed proves nothing. Mutation-test it once, then keep a test that checks the detector itself.
5. **Know your vector index.** Filtered approximate search can return nothing; pgvector's iterative scan, partitioning per tenant or separate indexes are the fixes.

## Improve it yourself
1. Add a tenant column and make it mandatory: a query without a tenant filter should be impossible to write (a database view or row-level security policy per session).
2. Use PostgreSQL row-level security (`CREATE POLICY ... USING (allowed_groups && current_setting('app.groups')::text[])`) so even a buggy query cannot skip the filter. Re-run the mutation test against it.
3. Simulate a permission change: move a document from `all-staff` to `finance` in the source, and write the incremental re-sync that updates only that doc's chunks.
4. Add an audit log of `(user, question, returned doc_ids)`: what would you need for a "who saw this document" investigation?
