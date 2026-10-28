# M10 Lab Environment Setup

## Prerequisites
- Docker Desktop; run `docker compose up -d` in `labs/` for a local Jaeger trace viewer
- Your agent service from M04/M09
- AWS account for CloudWatch labs

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
- [End-to-end OpenTelemetry traces for an agent](lab-01-otel-tracing/README.md)
- [Agent dashboard and alarms](lab-02-cloudwatch-dashboard-alarms/README.md)
- [Game day: five faults, timed diagnosis](lab-03-game-day/README.md)
