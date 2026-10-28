# Progress Tracker

Rate yourself 1 (never used) to 5 (could teach it). Spend the most time where you rate 1-2.

## Skill map
| # | Skill area | Priority | Week | Before (1-5) | After (1-5) |
|---|---|---|---|---|---|
| [M01](M01-python-engineering/README.md) | Python and Software Engineering Fundamentals | Must have | 1 |  |  |
| [M02](M02-llm-fundamentals/README.md) | LLM Fundamentals, Prompting, Tool Calling and Structured Outputs | Must have | 1 |  |  |
| [M03](M03-rag/README.md) | RAG: Retrieval-Augmented Generation | Must have | 2 |  |  |
| [M04](M04-agent-frameworks/README.md) | Agent Frameworks and Multi-Agent Systems | Must have | 3 |  |  |
| [M05](M05-amazon-bedrock/README.md) | Amazon Bedrock | Must have | 4 |  |  |
| [M06](M06-bedrock-agentcore/README.md) | Amazon Bedrock AgentCore | Must have (differentiator) | 5 |  |  |
| [M07](M07-mcp-a2a-integrations/README.md) | MCP, A2A and Enterprise Integrations | Must have | 5 |  |  |
| [M08](M08-aws-security/README.md) | AWS Security: IAM, OAuth, Secrets and Network | Must have | 6 |  |  |
| [M09](M09-deployment-cicd-iac/README.md) | Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC | Must have | 6 |  |  |
| [M10](M10-observability/README.md) | Observability and Production Troubleshooting | Must have | 7 |  |  |
| [M11](M11-testing-evaluation/README.md) | Testing and Evaluation of Agentic Systems | Must have | 7 |  |  |
| [M12](M12-responsible-ai-security/README.md) | Responsible AI, Security and Data Protection | Must have | 7 |  |  |
| [M13](M13-databases-sql/README.md) | Databases, SQL and Enterprise Data Sources | Must have | 2 |  |  |
| [M14](M14-itsm-aiops/README.md) | ITSM, CloudOps, SRE and AIOps Use Cases | Preferred | 8 |  |  |
| [M15](M15-customer-facing-skills/README.md) | Customer-Facing Engineering Skills | Must have | 8 |  |  |

## Labs

### M01 · Python and Software Engineering Fundamentals
- [ ] [Lab 01: FastAPI chat service with SSE streaming](M01-python-engineering/labs/lab-01-fastapi-sse-chat/README.md)
- [ ] [Lab 02: Resilient HTTP client wrapper](M01-python-engineering/labs/lab-02-resilient-http-client/README.md)
- [ ] [Lab 03: Test AWS code with moto](M01-python-engineering/labs/lab-03-moto-aws-testing/README.md)

### M02 · LLM Fundamentals, Prompting, Tool Calling and Structured Outputs
- [ ] [Lab 01: One extraction task, three techniques](M02-llm-fundamentals/labs/lab-01-extraction-three-ways/README.md)
- [ ] [Lab 02: Tool design for an IT-support agent](M02-llm-fundamentals/labs/lab-02-tool-design-it-support/README.md)
- [ ] [Lab 03: Prompt regression suite](M02-llm-fundamentals/labs/lab-03-prompt-regression-suite/README.md)

### M03 · RAG: Retrieval-Augmented Generation
- [ ] [Lab 01: RAG pipeline on pgvector + chunk-size experiment](M03-rag/labs/lab-01-pgvector-rag-chunking/README.md)
- [ ] [Lab 02: Same corpus on Amazon Bedrock Knowledge Bases](M03-rag/labs/lab-02-bedrock-knowledge-bases/README.md)
- [ ] [Lab 03: Document-level access control](M03-rag/labs/lab-03-rag-access-control/README.md)
- [ ] [Lab 04: Add a reranker and measure it](M03-rag/labs/lab-04-reranker/README.md)

