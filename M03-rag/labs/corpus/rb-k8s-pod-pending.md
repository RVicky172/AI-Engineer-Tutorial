---
title: Pods stuck in Pending
type: runbook
service: kubernetes
updated: 2026-08-09
allowed_groups: [it-ops]
---
# Pods stuck in Pending

A `Pending` pod has not been scheduled onto any node. Unlike CrashLoopBackOff, the container never started.

1. `kubectl describe pod <pod> -n <ns>` and read the events at the bottom.
2. `Insufficient cpu` or `Insufficient memory`: the cluster autoscaler should add a node within 5 minutes. If it doesn't, check the node group's maximum size.
3. `node(s) had untolerated taint`: the pod lacks a toleration for the `memory` node group.
4. `pod has unbound immediate PersistentVolumeClaims`: the EBS volume is in another availability zone than any free node.
5. Requests that are far too large (for example 64 GB memory) can never be scheduled; fix the deployment.
