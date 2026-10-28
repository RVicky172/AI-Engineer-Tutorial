# M05 Lab Environment Setup

## Prerequisites
- AWS account + AWS CLI v2 configured (`aws sts get-caller-identity` works)
- Model access enabled for at least one Claude model and one small/cheap model
- AWS Budget alarm configured
- Terraform or AWS CDK for lab 04 (console is acceptable for a first pass)

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
- [Converse client with tool use, streaming and throttling retries](lab-01-converse-client/README.md)
- [Bedrock Guardrails: PII masking and denied topics](lab-02-guardrails/README.md)
- [Model invocation logging and a token/latency query](lab-03-invocation-logging-dashboard/README.md)
- [Call Bedrock from a private subnet via VPC endpoint](lab-04-private-vpc-endpoint/README.md)
