# Interview Question Bank

Answer each in **two minutes**, out loud, using a real example from your work or your labs. Tick when you can answer it cleanly without notes. Likely interview style: scenario-based ("an agent fails in production, walk me through it"), small integration designs, IAM/networking trade-offs, and an end-to-end project you delivered.

Tip: structure answers as **Situation → approach → trade-off → result/metric**.

## Agents and LLMs
- [ ] Walk me through how you would design an agent that triages incidents and proposes fixes. *(M04, capstone)*
- [ ] How do you decide between a single agent, a workflow, and a multi-agent design? *(M04)*
- [ ] How do you prevent an agent from looping or running up cost? *(M04, M10)*
- [ ] How do you get reliable structured output from a model? *(M02)*
- [ ] How do you evaluate an agent before and after go-live? *(M11)*

## AWS and security
- [ ] Explain how an agent running in AgentCore (or ECS) gets permission to call Bedrock and read a secret. *(M06, M08)*
- [ ] A customer requires that no traffic leaves their VPC. What changes? *(M05, M08)*
- [ ] How would you let an agent call a customer's OAuth-protected API on behalf of different users? *(M06, M07)*
- [ ] You get AccessDenied on a cross-account call. How do you debug it? *(M08)*

## Production and operations
- [ ] The agent worked in the pilot but fails randomly in production. What is your investigation plan? *(M10)*
- [ ] How do you roll back a bad prompt or tool change? *(M09)*
- [ ] Which metrics and alarms would you set up for an agent service? *(M10)*
- [ ] How do you reduce latency and cost without hurting quality? *(M02, M05, M11)*

## Integration and RAG
- [ ] Retrieval returns irrelevant chunks for a customer's documents. What do you try? *(M03)*
- [ ] How do you enforce document-level access control in RAG? *(M03)*
- [ ] Describe a time you integrated with a poorly documented enterprise API. *(M07)*

## Customer-facing
- [ ] What are the first ten questions you ask in a technical discovery call? *(M15)*
- [ ] The customer wants a feature that the platform does not support. What do you do? *(M15)*
- [ ] Describe a deployment that went wrong and what you changed afterwards. *(M10, M15)*

## Module self-check questions
Each module README has two more self-check questions; collect your best answers here.

## Mock interview log
| Date | Interviewer | Questions | What went well | What to improve |
|---|---|---|---|---|
| | | | | |
