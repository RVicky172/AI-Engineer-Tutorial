# M07 Lab Environment Setup

## Prerequisites
- Node.js (for `npx @modelcontextprotocol/inspector`)
- A free ServiceNow Personal Developer Instance (developer.servicenow.com)
- The mock ticketing API from M06 lab-02 (or a new FastAPI mock)

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
- [MCP server over a mock ticketing API](lab-01-mcp-server-ticketing/README.md)
- [OAuth 2.0 client credentials with caching and refresh](lab-02-oauth-client-credentials/README.md)
- [ServiceNow incident tools](lab-03-servicenow-incidents/README.md)
- [Map messy API errors into actionable tool errors](lab-04-error-mapping-wrapper/README.md)
