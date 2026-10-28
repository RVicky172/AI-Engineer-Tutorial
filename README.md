# AI Engineer Tutorial — Forward Deployment Engineer (AWS Agentic AI)

A hands-on study repo built from [AI_Engineer_Learning_Guide.docx](AI_Engineer_Learning_Guide.docx). Every skill in the skill map has its own folder with a **study guide** (`docs/`) and **practice labs** (`labs/`).

## How to use this repo
1. Rate yourself on every skill in [PROGRESS.md](PROGRESS.md) (1 = never used, 5 = could teach it).
2. Follow the 8-week roadmap below. For each module:
   - **Study:** read `docs/guide.md`, write your own explanation in `docs/notes.md`.
   - **Set up:** follow `labs/SETUP.md` (prerequisites, Python env, local services).
   - **Practise:** complete the labs in order. Finish at least the first two before moving on.
   - **Check:** answer the self-check questions out loud, without notes.
3. Build the [capstone](capstone/README.md) one stage per week. It ties every module together.
4. Practise the [interview question bank](interview-prep/question-bank.md) and the [troubleshooting cheat sheet](interview-prep/troubleshooting-cheatsheet.md) in week 8.

> AWS services (especially Bedrock AgentCore) change quickly. Treat the official AWS documentation as the source of truth and check every command before you rely on it.

## Skill map
| # | Skill | Priority | Week |
|---|---|---|---|
| [M01](M01-python-engineering/README.md) | Python and Software Engineering Fundamentals | Must have | 1 |
| [M02](M02-llm-fundamentals/README.md) | LLM Fundamentals, Prompting, Tool Calling and Structured Outputs | Must have | 1 |
| [M03](M03-rag/README.md) | RAG: Retrieval-Augmented Generation | Must have | 2 |
| [M13](M13-databases-sql/README.md) | Databases, SQL and Enterprise Data Sources | Must have | 2 |
| [M04](M04-agent-frameworks/README.md) | Agent Frameworks and Multi-Agent Systems | Must have | 3 |
| [M05](M05-amazon-bedrock/README.md) | Amazon Bedrock | Must have | 4 |
| [M06](M06-bedrock-agentcore/README.md) | Amazon Bedrock AgentCore | **Differentiator** | 5 |
| [M07](M07-mcp-a2a-integrations/README.md) | MCP, A2A and Enterprise Integrations | Must have | 5 |
| [M08](M08-aws-security/README.md) | AWS Security: IAM, OAuth, Secrets and Network | Must have | 6 |
| [M09](M09-deployment-cicd-iac/README.md) | Deployment: Docker, ECS/EKS/Lambda, CI/CD and IaC | Must have | 6 |
| [M10](M10-observability/README.md) | Observability and Production Troubleshooting | Must have | 7 |
| [M11](M11-testing-evaluation/README.md) | Testing and Evaluation of Agentic Systems | Must have | 7 |
| [M12](M12-responsible-ai-security/README.md) | Responsible AI, Security and Data Protection | Must have | 7 |
| [M14](M14-itsm-aiops/README.md) | ITSM, CloudOps, SRE and AIOps Use Cases | Preferred | 8 |
| [M15](M15-customer-facing-skills/README.md) | Customer-Facing Engineering Skills | Must have | 8 |

Biggest gaps for most candidates: **M06, M07, M11, M12**. Give these extra days.

## Eight-week roadmap (~10-12 h/week)
| Week | Focus | Deliverable | Modules |
|---|---|---|---|
| 1 | Foundations | FastAPI chat service with tests; prompt regression suite | M01, M02 |
| 2 | RAG and databases | pgvector RAG with golden set and access control; safe text-to-SQL | M03, M13 |
| 3 | Agent frameworks | Triage agent in LangGraph and Strands; human approval step | M04 |
| 4 | Bedrock deep dive | Converse client with tool use, Guardrails, VPC endpoint test | M05 |
| 5 | AgentCore and integrations | Agent on AgentCore Runtime; Gateway tool; MCP server; OAuth tool | M06, M07 |
| 6 | Security and deployment | Least-privilege IAM; Terraform + ECS/Lambda; CI/CD pipeline | M08, M09 |
| 7 | Observability, testing, responsible AI | Traces + dashboard; 40-case eval in CI; prompt-injection report | M10, M11, M12 |
| 8 | Domain, customer skills, mock interviews | ITSM integration; demo video; runbook; 3 mock interviews | M14, M15 |

**Weekly routine:** 2 study sessions (~3 h, end with notes) · 2 build sessions (~6 h, commit labs with a short NOTES.md) · 1 review session (~1 h, self-check aloud + update PROGRESS.md).

## Repo layout
```
AI Engineer Tutorial/
├── README.md                  ← this file
├── PROGRESS.md                ← skill ratings, lab checklist, weekly log
├── M01-python-engineering/
│   ├── README.md              ← module overview, lab list, self-check
│   ├── docs/
│   │   ├── guide.md           ← study guide (concepts, code, pitfalls, resources)
│   │   └── notes.md           ← your own notes
│   └── labs/
│       ├── SETUP.md           ← environment setup
│       ├── requirements.txt
│       └── lab-01-.../README.md   ← goal, steps, done-when, stretch
├── M02-... → M15-...          ← same structure
├── capstone/                  ← IT Incident Triage Agent on AWS, built in 8 stages
└── interview-prep/            ← question bank + troubleshooting cheat sheet
```

## Cost safety
- Use a **sandbox AWS account** and set an **AWS Budget alarm** before week 1.
- Interface VPC endpoints, NAT gateways, load balancers, OpenSearch Serverless and similar resources bill **per hour**. Destroy them at the end of each session.
- Never commit `.env`, keys or Terraform state (see [.gitignore](.gitignore)).
