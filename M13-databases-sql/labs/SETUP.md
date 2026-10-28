# M13 Lab Environment Setup

## Prerequisites
- Docker Desktop; run `docker compose up -d` in `labs/` (PostgreSQL seeded with an ITSM-style schema from `labs/seed.sql`)

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
- [Safe text-to-SQL tool](lab-01-text-to-sql-safe/README.md)
- [Result cache for the SQL tool](lab-02-result-cache/README.md)
