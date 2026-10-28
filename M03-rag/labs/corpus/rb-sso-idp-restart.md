---
title: Restart the SSO identity provider
type: runbook
service: sso
updated: 2026-06-11
allowed_groups: [it-ops]
---
# Restart the SSO identity provider

The SSO identity provider (`sso-idp`) runs as three pods in the `identity` namespace of the `prod-eks-1` cluster, behind `id.acme.example`.

## Symptoms that justify a restart
- The login page returns HTTP 503 for all users.
- `idp_token_issue_latency_p95` is above 5 seconds for 10 minutes.
- Pods are stuck in `Ready=false` after a node failure.

## Steps
1. Link the incident. Restarting the IdP logs nobody out, but new logins fail for about 60 seconds.
2. Check whether the database is the real problem first: `kubectl -n identity logs deploy/sso-idp | grep -i "connection refused"`. If the IdP cannot reach its database, a restart will not help; fail over the identity database instead.
3. Rolling restart: `kubectl -n identity rollout restart deploy/sso-idp`.
4. Watch it: `kubectl -n identity rollout status deploy/sso-idp --timeout=5m`.
5. Test a login with the synthetic account `svc-sso-probe`.

## Do not
- Do not scale to zero. Sessions live in Redis, but the signing keys load at start-up; with zero pods nobody can log in for several minutes.
