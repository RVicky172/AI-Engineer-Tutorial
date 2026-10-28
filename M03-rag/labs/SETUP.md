# M03 Lab Environment Setup

## Prerequisites
- Completed M01 and M02 setup (M03 reuses M02's `llm_common` for answer generation)
- Docker Desktop, for PostgreSQL + pgvector
- About 2 GB of disk for PyTorch and the local embedding model. No GPU needed: the corpus embeds in seconds on a CPU.
- Optional: Claude access (as in M02) to generate answers; AWS Bedrock access for Titan embeddings and Lab 02

## Python environment (one shared venv for all M03 labs)
From this `labs/` folder:

```bash
# Option A: plain Python
python3.12 -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt

# Option B: uv
uv venv --python 3.12 && source .venv/bin/activate && uv pip install -r requirements.txt
```

The first run downloads the embedding model `BAAI/bge-small-en-v1.5` (~130 MB) from Hugging Face. Afterwards, set `HF_HUB_OFFLINE=1` to skip the online version check.

## Local services
```bash
docker compose up -d      # start PostgreSQL 16 + pgvector on localhost:5432 (user/password/db: rag)
docker compose ps         # check
docker compose down       # stop (add -v to wipe data)
```

## Configure
```bash
cp .env.example .env     # .env is git-ignored
```
| Variable | Used for |
|---|---|
| `PG_DSN` | the database (default matches docker-compose.yml) |
| `LLM_PROVIDER`, `LLM_MODEL`, `ANTHROPIC_API_KEY` | answer generation and judging, exactly as in M02 |
| `AWS_PROFILE`, `AWS_REGION` | `--embedder titan` and Lab 02 |

## Shared data
- `corpus/`: 77 documents (Markdown with front matter, 3 PDFs with `.meta.yaml` sidecars). Each has `allowed_groups` for Lab 03. Regenerate the PDFs with `python tools/make_pdfs.py`.
- `golden.yaml`: 25 questions with relevant doc ids, an exact evidence phrase and a reference answer.
- `common/` (`ragkit`): the corpus loader, chunker, embedders, pgvector store, BM25 + RRF, metrics and cited generation that every lab uses.

## Checks
```bash
./check.sh     # offline gates for every lab: starts the container, runs tests + coverage, ruff, mypy
```
Retrieval experiments (`python -m rag_pipeline run`) are also free: local model, local database. Only answer generation (Claude), `--embedder titan` and Lab 02 cost money.

## AWS checklist (Titan embeddings and Lab 02 only)
- [ ] `aws sts get-caller-identity` returns your **sandbox** account
- [ ] Region set, and Titan Text Embeddings V2 enabled there
- [ ] AWS Budget alarm exists
- [ ] Delete billable resources at the end of each session (Knowledge Base vector stores bill per hour)

## Labs in this module
- [RAG pipeline on pgvector + chunk-size experiment](lab-01-pgvector-rag-chunking/README.md)
- [Same corpus on Amazon Bedrock Knowledge Bases](lab-02-bedrock-knowledge-bases/README.md)
- [Document-level access control](lab-03-rag-access-control/README.md)
- [Add a reranker and measure it](lab-04-reranker/README.md)
