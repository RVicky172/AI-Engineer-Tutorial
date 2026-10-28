# M03 Lab Environment Setup

## Prerequisites
- Docker Desktop
- AWS account with Bedrock access to an embeddings model (e.g. Amazon Titan Text Embeddings V2) — or use a local sentence-transformers model
- Run `docker compose up -d` in `labs/` to start PostgreSQL + pgvector

## Python environment
From this `labs/` folder:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Local services
```bash
docker compose up -d      # start
docker compose ps         # check
docker compose down       # stop (add -v to wipe data)
```

## AWS checklist
- [ ] `aws sts get-caller-identity` returns your **sandbox** account
- [ ] Default region set (`aws configure get region`) and the services you need are available there
- [ ] AWS Budget alarm exists
- [ ] Copy `.env.example` to `.env` and fill it in (`.env` is git-ignored)
- [ ] Delete billable resources at the end of each session (endpoints, vector stores, NAT gateways, load balancers)

## Labs in this module
- [RAG pipeline on pgvector + chunk-size experiment](lab-01-pgvector-rag-chunking/README.md)
- [Same corpus on Amazon Bedrock Knowledge Bases](lab-02-bedrock-knowledge-bases/README.md)
- [Document-level access control](lab-03-rag-access-control/README.md)
- [Add a reranker and measure it](lab-04-reranker/README.md)
