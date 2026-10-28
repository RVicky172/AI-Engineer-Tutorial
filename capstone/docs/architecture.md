# Capstone Architecture

> Update this at the end of every stage. Keep a diagram (Mermaid below, or draw.io/Excalidraw export) and a short decision log.

```mermaid
flowchart LR
    SN[ServiceNow / mock ticket API] -->|new incident| RT[Agent on AgentCore Runtime]
    RT -->|Converse + tools| BR[Amazon Bedrock + Guardrails]
    RT -->|MCP| GW[AgentCore Gateway / MCP servers]
    GW --> SN
    GW --> CW[CloudWatch alarms]
    GW --> CMDB[CMDB lookup]
    RT -->|retrieve| KB[RAG: runbooks + resolved tickets]
    RT -->|approval request| HUM[Human approver]
    RT -->|traces, metrics| OBS[CloudWatch / X-Ray / OTel]
```

## Decision log
| Date | Decision | Options considered | Why |
|---|---|---|---|
| | | | |
