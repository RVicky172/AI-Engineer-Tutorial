# M02 Lab Environment Setup

## Prerequisites
- Completed M01 setup
- Access to an LLM: Amazon Bedrock (preferred, enable model access in the console) or the Anthropic API
- An AWS Budget alarm (e.g. $20/month) before you start calling models

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
- [One extraction task, three techniques](lab-01-extraction-three-ways/README.md)
- [Tool design for an IT-support agent](lab-02-tool-design-it-support/README.md)
- [Prompt regression suite](lab-03-prompt-regression-suite/README.md)
