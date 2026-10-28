---
title: Pods in CrashLoopBackOff
type: runbook
service: kubernetes
updated: 2026-08-09
allowed_groups: [it-ops]
---
# Pods in CrashLoopBackOff

`CrashLoopBackOff` means the container starts, exits, and Kubernetes waits longer and longer (up to 5 minutes) before each restart. The pod is not the problem; the process inside it is.

## Diagnose in this order
1. Logs of the **previous** container, which crashed: `kubectl logs <pod> -n <ns> --previous`. Without `--previous` you see the new container, which may not have logged anything yet.
2. Exit code: `kubectl get pod <pod> -n <ns> -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'`.

| Exit code | Usual meaning | Where to look |
|---|---|---|
| 1 | application error at start-up | logs: missing config, bad secret, failed migration |
| 137 | killed: out of memory (OOMKilled) or failed liveness probe | memory limit, `kubectl describe pod` events |
| 139 | segmentation fault | native library or image architecture mismatch (arm64 vs amd64) |
| 143 | SIGTERM, graceful stop | usually a liveness probe killing a slow starter |

3. Events: `kubectl describe pod <pod> -n <ns>`, last 10 events.

## Common fixes
- A new secret or config map name in the deployment that does not exist yet: create it, or roll back.
- A liveness probe that runs before the app is ready: add a `startupProbe` instead of raising the liveness timeout.
- After a bad release: `kubectl rollout undo deploy/<name> -n <ns>`.
