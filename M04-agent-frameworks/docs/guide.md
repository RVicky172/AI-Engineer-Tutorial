# M04 · Agent Frameworks and Multi-Agent Systems — Study Guide

> **Priority:** Must have · **Week:** 3 · **Study time:** ~3 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
The role names **LangGraph, LangChain and Strands Agents**. You should be able to build in at least two, explain the trade-offs to a customer, and — just as important — know when *not* to use an agent at all.

## Learning objectives
- Explain the agent loop and how to bound it.
- Build agents in LangGraph (explicit graph) and Strands (model-driven loop).
- Add human-in-the-loop approval with persistence.
- Design multi-agent systems and choose between patterns.
- Argue workflow vs. agent with concrete criteria.

---

## 1. The agent loop
```
while not done and steps < MAX_STEPS and time < BUDGET:
    response = model(system_prompt, history, tools)
    if response wants tools:
        results = run_tools(response.tool_calls)     # guarded, validated, approved
        history += [response, results]
    else:
        done = True
```
- **Reactive (ReAct)**: decide the next step each turn. Flexible, less predictable.
- **Plan-and-execute**: make a plan, then execute steps (re-plan on failure). More predictable, better for long tasks.
- **Stopping conditions**: final answer, max steps, max tokens/cost, wall-clock timeout, repeated identical tool call, human stop.

## 2. Workflow vs. agent
| Use a **deterministic workflow** when… | Use an **agent** when… |
|---|---|
| steps are known and stable | the path depends on what you discover |
| compliance needs exact, auditable steps | inputs are open-ended natural language |
| latency/cost must be predictable | a few extra calls are acceptable |
| errors must never be improvised around | you can bound actions with tools + approval |

Common middle ground: a **workflow with LLM steps** (classify → route → fixed path) or an agent *inside* one step of a workflow (Step Functions + agent).

## 3. LangGraph
A **state machine** for LLM apps: you define a typed state, nodes (functions that update state) and edges (including conditional routing).

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    messages: Annotated[list, add_messages]
    category: str | None

def classify(state: State): ...
def act(state: State):
    decision = interrupt({"action": "restart_service", "service": "payments-api"})
    if not decision["approved"]:
        return {"messages": [("ai", "Restart rejected; escalating instead.")]}
    ...

g = StateGraph(State)
g.add_node("classify", classify)
g.add_node("act", act)
g.add_edge(START, "classify")
g.add_conditional_edges("classify", lambda s: "act" if s["category"] == "outage" else END)
graph = g.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "inc-42"}}
graph.invoke({"messages": [("user", "payments down")]}, cfg)        # pauses at interrupt
graph.invoke(Command(resume={"approved": True}), cfg)              # resumes
```
Strengths: explicit control flow, **checkpointing/persistence**, human-in-the-loop interrupts, time-travel debugging, good for complex, auditable flows. Cost: more code and concepts. A prebuilt ReAct agent (`create_react_agent`) exists for simple cases.

## 4. LangChain
A library of components: chat model wrappers (e.g. `langchain-aws` `ChatBedrockConverse`), tools, retrievers, output parsers, runnables (LCEL). **Use** the model wrappers, tool abstractions and retrievers/integrations that save you time. **Skip** deep abstraction chains when a direct SDK call is clearer — fewer layers = easier debugging.

## 5. Strands Agents (AWS open-source SDK)
A **model-driven** loop: you give the model a prompt and tools; the SDK runs the loop. Very little code; Bedrock is the default provider; native MCP support; multi-agent primitives.

```python
from strands import Agent, tool

@tool
def get_ticket(number: str) -> dict:
    """Fetch an incident by number (format INC0012345)."""
    return tickets[number]

agent = Agent(system_prompt="You are an IT triage assistant.", tools=[get_ticket])
result = agent("What's the status of INC0000042?")
```
Strengths: fastest path from idea to working agent, first-class on AWS (deploys cleanly to AgentCore), MCP tools out of the box. Trade-off: less explicit control flow than a graph — you rely more on the model and on prompt/tool design; use hooks, limits and multi-agent patterns for structure.

## 6. Multi-agent patterns
| Pattern | How | Use when |
|---|---|---|
| **Supervisor / worker** | one agent delegates to specialists and merges results | distinct skills/permissions per worker |
| **Router** | a classifier picks one specialist | clear categories, low latency |
| **Agents-as-tools** | sub-agents exposed as tools to an orchestrator | simple composition (Strands supports this directly) |
| **Swarm / handoff** | agents pass control to each other | collaborative open-ended tasks (harder to bound) |
| **Graph / workflow of agents** | deterministic edges between agents | predictable pipelines |

**Memory:** shared memory = easy context sharing but leakage and confusion; isolated memory = clean boundaries but you must pass context explicitly. Isolating permissions per agent (knowledge agent read-only, actions agent write + approval) is a strong security pattern.

**Multi-agent costs more** (tokens, latency, failure points). Start single-agent; split only when tools/permissions/prompts get too large or conflicting.

## 7. Agent Skills
Packaging reusable instructions + scripts/tools as a folder an agent loads **on demand** (only a short description sits in context until needed). Keeps the base prompt small and capabilities modular. Know the concept and how it reduces context bloat versus stuffing every instruction into the system prompt.

## 8. Framework trade-offs (customer conversation)
- **Lock-in:** keep tools as plain Python functions / MCP servers so they move between frameworks.
- **Debuggability:** explicit graphs + traces (LangGraph, OTel in Strands) beat opaque chains.
- **Determinism:** graphs give fixed paths; model-driven loops need evals and guards.
- **Ops fit:** what the customer's team can maintain matters more than benchmark elegance.

---

## Self-check (try first, then open)
<details><summary>When is a deterministic workflow better than an autonomous agent?</summary>

When the steps are known, regulated or must be auditable; when latency and cost must be predictable; when errors are expensive and you don't want the model improvising; when the input is structured (an event, a form). Use LLM calls inside fixed steps (classification, extraction, summarisation) and reserve autonomy for genuinely open-ended investigation, bounded by tools and approval.
</details>

<details><summary>How do you stop an agent from looping on a failing tool?</summary>

Max-steps and time/cost budgets; detect repeated identical calls (same tool + args) and break; make tool errors actionable and distinguish retryable vs. permanent errors; cap retries per tool inside the tool layer (not via the model); circuit breaker on the dependency; instruct the model to escalate or explain after N failures; alert on high steps-per-task in observability.
</details>

## Resources
- LangGraph docs: concepts (state, persistence, human-in-the-loop, interrupts), how-to guides
- Strands Agents docs + GitHub samples (tools, MCP, multi-agent: agents-as-tools, swarm, graph)
- Anthropic engineering blog: "Building effective agents" (workflows vs. agents)
- LangChain docs: `langchain-aws` integration

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-triage-agent-two-frameworks/README.md)
