# M03 · RAG: Retrieval-Augmented Generation

**Priority:** Must have · **Roadmap week:** 2

Almost every customer deployment connects the agent to private knowledge (runbooks, tickets, wikis, databases). Retrieval quality decides answer quality.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
Reference solutions are built and tested. Labs 01, 03 and 04 were run live with local models (results in each lab's `results.md`); Lab 02 is scripted and tested offline. Read [LEARNINGS.md](LEARNINGS.md) after the labs; run every offline check with `labs/check.sh`.

- [ ] [Lab 01: RAG pipeline on pgvector + chunk-size experiment](labs/lab-01-pgvector-rag-chunking/README.md)
- [ ] [Lab 02: Same corpus on Amazon Bedrock Knowledge Bases](labs/lab-02-bedrock-knowledge-bases/README.md)
- [ ] [Lab 03: Document-level access control](labs/lab-03-rag-access-control/README.md)
- [ ] [Lab 04: Add a reranker and measure it](labs/lab-04-reranker/README.md)

## Self-check (answer aloud, no notes)
- [ ] Retrieval returns the right document but the answer is wrong. Where do you look?
- [ ] How do you keep a vector index fresh when source documents change daily?

## Folder layout
```
M03-rag/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
├── LEARNINGS.md       ← cross-lab lessons
└── labs/
    ├── SETUP.md       ← environment setup
    ├── check.sh       ← every offline quality gate (starts pgvector)
    ├── corpus/        ← 77 shared documents (Markdown + PDFs, with access groups)
    ├── golden.yaml    ← 25 questions with relevant docs and evidence phrases
    ├── common/        ← ragkit: chunker, embedders, pgvector store, BM25 + RRF, metrics
    ├── lab-01-pgvector-rag-chunking/
    ├── lab-02-bedrock-knowledge-bases/
    ├── lab-03-rag-access-control/
    └── lab-04-reranker/
```
