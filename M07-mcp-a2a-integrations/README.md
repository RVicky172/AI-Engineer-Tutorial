# M07 · MCP, A2A and Enterprise Integrations

**Priority:** Must have · **Roadmap week:** 5

The FDE spends most time integrating agents with customer systems. When no reusable connector exists, you build one.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: MCP server over a mock ticketing API](labs/lab-01-mcp-server-ticketing/README.md)
- [ ] [Lab 02: OAuth 2.0 client credentials with caching and refresh](labs/lab-02-oauth-client-credentials/README.md)
- [ ] [Lab 03: ServiceNow incident tools](labs/lab-03-servicenow-incidents/README.md)
- [ ] [Lab 04: Map messy API errors into actionable tool errors](labs/lab-04-error-mapping-wrapper/README.md)

## Self-check (answer aloud, no notes)
- [ ] Why wrap a legacy API as an MCP tool instead of letting the agent call it directly?
- [ ] How do you handle an API that rate-limits at 10 requests per second when an agent fans out tool calls?

## Folder layout
```
M07-mcp-a2a-integrations/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-mcp-server-ticketing/
    ├── lab-02-oauth-client-credentials/
    ├── lab-03-servicenow-incidents/
    └── lab-04-error-mapping-wrapper/
```
