# M03 Learnings — what the labs taught, and what to do better

All four labs are built and pass every offline gate (`labs/check.sh`: 92 tests across five projects, 98-100% coverage, ruff, mypy `--strict`). Labs 01, 03 and 04 were **run live** on this machine with local models (bge-small embeddings, a MiniLM cross-encoder) and pgvector in Docker, at no cost. Still to do: Lab 02 against AWS, and anything that calls Claude (cited answers in Lab 01, the judge in Lab 04). Each lab's `NOTES.md` lists the commands.

| Lab | Result | Most important lesson |
|---|---|---|
| [01 pgvector + chunk size](labs/lab-01-pgvector-rag-chunking/NOTES.md) | 256-token hybrid: evidence@5 100%, MRR 0.95 | recall@5 was 100% everywhere: a metric that can't fail tells you nothing |
| [02 Knowledge Bases](labs/lab-02-bedrock-knowledge-bases/NOTES.md) | scripted up/eval/down, tested offline | Price the store's billing model; teardown needs state and proof |
| [03 Access control](labs/lab-03-rag-access-control/NOTES.md) | 0 leaks vs 2,032 without the filter | Filter before LIMIT in every path, and prove the test can fail |
| [04 Reranker](labs/lab-04-reranker/NOTES.md) | vector MRR 0.86 → 0.96, +126 ms | Rerankers fix stale-doc ranking, and break term-dense near misses |
| [common/ (ragkit)](labs/common/) | 36 tests, 99% | One chunker, store and metric set, so every lab is comparable |

---

## 1. Habits that showed their value (keep doing them)

1. **Measure retrieval for free before spending on generation.** Every retrieval number in this module came from local models and a local database: about a minute per experiment, $0. Only answer quality needs Claude.
2. **Make the evaluation able to fail.** The first golden set scored 100% for every config. Adding distractors (superseded policies, neighbouring topics) and an exact evidence phrase per question is what made chunk size, hybrid search and reranking measurable.
3. **Validate the test data, not just the code.** `check_evidence` fails if an answer phrase is missing from its document, and a marker test caught a leak detector that could never fire (`**Project Kestrel**` in bold).
4. **Mutation-test security tests.** With the ACL filter removed, 22 of 26 leakage tests failed. A permanent test runs the detector against an unfiltered retriever.
5. **Validate cloud requests against the API model offline.** botocore's `Stubber` rejected invalid IDs and caught a script-ordering mistake. moto covered S3, IAM and S3 Vectors. Nothing was learned on a billed call.
6. **Read the individual questions, not just the averages.** With 25 questions, one question is 4 points. The interesting findings (q17's stale policy, q23 and q06 under reranking) only show in the per-question tables.

## 2. Mistakes made while building (learn from these)

| Mistake | Why it's tempting | Better approach |
|---|---|---|
| Chunk sizes 256/512/1024 copied from the lab text | "standard" sizes | Size relative to your documents (140-620 tokens here) and the embedder's input limit |
| A clean corpus and questions written from the documents | quick to write | Add stale versions and near-duplicates; write questions in users' words |
| Overlap sized to the full budget | overlap is "extra" | Pieces of a split block must leave room for it, or it silently disappears |
| Word-level overlap and table splits without headers | simplest code | Keep whole lines; repeat a table's header in every piece |
| Unquoted colon in YAML front matter | looks fine | Parse errors must name the file; one bad doc in 10,000 must be findable |
| Marker phrase matched against raw Markdown | the text "contains" it | Normalise markup before matching, and test the detector itself |
| PDFs committed as text | git sees ASCII | `.gitattributes`: `*.pdf binary` (CRLF conversion breaks the byte offsets) |
| Approximate numbers in notes ("~350 lines") | sounds about right | Measure, then write (`wc -l` said ~600) |

## 3. Things that surprised me
- **Filtered HNSW can return nothing** for a user with few permitted chunks, and only once the table is big enough for the planner to use the index. `hnsw.iterative_scan` fixes it (Lab 03).
- **A superseded document outranked the current one** with vector search (Lab 01, q17). The reranker fixed it (Lab 04); a `status` metadata filter would too.
- **Unfiltered retrieval hands ordinary employees finance, HR and pentest content** for innocent questions, not just for attacks (Lab 01's q17 and q25 pulled security-only chunks).
- **Reranking on top of hybrid barely helped** (MRR 0.95 → 0.96) and cost coverage on a two-document question. Hybrid had done most of the work.

## 4. How these labs connect to the rest of the course
- `ragkit` + the corpus → the knowledge tools of the triage agent in **M04**, and an MCP knowledge server in **M07**.
- Lab 02's Knowledge Base → Bedrock in depth in **M05**; its IAM role is a least-privilege example for **M08**.
- Lab 03's `authenticate()` → real OAuth / JWT identity in **M06** (AgentCore Identity) and **M08**.
- The golden set, evidence metric and LLM judge → **M11** evaluation; retrieval latency → **M10** traces.
- Lab 03's attack queries → prompt-injection and data-leakage testing in **M12**.

## 5. Improvements to how you study this module
1. **Attempt each lab first** (60-90 minutes from the README, without opening `src/`), then diff against the reference and write 3 differences in `docs/notes.md`.
2. **Write 10 golden questions yourself before reading `golden.yaml`**, in the words a user would type. Run them: how many does your pipeline get, and why?
3. **Break things on purpose:** remove the iterative scan, the BM25 `allowed` set, or the table-header repetition, and predict which test fails before running it.
4. **Spend money last.** Run Labs 01, 03, 04 locally first. Then Lab 02 (`up --yes` … `down`) in one sitting, and the Claude-based answer/judge runs with `--limit 5` first.
5. **Answer the self-check questions aloud** (in `README.md`). Both are answered by these labs:
   - *Right document, wrong answer?* → is the answer-bearing **chunk** in the context (evidence@5, Lab 01)? A stale version beside it (q17)? Citations pointing at chunks the model never saw (`check_citations`)? Then the prompt and the model.
   - *Keep the index fresh?* → incremental re-ingestion per changed document (delete its chunks by `doc_id`, re-chunk, re-embed, copy ACLs), periodic reconciliation by hash/`updated`, and for a KB, an ingestion job triggered by S3 events (Lab 02, "Improve it" #5).

## 6. Changes made to the lab setup
- `labs/corpus/` (77 documents, 3 PDFs with sidecars) and `labs/golden.yaml` (25 questions with evidence phrases), shared by all labs; `tools/make_pdfs.py` regenerates the PDFs.
- `labs/common/` (`ragkit`): the reusable RAG pieces, reusing M02's `llm_common` for generation.
- `labs/requirements.txt` installs everything editable; `check.sh` starts pgvector and runs every gate.
- `labs/.env.example` and `SETUP.md`: `PG_DSN`, the M02 model variables, `HF_HUB_OFFLINE`.
- `docs/guide.md`: filtered-HNSW trap, billing models of vector stores, ACL on every retrieval path, saturated metrics and evidence@k, rerankers' training distribution.
- Repo root `.gitattributes`: PDFs binary, shell scripts LF.