### M04 · Agent Frameworks and Multi-Agent Systems
- [ ] [Lab 01: Incident triage agent in LangGraph and Strands](M04-agent-frameworks/labs/lab-01-triage-agent-two-frameworks/README.md)
- [ ] [Lab 02: Human approval with LangGraph interrupts](M04-agent-frameworks/labs/lab-02-human-approval-interrupts/README.md)
- [ ] [Lab 03: Supervisor with knowledge and actions agents](M04-agent-frameworks/labs/lab-03-supervisor-multi-agent/README.md)

### M05 · Amazon Bedrock
- [ ] [Lab 01: Converse client with tool use, streaming and throttling retries](M05-amazon-bedrock/labs/lab-01-converse-client/README.md)
- [ ] [Lab 02: Bedrock Guardrails: PII masking and denied topics](M05-amazon-bedrock/labs/lab-02-guardrails/README.md)
- [ ] [Lab 03: Model invocation logging and a token/latency query](M05-amazon-bedrock/labs/lab-03-invocation-logging-dashboard/README.md)
- [ ] [Lab 04: Call Bedrock from a private subnet via VPC endpoint](M05-amazon-bedrock/labs/lab-04-private-vpc-endpoint/README.md)

### M06 · Amazon Bedrock AgentCore
- [ ] [Lab 01: Deploy an agent to AgentCore Runtime](M06-bedrock-agentcore/labs/lab-01-deploy-runtime/README.md)
- [ ] [Lab 02: Put your REST API behind AgentCore Gateway](M06-bedrock-agentcore/labs/lab-02-gateway-openapi-target/README.md)
- [ ] [Lab 03: Outbound OAuth with AgentCore Identity](M06-bedrock-agentcore/labs/lab-03-identity-outbound-oauth/README.md)
- [ ] [Lab 04: AgentCore Memory across sessions](M06-bedrock-agentcore/labs/lab-04-memory/README.md)
- [ ] [Lab 05: Find a failing tool call in AgentCore Observability](M06-bedrock-agentcore/labs/lab-05-observability-debug/README.md)

### M07 · MCP, A2A and Enterprise Integrations
- [ ] [Lab 01: MCP server over a mock ticketing API](M07-mcp-a2a-integrations/labs/lab-01-mcp-server-ticketing/README.md)
- [ ] [Lab 02: OAuth 2.0 client credentials with caching and refresh](M07-mcp-a2a-integrations/labs/lab-02-oauth-client-credentials/README.md)
- [ ] [Lab 03: ServiceNow incident tools](M07-mcp-a2a-integrations/labs/lab-03-servicenow-incidents/README.md)
- [ ] [Lab 04: Map messy API errors into actionable tool errors](M07-mcp-a2a-integrations/labs/lab-04-error-mapping-wrapper/README.md)

### M08 · AWS Security: IAM, OAuth, Secrets and Network
- [ ] [Lab 01: Least-privilege role for an agent](M08-aws-security/labs/lab-01-least-privilege-agent-role/README.md)
- [ ] [Lab 02: Private Lambda reaching AWS only through VPC endpoints](M08-aws-security/labs/lab-02-private-lambda-endpoints/README.md)
- [ ] [Lab 03: Break it, diagnose it, write the runbook](M08-aws-security/labs/lab-03-accessdenied-runbook/README.md)

### M09 · Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC
- [ ] [Lab 01: Containerise and deploy to ECS Fargate with Terraform](M09-deployment-cicd-iac/labs/lab-01-docker-ecs-terraform/README.md)
- [ ] [Lab 02: CI/CD with promotion and one-command rollback](M09-deployment-cicd-iac/labs/lab-02-cicd-pipeline/README.md)
- [ ] [Lab 03: Step Functions with retries and a dead-letter queue](M09-deployment-cicd-iac/labs/lab-03-step-functions-dlq/README.md)
- [ ] [Lab 04: Lambda vs ECS for the same service](M09-deployment-cicd-iac/labs/lab-04-lambda-vs-ecs/README.md)

