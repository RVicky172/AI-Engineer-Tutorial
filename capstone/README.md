# Capstone: IT Incident Triage Agent on AWS

One project that touches almost every requirement in the job description. Build it in stages across the 8 weeks.

## Use case
An agent receives a new incident (from ServiceNow or a mock API), searches runbooks and past tickets, proposes a diagnosis, and, **with approval**, performs a safe action (for example restarting a service or adding a work note).

## Target architecture
| Layer | What to build |
|---|---|
| Model | Amazon Bedrock via Converse API with tool use, Guardrails for PII masking, cost tracking per request |
| Knowledge | RAG over runbooks and resolved tickets with metadata filters (team, severity) and a golden question set |
| Integrations | MCP server or AgentCore Gateway for ticketing, monitoring (CloudWatch alarms) and CMDB lookup; OAuth for the ticketing API; secrets in Secrets Manager |
| Hosting | AgentCore Runtime (or ECS Fargate / Lambda), deployed with Terraform and CI/CD with rollback |
| Security | Least-privilege roles, VPC endpoints, human approval for state changes, audit log, prompt-injection tests |
| Operations | OpenTelemetry traces, CloudWatch dashboard and alarms, evaluation suite in CI, runbook and troubleshooting guide |
| Customer pack | Architecture diagram, integration spec, deployment steps, 10-minute demo video, lessons-learned note |

## Stages (one per week)
1. [Foundation](stages/stage-01-foundation/README.md) — M01, M02
2. [Knowledge](stages/stage-02-knowledge/README.md) — M03, M13
3. [Agent](stages/stage-03-agent/README.md) — M04
4. [Model layer](stages/stage-04-model-layer/README.md) — M05
5. [Platform & integrations](stages/stage-05-platform-integrations/README.md) — M06, M07
6. [Secure deploy](stages/stage-06-secure-deploy/README.md) — M08, M09
7. [Operate & evaluate](stages/stage-07-operate-evaluate/README.md) — M10, M11, M12
8. [Customer pack](stages/stage-08-customer-pack/README.md) — M14, M15

## Definition of done
- [ ] A stranger can deploy it from the README in under an hour.
- [ ] You can show a trace of one failed run and explain the root cause.
- [ ] You can state the cost per resolved incident and what drives it.

## Suggested code layout
```
capstone/
├── src/triage_agent/      agent, tools, prompts, config
├── mcp_servers/           ticketing, cmdb, monitoring
├── rag/                   ingestion + retrieval
├── evals/                 scenarios, golden set, judge
├── infra/                 terraform
├── .github/workflows/     ci, deploy, rollback (move to repo root if this becomes its own repo)
└── docs/                  architecture, integration spec, runbook, lessons learned
```
