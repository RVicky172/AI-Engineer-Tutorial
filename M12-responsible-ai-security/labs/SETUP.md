# M12 Lab Environment Setup

## Prerequisites
- Your agent + RAG from earlier modules
- Bedrock Guardrail from M05 lab-02

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
- [Prompt-injection red team](lab-01-prompt-injection-redteam/README.md)
- [Approval gate and audit log for state-changing tools](lab-02-approval-audit-log/README.md)
- [One-page data handling & security summary](lab-03-data-handling-summary/README.md)
