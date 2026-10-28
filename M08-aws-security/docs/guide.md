# M08 · AWS Security: IAM, OAuth, Secrets and Network — Study Guide

> **Priority:** Must have · **Week:** 6 · **Study time:** ~3-4 h · **Labs:** [../labs](../labs/SETUP.md)

## Why it matters
Customer security reviews decide whether you go live. Most integration delays come from **IAM, secrets or private connectivity** — and the engineer who can debug an AccessDenied or a VPC timeout in minutes is the one customers trust.

## Learning objectives
- Write least-privilege IAM for an agent and explain how policies are evaluated.
- Manage secrets correctly at runtime.
- Secure API entry points with the right authorizer.
- Design private networking with VPC endpoints and diagnose connectivity failures.
- Debug AccessDenied systematically with CloudTrail and the policy simulator.

---

## 1. IAM fundamentals
| Concept | Meaning |
|---|---|
| **User** | long-term identity (avoid for workloads) |
| **Role** | identity assumed temporarily; workloads (Lambda, ECS task, AgentCore runtime) use roles |
| **Trust policy** | *who may assume* the role (principal: service, account, federated IdP) |
| **Permissions policy** | *what* the role may do once assumed |
| **Identity-based policy** | attached to user/role |
| **Resource-based policy** | attached to resource (S3 bucket, KMS key, secret, Lambda, VPC endpoint) |
| **Permission boundary** | cap on max permissions of a role |
| **SCP / RCP** | organisation-level guardrails |
| **Condition keys** | `aws:SourceVpce`, `aws:PrincipalTag`, `aws:SourceAccount`, `kms:ViaService` ... |
| **STS AssumeRole** | get temporary credentials; basis of cross-account access |

**Evaluation logic (simplified):** explicit **Deny** anywhere wins → otherwise need an **Allow** from identity *or* resource policy (same account) → and nothing (SCP, boundary, session policy) may leave it out. Cross-account: need Allow on **both** sides (identity policy in caller account + resource/trust policy in target).

Least-privilege agent role example:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
     "Resource": ["arn:aws:bedrock:*::foundation-model/<model-id>",
                  "arn:aws:bedrock:<region>:<acct>:inference-profile/<profile-id>"]},
    {"Effect": "Allow", "Action": "s3:GetObject",
     "Resource": "arn:aws:s3:::acme-agent-data/runbooks/*"},
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": "arn:aws:secretsmanager:<region>:<acct>:secret:agent/servicenow-*"}
  ]
}
```

## 2. Secrets Manager and Parameter Store
- **Secrets Manager:** secrets with **rotation** (Lambda-based), resource policies, KMS encryption, cross-account sharing. Use for credentials, API keys, OAuth client secrets.
- **Parameter Store:** config + `SecureString` (KMS), cheaper, no built-in rotation. Use for non-secret config and simple secrets.
- **Runtime retrieval:** fetch at startup/first use, cache with TTL (AWS provides caching clients/Lambda extension), refresh on auth failure after rotation.
- If the secret uses a **customer-managed KMS key**, the role also needs `kms:Decrypt` *and* the key policy must allow it.

## 3. API Gateway authorizers
| Authorizer | Use |
|---|---|
| **IAM (SigV4)** | AWS-internal callers with roles |
| **Cognito / JWT** | users or apps with tokens from an OIDC IdP (HTTP API JWT authorizer works with Okta/Entra too) |
| **Lambda authorizer** | custom logic: API keys from a DB, custom headers, complex claims |
Plus **usage plans + API keys** for throttling/quotas per client (not for authentication alone), WAF for edge protection.

## 4. Networking
```
VPC
├── public subnet  (ALB, NAT gateway)       → internet gateway
└── private subnet (Lambda/ECS/agent)
       ├── interface endpoints (ENIs): bedrock-runtime, secretsmanager, logs, ecr.api, ecr.dkr, sts ...
       └── gateway endpoints (route table): S3, DynamoDB
```
- **Security groups:** stateful; the endpoint SG must allow **443 inbound from the workload SG**.
- **Interface endpoints (PrivateLink):** private IPs in your subnets; with **private DNS** on, the normal service hostname resolves to them — no code change.
- **Gateway endpoints:** free, S3 and DynamoDB only, added to route tables.
- **Endpoint policies:** restrict which principals/resources can be used through the endpoint.
- **Private connectivity to customer data centres:** Site-to-Site VPN or Direct Connect (+ Transit Gateway); DNS via Route 53 Resolver endpoints.

**Key debugging insight:** missing route/endpoint/SG usually shows up as a **timeout**, not AccessDenied. AccessDenied means you *reached* the service.

## 5. Data protection
- Encryption at rest (KMS) and in transit (TLS 1.2+); enforce with bucket policies (`aws:SecureTransport`).
- PII: minimise, mask (Guardrails, Comprehend), set retention.
- **Logging hygiene:** never log secrets, tokens or raw sensitive data; log IDs and hashes.

## 6. Debugging AccessDenied
1. Read the full error: action, resource ARN, principal, and (often) **which policy type** denied ("explicit deny in a resource-based policy", "no identity-based policy allows").
2. Confirm the **principal**: `aws sts get-caller-identity` from inside the workload (wrong role is common).
3. Find the event in **CloudTrail** (`errorCode: AccessDenied`), check `userIdentity`, `requestParameters`.
4. Use **IAM policy simulator** / `simulate-principal-policy` and Access Analyzer.
5. Check, in order: identity policy → resource policy (bucket, key, secret, endpoint) → KMS key policy → permission boundary → SCP → session policy.

---

## Self-check (try first, then open)
<details><summary>A Lambda times out calling Secrets Manager from a private subnet. List your checks in order.</summary>

1) Timeout = network, not IAM. Is the Lambda in the VPC subnets you think? 2) Is there a route to Secrets Manager: interface endpoint `secretsmanager` in those subnets/AZs, or a NAT gateway? 3) Private DNS enabled on the endpoint (and VPC DNS hostnames/resolution on)? 4) Endpoint security group allows 443 from the Lambda SG; Lambda SG allows outbound 443. 5) NACLs. 6) Endpoint policy allows the call. 7) Lambda timeout and SDK timeouts sensible. 8) Then IAM/KMS once it stops timing out.
</details>

<details><summary>Explain the difference between a trust policy and a permissions policy.</summary>

A trust policy is a resource policy on the role that says **who may assume it** (e.g. `lambda.amazonaws.com`, another account, a federated IdP, with conditions). A permissions policy says **what actions on which resources** the role can perform after it's assumed. You need both: trust to get credentials, permissions to use them.
</details>

## Resources
- IAM User Guide: Policy evaluation logic, Troubleshooting access denied, Policy simulator, Access Analyzer
- AWS PrivateLink and VPC endpoints docs; Secrets Manager best practices
- AWS Well-Architected Framework: Security pillar

**Next:** [Lab environment setup](../labs/SETUP.md) → [Lab 01](../labs/lab-01-least-privilege-agent-role/README.md)
