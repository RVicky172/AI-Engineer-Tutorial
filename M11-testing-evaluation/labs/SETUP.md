# M11 Lab Environment Setup

## Prerequisites
- Your triage agent from M04
- GitHub Actions from M09

## Python environment
From this `labs/` folder:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## AWS checklist
- [ ] `aws sts get-caller-identity` returns your **sandbox** account
- [ ] Default region set (`aws configure get region`) and the services you need are available there
- [ ] AWS Budget alarm exists
- [ ] Copy `.env.example` to `.env` and fill it in (`.env` is git-ignored)
- [ ] Delete billable resources at the end of each session (endpoints, vector stores, NAT gateways, load balancers)

## Labs in this module
- [40-case scenario evaluation gated in CI](lab-01-scenario-eval-ci/README.md)
- [LLM-as-judge vs your own scoring](lab-02-llm-judge-calibration/README.md)
- [Load test with 50 concurrent users](lab-03-load-test/README.md)
