# M06 Lab Environment Setup

## Prerequisites
- Completed M04 (an agent to deploy) and M05
- AWS CLI v2 with permissions to create IAM roles, ECR repos and AgentCore resources
- Docker (optional: the starter toolkit can build in the cloud with CodeBuild)
- Check the AgentCore Developer Guide for current region availability and CLI commands before each lab

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
- [Deploy an agent to AgentCore Runtime](lab-01-deploy-runtime/README.md)
- [Put your REST API behind AgentCore Gateway](lab-02-gateway-openapi-target/README.md)
- [Outbound OAuth with AgentCore Identity](lab-03-identity-outbound-oauth/README.md)
- [AgentCore Memory across sessions](lab-04-memory/README.md)
- [Find a failing tool call in AgentCore Observability](lab-05-observability-debug/README.md)
