# M04 Lab Environment Setup

## Prerequisites
- Completed M02 (tool design)
- Bedrock model access (Strands and langchain-aws default to Bedrock)

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
- [Incident triage agent in LangGraph and Strands](lab-01-triage-agent-two-frameworks/README.md)
- [Human approval with LangGraph interrupts](lab-02-human-approval-interrupts/README.md)
- [Supervisor with knowledge and actions agents](lab-03-supervisor-multi-agent/README.md)