### M10 · Observability and Production Troubleshooting
- [ ] [Lab 01: End-to-end OpenTelemetry traces for an agent](M10-observability/labs/lab-01-otel-tracing/README.md)
- [ ] [Lab 02: Agent dashboard and alarms](M10-observability/labs/lab-02-cloudwatch-dashboard-alarms/README.md)
- [ ] [Lab 03: Game day: five faults, timed diagnosis](M10-observability/labs/lab-03-game-day/README.md)

### M11 · Testing and Evaluation of Agentic Systems
- [ ] [Lab 01: 40-case scenario evaluation gated in CI](M11-testing-evaluation/labs/lab-01-scenario-eval-ci/README.md)
- [ ] [Lab 02: LLM-as-judge vs your own scoring](M11-testing-evaluation/labs/lab-02-llm-judge-calibration/README.md)
- [ ] [Lab 03: Load test with 50 concurrent users](M11-testing-evaluation/labs/lab-03-load-test/README.md)

### M12 · Responsible AI, Security and Data Protection
- [ ] [Lab 01: Prompt-injection red team](M12-responsible-ai-security/labs/lab-01-prompt-injection-redteam/README.md)
- [ ] [Lab 02: Approval gate and audit log for state-changing tools](M12-responsible-ai-security/labs/lab-02-approval-audit-log/README.md)
- [ ] [Lab 03: One-page data handling & security summary](M12-responsible-ai-security/labs/lab-03-data-handling-summary/README.md)

### M13 · Databases, SQL and Enterprise Data Sources
- [ ] [Lab 01: Safe text-to-SQL tool](M13-databases-sql/labs/lab-01-text-to-sql-safe/README.md)
- [ ] [Lab 02: Result cache for the SQL tool](M13-databases-sql/labs/lab-02-result-cache/README.md)

### M14 · ITSM, CloudOps, SRE and AIOps Use Cases
- [ ] [Lab 01: Seed 20 realistic incidents](M14-itsm-aiops/labs/lab-01-servicenow-seed-incidents/README.md)
- [ ] [Lab 02: Capstone triage agent against ServiceNow](M14-itsm-aiops/labs/lab-02-capstone-triage-servicenow/README.md)

### M15 · Customer-Facing Engineering Skills
- [ ] [Lab 01: Technical discovery checklist + role-play](M15-customer-facing-skills/labs/lab-01-discovery-checklist/README.md)
- [ ] [Lab 02: 10-minute capstone demo](M15-customer-facing-skills/labs/lab-02-demo-video/README.md)
- [ ] [Lab 03: Go-live readiness checklist and runbook](M15-customer-facing-skills/labs/lab-03-go-live-runbook/README.md)

## Capstone
- [ ] [stage-01-foundation](capstone/stages/stage-01-foundation/README.md) — FastAPI service skeleton, structured logging, prompt regression suite
- [ ] [stage-02-knowledge](capstone/stages/stage-02-knowledge/README.md) — RAG over runbooks and resolved tickets with metadata filters and a golden set
- [ ] [stage-03-agent](capstone/stages/stage-03-agent/README.md) — Triage agent (LangGraph or Strands) with human approval for state changes
- [ ] [stage-04-model-layer](capstone/stages/stage-04-model-layer/README.md) — Bedrock Converse with tool use, Guardrails for PII, cost tracking per request
- [ ] [stage-05-platform-integrations](capstone/stages/stage-05-platform-integrations/README.md) — AgentCore Runtime hosting; Gateway/MCP tools for ticketing, alarms and CMDB; OAuth to ticketing API
- [ ] [stage-06-secure-deploy](capstone/stages/stage-06-secure-deploy/README.md) — Least-privilege roles, VPC endpoints, Terraform, CI/CD with rollback
- [ ] [stage-07-operate-evaluate](capstone/stages/stage-07-operate-evaluate/README.md) — OpenTelemetry traces, dashboard + alarms, eval suite in CI, prompt-injection tests, audit log
- [ ] [stage-08-customer-pack](capstone/stages/stage-08-customer-pack/README.md) — ServiceNow integration, architecture diagram, integration spec, demo video, runbook, lessons learned

## Weekly log
| Week | Hours | Done | Blockers | Next |
|---|---|---|---|---|
| 1 | | | | |
