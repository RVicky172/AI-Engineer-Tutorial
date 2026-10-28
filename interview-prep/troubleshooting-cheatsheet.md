# Production Troubleshooting Cheat Sheet

**Isolate the layer first. Work from the outside in and change one thing at a time.**

| Layer | Typical symptoms | First checks |
|---|---|---|
| Client / API entry | 4xx/5xx errors, timeouts, auth failures | API Gateway or ALB logs, authorizer config, request IDs, payload size |
| Identity and IAM | AccessDenied, 401/403 from tools | Role trust and permission policies, CloudTrail, token expiry, OAuth scopes |
| Network | Timeouts only inside the VPC, DNS errors | Security groups, route tables, VPC endpoints and their policies, private DNS |
| Model | Throttling, slow responses, refusals, truncation | Quotas, region/inference profile, max tokens, guardrail interventions |
| Prompt / context | Wrong tone, ignored rules, regressions after release | Prompt version diff, context length, tool descriptions, eval results |
| Tools / integrations | Wrong tool, bad arguments, upstream errors | Tool schemas, traces of tool spans, upstream status and rate limits, error mapping |
| RAG | Missing or outdated answers, irrelevant citations | Index freshness, chunking, filters, retrieval scores, golden set |
| Infrastructure | Container restarts, cold starts, memory errors | Task/pod logs, memory and CPU, concurrency limits, deployment history |
| Cost | Unexpected spend | Tokens per request, retries, loop counts, model choice, caching |

## Incident method
1. **Reproduce** — get a request ID / session ID / trace ID for a failing case.
2. **Isolate the layer** — use the table above; read the trace top-down.
3. **Fix** — smallest change, one at a time.
4. **Verify** — re-run the failing case + the eval suite.
5. **Write it down** — post-incident note: symptom, detection, root cause, fix, prevention.

## Symptom → first guess
| Symptom | First guess |
|---|---|
| Timeout (not AccessDenied) from inside a VPC | Missing VPC endpoint / NAT, security group, or private DNS |
| AccessDenied with an explicit deny | SCP, permission boundary, resource or endpoint policy |
| Works locally, fails deployed | Different role, region, model access, env var or secret |
| Quality dropped after release, no errors | Prompt/tool description/model ID change; compare eval runs |
| Answer cites wrong/old docs | Index not refreshed, metadata filter, chunk boundaries |
| Cost spike | Agent loop, retry storm, larger context, model change |
| Slow only at peak times | Throttling/quotas, connection pool, downstream rate limits |
