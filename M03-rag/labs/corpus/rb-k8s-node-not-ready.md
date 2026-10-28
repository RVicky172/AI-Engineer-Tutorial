---
title: Kubernetes node NotReady
type: runbook
service: kubernetes
updated: 2026-08-22
allowed_groups: [it-ops]
---
# Kubernetes node NotReady

Production workloads run on EKS cluster `prod-eks-1` (managed node groups `general` and `memory`).

## Symptoms
- Alert `KubeNodeNotReady` for more than 5 minutes.
- Pods on the node stuck in `Terminating` or `Unknown`.

## Diagnose
1. `kubectl describe node <node>` and read the Conditions. `MemoryPressure=True` or `DiskPressure=True` tells you why the kubelet stopped reporting.
2. `DiskPressure`: usually container images and logs filling the root volume. The `general` group uses 50 GB volumes, which was too small during the August 2026 incident.
3. `MemoryPressure`: look for a pod without memory limits: `kubectl top pods -A --sort-by=memory | head`.
4. If the node does not respond at all, check the EC2 instance status checks in the console.

## Fix
1. Cordon the node: `kubectl cordon <node>`.
2. Drain it: `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --timeout=10m`. PodDisruptionBudgets may slow this down; do not force-delete pods of stateful sets.
3. Terminate the instance from the node group. The autoscaling group replaces it within about 4 minutes.
4. Fix the cause (memory limits, larger volume) with a change request so it does not repeat.
