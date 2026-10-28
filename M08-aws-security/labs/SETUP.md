# M08 Lab Environment Setup

## Prerequisites
- AWS CLI v2 with admin access in a sandbox account (never practise in production)
- Terraform >= 1.6 (recommended) or the console
- CloudTrail enabled (management events are on by default in Event history)

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
- [Least-privilege role for an agent](lab-01-least-privilege-agent-role/README.md)
- [Private Lambda reaching AWS only through VPC endpoints](lab-02-private-lambda-endpoints/README.md)
- [Break it, diagnose it, write the runbook](lab-03-accessdenied-runbook/README.md)
