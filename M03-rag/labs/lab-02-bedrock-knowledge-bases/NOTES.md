# Lab 02 Notes — Same corpus on Amazon Bedrock Knowledge Bases

## What I built
Scripts that put the shared corpus into a Bedrock Knowledge Base, query it with the same golden set as the pgvector labs, and delete every resource again, with a check that nothing is left.

```
src/kb_lab/
├── prepare.py   corpus -> upload files (front matter stripped) + <file>.metadata.json sidecars
├── infra.py     KnowledgeBaseLab: bucket, S3 Vectors index, least-privilege IAM role, KB, data
│                source, ingestion job; down(); remaining(). Every resource goes into a state file
│                the moment it exists, so `down` works even after a half-finished `up`.
├── query.py     Retrieve (with an allowed_groups metadata filter), golden-set scoring with the
│                same ragkit metrics, RetrieveAndGenerate
└── cli.py       python -m kb_lab prepare | up --yes | eval | ask | down | status
tests/           12 tests, 98% coverage, $0: moto plays S3/IAM/STS/S3 Vectors; botocore's Stubber
                 plays Bedrock and validates every request against the real API model
```

Design choices:
- **Vector store: Amazon S3 Vectors.** It bills for storage and queries rather than per hour. OpenSearch Serverless, the option most tutorials use, bills per OCU-hour while the collection exists, whether you query it or not: that's the "some vector stores bill per hour" warning in the lab. Aurora PostgreSQL (pgvector) bills for its minimum capacity while running. Check the current pricing pages before you choose; I have deliberately not copied prices into this file because they change.
- **Same chunking as pgvector:** fixed-size chunks of 256 tokens with 12% overlap, so the comparison is about the platform, not the chunker.
- **Same access control as Lab 03:** `allowed_groups` goes into each sidecar, and `Retrieve` sends `listContains` / `orAll` metadata filters (`query.group_filter`). That's step 5 of Lab 03.
- **`up` refuses to run without `--yes`** and prints exactly what it will create first.

## Commands to run it
```bash
cd M03-rag/labs && source .venv/bin/activate && cd lab-02-bedrock-knowledge-bases
pytest                                   # offline, $0
python -m kb_lab prepare                 # local: build/kb-upload/, inspect the sidecars
python -m kb_lab up                      # prints what it would create; nothing happens
python -m kb_lab up --yes                # BILLABLE: create + ingest (~5-10 min)
python -m kb_lab eval                    # golden set: plain and with each asker's groups
python -m kb_lab ask "What does VPN-ERR-812 mean?" --model-arn <claude model or profile ARN>
python -m kb_lab down                    # delete everything, then list what remains: must say "none"
```
Use a region where both Bedrock Knowledge Bases with S3 Vectors and Titan Text Embeddings V2 are available. `AWS_REGION` and `AWS_PROFILE` come from the environment or `labs/.env`.

## Results / numbers
**Not run against AWS yet.** This session was scoped to "build scripts only, create nothing". The pgvector column below is measured; fill in the Knowledge Base column from `eval`, and paste the `down` output as evidence of deletion.

| | pgvector (Labs 01, 03, 04) | Bedrock Knowledge Base |
|---|---|---|
| Setup effort | docker compose + ~900 lines of shared Python (`ragkit`: chunker, store, BM25, metrics, generation) | `up --yes`: ~600 lines of scripts, much of it IAM, state and teardown |
| Time to first query | ~2 s ingestion after the model download | __ min (ingestion job) |
| recall@5 / evidence@5 (25 golden questions) | 100% / 96% vector, 100% / 100% hybrid (256 tokens) | __ / __ |
| MRR | 0.86 vector, 0.95 hybrid, 0.96 hybrid + rerank | __ |
| p50 retrieval latency | ~8 ms local (vector or hybrid) | __ ms (network round trip included) |
| Access control | SQL filter before LIMIT; 0 leaks in Lab 03's scan | metadata filter (`listContains`); rerun Lab 03's attacks against it |
| Hybrid search / reranking | built in Labs 01 and 04 | KB hybrid search depends on the vector store; reranking via the Rerank API |
| Monthly cost estimate | your Postgres (RDS/Aurora) instance + embedding compute | S3 + S3 Vectors storage/queries + embedding tokens at ingestion + per-query embeddings |
| Control / flexibility | everything: chunker, tokenizer, filters, SQL joins with ticket data | managed ingestion, sync and citations; chunking strategies and filters within the API's options |

**Deletion evidence:** paste the output of `python -m kb_lab down` here. It must end with `Remaining resources with prefix m03-kb-lab: none`.

## What broke and how I fixed it
These were caught offline, which is the point of testing infrastructure code against the API models before running it:
- **Invalid IDs in my own test data.** The Stubber rejected `KB1` because Knowledge Base IDs are at least 10 characters, and `sessionId: "s"` because session IDs are at least 2. Fakes that accept any value hide this kind of mismatch until the first real call.
- **Over-strict "least privilege" assertion.** My first test said "no `*` anywhere in the policy", which also rejected the correctly scoped `arn:aws:s3:::bucket/corpus/*`. The real rule is: no bare `*` resource and no wildcard actions.
- **One stub script shared across CLI runs.** Each CLI run builds new clients, so `ask` got a client whose next scripted response was a `retrieve`, and the Stubber raised "Operation mismatch". Each run now gets its own script.

Pitfalls handled up front:
- **IAM propagation:** a role created seconds ago can't be assumed by Bedrock yet. `create_knowledge_base` retries only that specific `ValidationException`, with an injected sleep so the test is instant.
- **Re-runnable teardown:** `down` treats "not found" as success, and `remaining()` lists anything with the lab prefix that survived, including resources missing from the state file.
- **Ingestion can "succeed" with failures:** the job's statistics and `failureReasons` are printed and saved, and `up` exits non-zero unless the job is `COMPLETE`.
- **Front matter:** uploading the Markdown files as-is would make the KB chunk and embed the YAML header. `prepare` strips it and moves the fields into the sidecar.

## What I'd explain in an interview
1. **Managed vs. build-your-own is a control trade-off.** A KB gives managed ingestion, sync and cited answers in an afternoon. pgvector gives you the chunker, the hybrid search, the reranker and ACL joins with your own tables. Choose by what the customer must control.
2. **Price the vector store before you create it.** Per-hour stores cost money while idle; for a lab or a low-traffic tenant, pay-per-use storage wins.
3. **Infrastructure code needs teardown and proof of teardown.** State file, idempotent delete, and a final listing by prefix.
4. **Test AWS code against the API model, not against your assumptions.** moto for the services it emulates; botocore's Stubber validates every parameter of the rest.
5. **Same golden set, same metrics, across platforms**, or the comparison is opinion.

## Improve it yourself
1. Run it: `up --yes`, `eval`, `down`. Fill in the table and note what surprised you.
2. Stretch: re-create the data source with `HIERARCHICAL` or `SEMANTIC` chunking and re-run `eval`.
3. Run Lab 03's attack queries through `retrieve(..., groups=...)` and confirm the metadata filter leaks nothing.
4. Add a `status: superseded` filter (`notEquals`) and check q17 from Lab 01.
5. Trigger a re-sync from an S3 event (EventBridge → Lambda → `start_ingestion_job`) so the index stays fresh: the guide's self-check question.
